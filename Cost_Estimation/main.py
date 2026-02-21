"""
Healthcare Cost & Treatment Rating API
Main FastAPI application — conversational /chat and /rag-chat endpoints.
"""
import json
import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
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
from services.cost_engine import calculate_personalized_cost, calculate_adjusted_complication, calculate_insurance_breakdown
from services.ranking_engine import compute_value_score, rank_hospitals, generate_ai_explanation
from services.patient_service import fetch_patient_context, prefill_from_patient, generate_opening_summary
from services.questionnaire import (
    create_session,
    get_next_question,
    process_answer,
    build_chat_request,
    build_known_summary,
)
from services.rag_service import (
    build_knowledge_context,
    build_patient_context,
    process_rag_turn,
    generate_rag_opening,
    generate_field_options,
    REQUIRED_FIELDS,
)
from services.memory_service import (
    init_history,
    append_message,
    save_answers,
    save_result,
    load_history,
    get_all_sessions,
)
from seed import seed


# ── RAG chat schemas ──────────────────────────────────────────────────────────

class RagChatMessage(BaseModel):
    """
    /rag-chat endpoint message.
    - Start: send {} or {patient_id: 1}
    - Continue: send {session_id: "...", message: "I need knee surgery in Pune"}
    """
    patient_id: Optional[int] = None
    session_id: Optional[str] = None
    message: Optional[str] = None


class RagChatResponse(BaseModel):
    session_id: str
    reply: str
    missing_fields: list = []
    collected: dict = {}
    is_complete: bool = False
    result: Optional[ChatResponse] = None
    next_field: Optional[str] = None         # which field to ask next
    suggested_options: list = []              # choices to show as buttons in UI

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
            patient_context=opening_summary if message.patient_id else "",  # give LLM context
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
    patient_id: int = None,
) -> QuestionResponse:
    """
    Converts collected session answers into a full hospital comparison result.
    If the requested procedure is NOT in the DB, Groq estimates its cost dynamically.
    """
    chat_data = build_chat_request(answers)

    # ── Fetch procedure (exact → fuzzy → Groq estimate) ─────────────────
    procedure_name = chat_data["selected_procedure"].strip()

    # 1. Exact case-insensitive match
    proc_result = (
        client.table("procedures")
        .select("*")
        .ilike("name", procedure_name)
        .execute()
    )

    # 2. Fuzzy wildcard match (handles partial names)
    if not proc_result.data:
        proc_result = (
            client.table("procedures")
            .select("*")
            .ilike("name", f"%{procedure_name}%")
            .execute()
        )

    if proc_result.data:
        procedure = Procedure.from_dict(proc_result.data[0])
    else:
        # 3. Procedure not in DB — use Groq to estimate cost and LOS
        procedure = _estimate_procedure_with_groq(
            procedure_name=procedure_name,
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
        ins_breakdown = calculate_insurance_breakdown(
            hospital=hospital,
            personalized_cost=p_cost,
            insurance_status=chat_data["insurance_status"],
        )
        hospital_results.append(HospitalResult(
            hospital_name=hospital.name,
            personalized_cost=p_cost,
            success_rate=hospital.success_rate,
            adjusted_complication=adj_comp,
            recovery_days=hospital.average_recovery_days,
            value_score=v_score,
            insurance_accepted=ins_breakdown["insurance_accepted"],
            amount_covered=ins_breakdown["amount_covered"],
            patient_out_of_pocket=ins_breakdown["patient_out_of_pocket"],
        ))

    ranked = rank_hospitals(hospital_results)
    all_costs = [h.personalized_cost for h in ranked]
    cost_min, cost_max = round(min(all_costs), 2), round(max(all_costs), 2)
    budget_fit = cost_min <= chat_data["budget_limit"]

    # ── Insurance summary ─────────────────────────────────────────────────
    ins = chat_data["insurance_status"].lower()
    insured_hospitals = [h for h in ranked if h.insurance_accepted]
    ins_count = len(insured_hospitals)
    total_hospitals = len(ranked)

    if ins == "none":
        insurance_note = (
            "No insurance detected. ₹{:,.0f}–₹{:,.0f} must be paid out-of-pocket. "
            "Ask the hospital about EMI or financing options."
        ).format(cost_min, cost_max)
    else:
        if insured_hospitals:
            covered_amounts = [h.amount_covered for h in insured_hospitals]
            oop_amounts = [h.patient_out_of_pocket for h in insured_hospitals]
            cov_min, cov_max = round(min(covered_amounts), 2), round(max(covered_amounts), 2)
            oop_min, oop_max = round(min(oop_amounts), 2), round(max(oop_amounts), 2)

            scheme = "Ayushman Bharat / PMJAY" if ins == "government" else "Private insurance"
            insurance_note = (
                "With {scheme}, insurance covers ₹{cov_min:,.0f}–₹{cov_max:,.0f} "
                "({count} of {total} hospitals accept your insurance). "
                "Your estimated out-of-pocket: ₹{oop_min:,.0f}–₹{oop_max:,.0f}."
            ).format(
                scheme=scheme,
                cov_min=cov_min, cov_max=cov_max,
                count=ins_count, total=total_hospitals,
                oop_min=oop_min, oop_max=oop_max,
            )
        else:
            scheme = "Government scheme" if ins == "government" else "Private insurance"
            insurance_note = (
                f"None of the listed hospitals currently accept your {scheme}. "
                f"Full amount ₹{cost_min:,.0f}–₹{cost_max:,.0f} payable out-of-pocket. "
                "Please call ahead to verify insurance tie-ups."
            )

    ai_explanation = generate_ai_explanation(ranked[:2])
    chat_response = ChatResponse(
        personalized_summary=PersonalizedSummary(
            estimated_cost_range=[cost_min, cost_max],
            budget_fit=budget_fit,
            insurance_note=insurance_note,
            insurance_accepted_count=ins_count,
        ),
        hospital_comparison=ranked,
        ai_explanation=ai_explanation,
    )

    # ── Save full result to Supabase chat_history ─────────────────────────
    try:
        result_payload = {
            "estimated_cost_range": [cost_min, cost_max],
            "budget_fit": budget_fit,
            "insurance_note": insurance_note,
            "top_hospital": ranked[0].hospital_name if ranked else None,
            "top_value_score": ranked[0].value_score if ranked else None,
            "ai_explanation": ai_explanation,
            "all_hospitals": [
                {
                    "name": h.hospital_name,
                    "cost": h.personalized_cost,
                    "success_rate": h.success_rate,
                    "value_score": h.value_score,
                }
                for h in ranked
            ],
        }
        save_answers(client, session_id, answers)
        save_result(client, session_id, result_payload)
    except Exception:
        pass  # history save errors must never crash the response

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


# ── RAG Chat endpoint ─────────────────────────────────────────────────────────

# In-memory store for RAG sessions: {session_id: {collected, messages, patient_id, knowledge_ctx, patient_ctx}}
_rag_sessions: dict = {}


@app.post("/rag-chat", response_model=RagChatResponse)
def rag_chat(message: RagChatMessage, client: Client = Depends(get_db)):
    """
    Fully conversational free-form RAG chatbot.
    User can type anything — the LLM extracts required fields from natural language,
    asks follow-up questions for missing info, and runs the cost engine when ready.
    All conversation turns + final result are saved as JSON to Supabase chat_history.
    """

    # ── START NEW RAG SESSION ─────────────────────────────────────────────
    if not message.session_id:
        import uuid
        session_id = str(uuid.uuid4())

        # Fetch Supabase knowledge context (hospitals + procedures + risk_conditions)
        knowledge_ctx = build_knowledge_context(client)

        # Fetch patient profile if patient_id provided
        patient_ctx_text = ""
        prefilled: dict = {}
        if message.patient_id:
            patient_ctx_text = build_patient_context(client, message.patient_id)
            # Also prefill via patient_service for structured fields
            from services.patient_service import fetch_patient_context as _fetch
            from services.patient_service import prefill_from_patient as _prefill
            raw_ctx = _fetch(client, message.patient_id)
            if raw_ctx:
                prefilled, _ = _prefill(raw_ctx)

        _rag_sessions[session_id] = {
            "collected": prefilled,
            "messages": [],
            "patient_id": message.patient_id,
            "knowledge_ctx": knowledge_ctx,
            "patient_ctx": patient_ctx_text,
        }

        # Init Supabase history row
        try:
            init_history(client, session_id, message.patient_id)
        except Exception:
            pass

        # Generate personalized opening
        opening = generate_rag_opening(knowledge_ctx, patient_ctx_text, prefilled)

        # Save opening message to history
        try:
            append_message(client, session_id, "assistant", opening)
        except Exception:
            pass

        missing = [f for f in REQUIRED_FIELDS if f not in prefilled]
        first_field = missing[0] if missing else None
        opts = generate_field_options(first_field, knowledge_ctx, prefilled) if first_field else []
        return RagChatResponse(
            session_id=session_id,
            reply=opening,
            missing_fields=missing,
            collected=prefilled,
            is_complete=False,
            next_field=first_field,
            suggested_options=opts,
        )

    # ── CONTINUE EXISTING RAG SESSION ─────────────────────────────────────
    session_id = message.session_id
    rag_state = _rag_sessions.get(session_id)
    if not rag_state:
        raise HTTPException(
            status_code=404,
            detail="RAG session not found. Please start a new session.",
        )

    if not message.message:
        raise HTTPException(
            status_code=422,
            detail="Provide 'message' when continuing an existing RAG session.",
        )

    user_msg = message.message

    # Save user message to history
    try:
        append_message(client, session_id, "user", user_msg)
    except Exception:
        pass

    # Process the turn via RAG service
    turn_result = process_rag_turn(
        user_message=user_msg,
        collected=rag_state["collected"],
        knowledge_context=rag_state["knowledge_ctx"],
        patient_context=rag_state["patient_ctx"],
        message_history=rag_state["messages"],
    )

    # Update session state
    rag_state["collected"] = turn_result["collected"]
    rag_state["messages"].append({"role": "user", "content": user_msg})
    rag_state["messages"].append({"role": "assistant", "content": turn_result["reply"]})

    # Save assistant reply + current answers snapshot to Supabase
    try:
        append_message(client, session_id, "assistant", turn_result["reply"])
        save_answers(client, session_id, rag_state["collected"])
    except Exception:
        pass

    # ── All fields collected — run cost engine ────────────────────────────
    if turn_result["is_complete"]:
        try:
            q_response = _run_cost_engine(
                session_id=session_id,
                answers=rag_state["collected"],
                client=client,
                patient_id=rag_state.get("patient_id"),
            )
            return RagChatResponse(
                session_id=session_id,
                reply=turn_result["reply"],
                missing_fields=[],
                collected=rag_state["collected"],
                is_complete=True,
                result=q_response.result,
                next_field=None,
                suggested_options=[],
            )
        except HTTPException as e:
            return RagChatResponse(
                session_id=session_id,
                reply=f"Sorry, I ran into an issue: {e.detail} Could you double-check your city or procedure?",
                missing_fields=[],
                collected=rag_state["collected"],
                is_complete=False,
                next_field=None,
                suggested_options=[],
            )

    next_f = turn_result.get("next_field")
    opts = generate_field_options(next_f, rag_state["knowledge_ctx"], rag_state["collected"]) if next_f else []
    return RagChatResponse(
        session_id=session_id,
        reply=turn_result["reply"],
        missing_fields=turn_result["missing"],
        collected=rag_state["collected"],
        is_complete=False,
        next_field=next_f,
        suggested_options=opts,
    )


# ── History endpoints ─────────────────────────────────────────────────────────
# IMPORTANT: /history/patient/{patient_id} MUST come before /history/{session_id}
# otherwise FastAPI matches "patient" as a session_id string.

@app.get("/history/patient/{patient_id}")
def get_patient_history(patient_id: int, client: Client = Depends(get_db)):
    """
    Retrieve all past sessions for a patient, newest first.
    Returns list of {session_id, answers, result, created_at}.
    """
    sessions_list = get_all_sessions(client, patient_id)
    if not sessions_list:
        raise HTTPException(
            status_code=404,
            detail=f"No session history found for patient {patient_id}.",
        )
    return {"patient_id": patient_id, "sessions": sessions_list}


@app.get("/history/{session_id}")
def get_session_history(session_id: str, client: Client = Depends(get_db)):
    """
    Retrieve the full conversation history + result for a specific session.
    Returns messages[], answers{}, and result{} as JSON from Supabase.
    """
    history = load_history(client, session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session history not found.")
    return history
