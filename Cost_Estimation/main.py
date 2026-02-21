"""
Healthcare Cost & Treatment Rating API
Main FastAPI application — conversational /chat endpoint.
"""
import json
import os
from fastapi import FastAPI, Depends, HTTPException
from supabase import Client
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from database import get_db
from models import Hospital, Procedure
from schemas import (
    ChatMessage,
    QuestionResponse,
    ChatResponse,
    HospitalResult,
    PersonalizedSummary,
)
from services.risk_engine import calculate_total_risk
from services.cost_engine import calculate_personalized_cost, calculate_adjusted_complication
from services.ranking_engine import compute_value_score, rank_hospitals, generate_ai_explanation
from services.patient_service import fetch_patient_context, prefill_from_patient, generate_opening_summary
from services.questionnaire import (
    create_session,
    get_next_question,
    process_answer,
    build_chat_request,
    build_known_summary,
)
from seed import seed

app = FastAPI(
    title="Healthcare Cost & Treatment Rating API",
    description="Patient-centric conversational cost estimation with Groq AI. Supports any treatment.",
    version="3.0.0",
)


@app.on_event("startup")
def startup_event():
    client = get_db()
    seed(client)


# ── Helper: fetch dynamic options from DB ─────────────────────────────────────

def _get_procedure_options(client: Client) -> list[str]:
    """Fetch all procedure names from DB — no hardcoding."""
    result = client.table("procedures").select("name").order("name").execute()
    return [row["name"] for row in result.data] if result.data else []


def _get_city_options(client: Client) -> list[str]:
    """Fetch unique cities from hospitals table — no hardcoding."""
    result = client.table("hospitals").select("city").execute()
    seen = set()
    cities = []
    for row in result.data or []:
        c = row["city"].strip().title()
        if c not in seen:
            seen.add(c)
            cities.append(c)
    return sorted(cities)


# ── Single endpoint ──────────────────────────────────────────────────────────

@app.post("/chat", response_model=QuestionResponse)
def chat(message: ChatMessage, client: Client = Depends(get_db)):
    """
    Conversational healthcare cost estimation.

    Flow:
      1. No session_id → start new session (with optional patient_id)
      2. Has session_id + answer → answer question, return next
      3. All answered → run cost engine → return comparison
    """

    # ── START NEW SESSION ─────────────────────────────────────────────────
    if not message.session_id:
        prefilled_answers = {}
        prefilled_fields = []
        opening_summary = None

        # Load patient data if patient_id provided
        if message.patient_id:
            patient_ctx = fetch_patient_context(client, message.patient_id)
            if not patient_ctx:
                raise HTTPException(
                    status_code=404,
                    detail=f"Patient with id {message.patient_id} not found.",
                )
            prefilled_answers, prefilled_fields = prefill_from_patient(patient_ctx)
            opening_summary = generate_opening_summary(patient_ctx, prefilled_fields)

        # Default greeting for anonymous sessions
        if not opening_summary:
            opening_summary = (
                "👋 Hi! I'm your healthcare cost assistant. "
                "I'll ask a few quick questions to estimate treatment costs "
                "and find the best hospital for you."
            )

        # Fetch dynamic options from DB (no hardcoding!)
        procedure_options = _get_procedure_options(client)
        city_options = _get_city_options(client)

        session_id = create_session(
            prefilled_answers=prefilled_answers,
            procedure_options=procedure_options,
            city_options=city_options,
        )
        first_q = get_next_question(session_id)

        if first_q is None:
            # All fields pre-filled — run engine immediately
            return _run_cost_engine(session_id, prefilled_answers, client,
                                    opening_summary, prefilled_fields)

        return QuestionResponse(
            session_id=session_id,
            summary=opening_summary,
            known_summary=build_known_summary(session_id),
            question=first_q["question"],
            question_key=first_q["question_key"],
            options=first_q["options"],
            allow_other=first_q["allow_other"],
            awaiting_free_text=first_q["awaiting_free_text"],
            prefilled_fields=prefilled_fields,
            is_complete=False,
        )

    # ── CONTINUE EXISTING SESSION ─────────────────────────────────────────
    if not message.answer:
        raise HTTPException(
            status_code=422,
            detail="Provide 'answer' when continuing an existing session.",
        )

    result = process_answer(message.session_id, message.answer)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    if result["type"] == "final":
        return _run_cost_engine(
            session_id=message.session_id,
            answers=result["collected_answers"],
            client=client,
        )

    return QuestionResponse(
        session_id=message.session_id,
        known_summary=build_known_summary(message.session_id),
        question=result["question"],
        question_key=result["question_key"],
        options=result["options"],
        allow_other=result["allow_other"],
        awaiting_free_text=result["awaiting_free_text"],
        is_complete=False,
    )


# ── Cost engine runner ────────────────────────────────────────────────────────

def _run_cost_engine(
    session_id: str,
    answers: dict,
    client: Client,
    summary: str = None,
    prefilled_fields: list = None,
) -> QuestionResponse:
    """
    Converts collected session answers into a full hospital comparison result.
    If the requested procedure is NOT in the DB, Groq estimates its cost dynamically.
    """
    chat_data = build_chat_request(answers)

    # ── Fetch procedure (or estimate via Groq if unknown) ─────────────────
    proc_result = (
        client.table("procedures")
        .select("*")
        .ilike("name", chat_data["selected_procedure"])
        .execute()
    )

    if proc_result.data:
        procedure = Procedure.from_dict(proc_result.data[0])
    else:
        # Procedure not in DB — use Groq to estimate cost and LOS
        procedure = _estimate_procedure_with_groq(
            procedure_name=chat_data["selected_procedure"],
            client=client,
        )

    # ── Fetch hospitals by city ───────────────────────────────────────────
    hosp_result = (
        client.table("hospitals")
        .select("*")
        .ilike("city", chat_data["city"])
        .execute()
    )
    if not hosp_result.data:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No hospitals found in '{chat_data['city'].title()}'. "
                f"We currently cover: {', '.join(_get_city_options(client))}."
            ),
        )
    hospitals = [Hospital.from_dict(h) for h in hosp_result.data]

    # ── Fetch risk conditions ─────────────────────────────────────────────
    risk_result = client.table("risk_conditions").select("*").execute()
    risk_map = {rc["name"]: float(rc["cost_multiplier"]) for rc in risk_result.data}

    # ── Risk → Cost → Ranking ─────────────────────────────────────────────
    total_risk = calculate_total_risk(
        age=chat_data["age"],
        comorbidities=chat_data["comorbidities"],
        smoking=chat_data["smoking"],
        all_risk_conditions=risk_map,
    )

    hospital_results: list[HospitalResult] = []
    for hospital in hospitals:
        p_cost = calculate_personalized_cost(hospital, procedure, total_risk)
        adj_comp = calculate_adjusted_complication(hospital, total_risk)
        v_score = compute_value_score(hospital.success_rate, p_cost, adj_comp)
        hospital_results.append(HospitalResult(
            hospital_name=hospital.name,
            personalized_cost=p_cost,
            success_rate=hospital.success_rate,
            adjusted_complication=adj_comp,
            recovery_days=hospital.average_recovery_days,
            value_score=v_score,
        ))

    ranked = rank_hospitals(hospital_results)
    all_costs = [h.personalized_cost for h in ranked]
    cost_min, cost_max = round(min(all_costs), 2), round(max(all_costs), 2)
    budget_fit = cost_min <= chat_data["budget_limit"]

    ins = chat_data["insurance_status"].lower()
    if ins == "private":
        insurance_note = "Your private insurance may cover 60–80% of the cost. Confirm limits with your insurer."
    elif ins == "government":
        insurance_note = "Government schemes like Ayushman Bharat may apply. Verify eligibility at the hospital."
    else:
        insurance_note = "No insurance detected. Ask the hospital about EMI or financing options."

    chat_response = ChatResponse(
        personalized_summary=PersonalizedSummary(
            estimated_cost_range=[cost_min, cost_max],
            budget_fit=budget_fit,
            insurance_note=insurance_note,
        ),
        hospital_comparison=ranked,
        ai_explanation=generate_ai_explanation(ranked[:2]),
    )

    return QuestionResponse(
        session_id=session_id,
        summary=summary,
        prefilled_fields=prefilled_fields or [],
        is_complete=True,
        result=chat_response,
    )


# ── Groq procedure cost estimator (unlimited treatment support) ───────────────

def _estimate_procedure_with_groq(procedure_name: str, client: Client) -> Procedure:
    """
    If a procedure is not in the DB, call Groq to estimate a realistic base cost
    and length of stay based on similar known procedures.
    Returns a synthetic Procedure object (not stored in DB).
    """
    # Get existing procedures as reference
    ref_result = client.table("procedures").select("name,base_cost,average_length_of_stay").execute()
    known = ref_result.data or []

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=groq_key,
                temperature=0.2,
            )
            system_msg = SystemMessage(content=(
                "You are a medical cost estimation expert in India (2024 rates, INR). "
                "Estimate realistic hospital procedure costs based on similar known procedures. "
                "Respond ONLY with valid JSON, no extra text."
            ))
            human_msg = HumanMessage(content=(
                f"Procedure requested: \"{procedure_name}\"\n\n"
                f"Known procedures for reference:\n"
                + "\n".join(
                    f"  - {p['name']}: ₹{p['base_cost']:,.0f}, {p['average_length_of_stay']} days stay"
                    for p in known
                )
                + f"\n\nEstimate base cost (in INR) and average hospital stay in days for \"{procedure_name}\".\n"
                f"Return: {{\"base_cost\": 95000, \"average_length_of_stay\": 4}}"
            ))
            response = llm.invoke([system_msg, human_msg])
            content = response.content.strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            return Procedure(
                id=0,
                name=procedure_name.title(),
                base_cost=float(data.get("base_cost", 80000)),
                average_length_of_stay=int(data.get("average_length_of_stay", 4)),
            )
        except Exception:
            pass

    # Hard fallback if Groq fails
    return Procedure(
        id=0,
        name=procedure_name.title(),
        base_cost=80000.0,
        average_length_of_stay=4,
    )
