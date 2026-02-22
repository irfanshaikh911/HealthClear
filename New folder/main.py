"""
main.py — HealthClear FastAPI Application
Updated /rag-chat endpoint with:
  • LLM-driven dynamic questionnaire (no hardcoded questions)
  • Triage: surgery/hospital vs doctor consultation
  • Prior consultation follow-up branch
  • Free-text + clickable options both supported
  • Doctor recommendation path (when surgery NOT needed)
  • Full session persistence to Supabase chat_history
"""
import json
import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

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
from services.cost_engine import (
    calculate_personalized_cost,
    calculate_adjusted_complication,
    calculate_insurance_breakdown,
)
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
    build_doctor_recommendation,   # ← NEW: doctor-path handler
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


# ── Schemas ───────────────────────────────────────────────────────────────────

class RagChatMessage(BaseModel):
    """
    /rag-chat request body.

    Starting a session:
        POST /rag-chat  { "patient_id": 1 }

    Continuing a session:
        POST /rag-chat  { "session_id": "uuid", "message": "I have chest pain" }

    Anonymous start:
        POST /rag-chat  {}
    """
    patient_id: Optional[int] = None
    session_id: Optional[str] = None
    message: Optional[str] = None


class DoctorInfo(BaseModel):
    doctor_name: str
    specialization: Optional[str] = None
    experience: Optional[str] = None
    city: Optional[str] = None
    clinic: Optional[str] = None
    consultation_fee: Optional[str] = None


class DoctorRecommendationResult(BaseModel):
    type: str = "doctor_recommendation"
    specialization: str
    triage_reason: str
    doctors: list[DoctorInfo]
    ai_explanation: str
    prior_consultation_note: str


class RagChatResponse(BaseModel):
    session_id: str
    reply: str                                     # assistant message
    missing_fields: list = []                      # still-needed fields
    collected: dict = {}                           # everything gathered so far
    is_complete: bool = False                      # True = results ready
    result: Optional[ChatResponse] = None          # hospital cost result (surgery path)
    doctor_result: Optional[DoctorRecommendationResult] = None  # doctor result (consult path)
    next_field: Optional[str] = None              # hint to frontend for options
    suggested_options: list = []                   # clickable button labels
    recommendation_type: Optional[str] = None      # "hospital" | "specialist" | "gp"


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="HealthClear API",
    description="Conversational healthcare cost estimation & doctor/hospital recommendation.",
    version="4.0.0",
)

# In-memory RAG session store (consider Redis for production)
# { session_id: { collected, messages, patient_id, knowledge_ctx, patient_ctx } }
_rag_sessions: dict = {}


@app.on_event("startup")
def startup_event():
    client = get_db()
    seed(client)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_procedure_options(client: Client) -> list[str]:
    result = client.table("procedures").select("name").order("name").execute()
    return [r["name"] for r in result.data] if result.data else []


def _get_city_options(client: Client) -> list[str]:
    result = client.table("hospitals").select("city").execute()
    seen, cities = set(), []
    for row in result.data or []:
        c = row["city"].strip().title()
        if c not in seen:
            seen.add(c)
            cities.append(c)
    return sorted(cities)


# ── /rag-chat ─────────────────────────────────────────────────────────────────

@app.post("/rag-chat", response_model=RagChatResponse)
def rag_chat(message: RagChatMessage, client: Client = Depends(get_db)):
    """
    Fully conversational RAG chatbot.

    Flow:
    ┌─────────────────────────────────────────────────────┐
    │  Session start → load patient profile + greet       │
    │       ↓                                             │
    │  Detect intent (general Q&A / hospital / doctor)    │
    │       ↓                                             │
    │  Extract fields from free-text dynamically          │
    │       ↓                                             │
    │  Triage: needs surgery? → hospital path             │
    │          just consult?  → doctor path               │
    │       ↓                                             │
    │  Ask prior consultation questions (LLM-generated)   │
    │       ↓                                             │
    │  Collect remaining fields one-by-one (LLM-driven)  │
    │       ↓                                             │
    │  is_complete=True → run cost engine OR find doctors │
    │       ↓                                             │
    │  Save full result to Supabase chat_history          │
    └─────────────────────────────────────────────────────┘
    """

    # ── NEW SESSION ───────────────────────────────────────────────────────
    if not message.session_id:
        import uuid
        session_id = str(uuid.uuid4())

        # Pull DB knowledge (hospitals, procedures, doctors, risk conditions)
        knowledge_ctx = build_knowledge_context(client)

        # Load patient profile if logged in
        patient_ctx_text = ""
        prefilled: dict = {}
        if message.patient_id:
            patient_ctx_text = build_patient_context(client, message.patient_id)
            raw_ctx = fetch_patient_context(client, message.patient_id)
            if raw_ctx:
                prefilled, _ = prefill_from_patient(raw_ctx)

        # Store session state
        _rag_sessions[session_id] = {
            "collected": prefilled,
            "messages": [],
            "patient_id": message.patient_id,
            "knowledge_ctx": knowledge_ctx,
            "patient_ctx": patient_ctx_text,
        }

        # Persist session row to Supabase
        try:
            init_history(client, session_id, message.patient_id)
        except Exception:
            pass

        # Generate warm personalized opening with intent options
        opening = generate_rag_opening(knowledge_ctx, patient_ctx_text, prefilled)

        try:
            append_message(client, session_id, "assistant", opening)
        except Exception:
            pass

        return RagChatResponse(
            session_id=session_id,
            reply=opening,
            missing_fields=[],
            collected=prefilled,
            is_complete=False,
            suggested_options=[
                "Ask a health question",
                "Find a doctor for me",
                "Find a hospital / surgery",
                "Understand my bill",
            ],
        )

    # ── CONTINUE SESSION ──────────────────────────────────────────────────
    session_id = message.session_id
    state = _rag_sessions.get(session_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please start a new session.",
        )

    if not message.message:
        raise HTTPException(
            status_code=422,
            detail="Provide 'message' to continue the session.",
        )

    user_msg = message.message

    # Save user turn to Supabase
    try:
        append_message(client, session_id, "user", user_msg)
    except Exception:
        pass

    # ── Core RAG turn ─────────────────────────────────────────────────────
    turn = process_rag_turn(
        user_message=user_msg,
        collected=state["collected"],
        knowledge_context=state["knowledge_ctx"],
        patient_context=state["patient_ctx"],
        message_history=state["messages"],
    )

    # Update in-memory state
    state["collected"] = turn["collected"]
    state["messages"].append({"role": "user", "content": user_msg})
    state["messages"].append({"role": "assistant", "content": turn["reply"]})

    # Persist assistant reply + snapshot of collected answers
    try:
        append_message(client, session_id, "assistant", turn["reply"])
        save_answers(client, session_id, state["collected"])
    except Exception:
        pass

    # ── NOT COMPLETE YET — return next question ───────────────────────────
    if not turn["is_complete"]:
        return RagChatResponse(
            session_id=session_id,
            reply=turn["reply"],
            missing_fields=turn["missing"],
            collected=state["collected"],
            is_complete=False,
            next_field=turn.get("next_field"),
            suggested_options=turn.get("suggested_options", []),
            recommendation_type=state["collected"].get("recommendation_type"),
        )

    # ── COMPLETE — branch on recommendation_type ──────────────────────────
    rec_type = state["collected"].get("recommendation_type", "gp")

    if rec_type == "hospital":
        return _handle_hospital_path(session_id, state, turn, client)
    else:
        return _handle_doctor_path(session_id, state, turn, client)


# ── Hospital path ─────────────────────────────────────────────────────────────

def _handle_hospital_path(
    session_id: str,
    state: dict,
    turn: dict,
    client: Client,
) -> RagChatResponse:
    """Run existing cost engine for hospital/surgery recommendations."""
    try:
        q_response = _run_cost_engine(
            session_id=session_id,
            answers=state["collected"],
            client=client,
            patient_id=state.get("patient_id"),
        )
        return RagChatResponse(
            session_id=session_id,
            reply=turn["reply"],
            collected=state["collected"],
            is_complete=True,
            result=q_response.result,
            recommendation_type="hospital",
            suggested_options=[
                "Tell me more about the top hospital",
                "Compare costs in detail",
                "Find a doctor instead",
                "Start over",
            ],
        )
    except HTTPException as e:
        return RagChatResponse(
            session_id=session_id,
            reply=f"I ran into an issue finding hospitals: {e.detail} Could you double-check your city or procedure name?",
            collected=state["collected"],
            is_complete=False,
            suggestion=["Try a different city", "Tell me the procedure name"],
        )


# ── Doctor path ───────────────────────────────────────────────────────────────

def _handle_doctor_path(
    session_id: str,
    state: dict,
    turn: dict,
    client: Client,
) -> RagChatResponse:
    """
    Find doctor recommendations when surgery is NOT needed.
    Uses build_doctor_recommendation from rag_service.
    """
    try:
        doc_result_raw = build_doctor_recommendation(state["collected"], client)

        # Validate / coerce doctor dicts into DoctorInfo
        doctors = [
            DoctorInfo(
                doctor_name=d.get("doctor_name", "Unknown"),
                specialization=d.get("specialization"),
                experience=d.get("experience"),
                city=d.get("city"),
                clinic=d.get("clinic"),
                consultation_fee=d.get("consultation_fee"),
            )
            for d in doc_result_raw.get("doctors", [])
        ]

        doc_result = DoctorRecommendationResult(
            type="doctor_recommendation",
            specialization=doc_result_raw.get("specialization", "General Physician"),
            triage_reason=doc_result_raw.get("triage_reason", ""),
            doctors=doctors,
            ai_explanation=doc_result_raw.get("ai_explanation", ""),
            prior_consultation_note=doc_result_raw.get("prior_consultation_note", ""),
        )

        # Persist result to Supabase
        try:
            save_result(client, session_id, {
                "type": "doctor_recommendation",
                "specialization": doc_result.specialization,
                "doctors": [d.dict() for d in doctors],
                "ai_explanation": doc_result.ai_explanation,
            })
        except Exception:
            pass

        # Craft a reply that bridges the questionnaire to the results
        bridge_reply = turn["reply"]
        if not bridge_reply.strip():
            bridge_reply = (
                f"Based on everything you've shared, here are my top {doc_result.specialization} "
                f"recommendations in {state['collected'].get('city', 'your city')}. "
                + (doc_result.prior_consultation_note or "")
            )

        return RagChatResponse(
            session_id=session_id,
            reply=bridge_reply,
            collected=state["collected"],
            is_complete=True,
            doctor_result=doc_result,
            recommendation_type=state["collected"].get("recommendation_type", "gp"),
            suggested_options=[
                "Tell me more about the top doctor",
                "I actually need a hospital instead",
                "Ask another health question",
                "Start over",
            ],
        )

    except Exception as e:
        return RagChatResponse(
            session_id=session_id,
            reply=f"I had trouble finding doctors right now: {str(e)}. Please try again or specify a different city.",
            collected=state["collected"],
            is_complete=False,
        )


# ── Cost engine (unchanged, used for hospital path) ───────────────────────────

def _run_cost_engine(
    session_id: str,
    answers: dict,
    client: Client,
    summary: str = None,
    prefilled_fields: list = None,
    patient_id: int = None,
) -> QuestionResponse:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage

    chat_data = build_chat_request(answers)
    procedure_name = chat_data["selected_procedure"].strip()

    # 1. Exact match
    proc_result = client.table("procedures").select("*").ilike("name", procedure_name).execute()
    # 2. Fuzzy match
    if not proc_result.data:
        proc_result = client.table("procedures").select("*").ilike("name", f"%{procedure_name}%").execute()

    if proc_result.data:
        procedure = Procedure.from_dict(proc_result.data[0])
    else:
        procedure = _estimate_procedure_with_groq(procedure_name, client)

    # Hospitals by city
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
                f"Available: {', '.join(_get_city_options(client))}."
            ),
        )
    hospitals = [Hospital.from_dict(h) for h in hosp_result.data]

    risk_result = client.table("risk_conditions").select("*").execute()
    risk_map = {rc["name"]: float(rc["cost_multiplier"]) for rc in risk_result.data}

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

    ins = chat_data["insurance_status"].lower()
    insured_hospitals = [h for h in ranked if h.insurance_accepted]
    ins_count = len(insured_hospitals)
    total_hospitals = len(ranked)

    if ins == "none":
        insurance_note = (
            f"No insurance detected. ₹{cost_min:,.0f}–₹{cost_max:,.0f} payable out-of-pocket. "
            "Ask the hospital about EMI options."
        )
    else:
        if insured_hospitals:
            covered = [h.amount_covered for h in insured_hospitals]
            oop = [h.patient_out_of_pocket for h in insured_hospitals]
            scheme = "Ayushman Bharat / PMJAY" if ins == "government" else "Private insurance"
            insurance_note = (
                f"With {scheme}, insurance covers ₹{min(covered):,.0f}–₹{max(covered):,.0f} "
                f"({ins_count} of {total_hospitals} hospitals). "
                f"Your out-of-pocket: ₹{min(oop):,.0f}–₹{max(oop):,.0f}."
            )
        else:
            scheme = "Government scheme" if ins == "government" else "Private insurance"
            insurance_note = (
                f"None of the listed hospitals accept your {scheme}. "
                f"Full amount ₹{cost_min:,.0f}–₹{cost_max:,.0f} payable out-of-pocket."
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

    try:
        result_payload = {
            "estimated_cost_range": [cost_min, cost_max],
            "budget_fit": budget_fit,
            "insurance_note": insurance_note,
            "top_hospital": ranked[0].hospital_name if ranked else None,
            "ai_explanation": ai_explanation,
            "all_hospitals": [
                {"name": h.hospital_name, "cost": h.personalized_cost,
                 "success_rate": h.success_rate, "value_score": h.value_score}
                for h in ranked
            ],
        }
        save_answers(client, session_id, answers)
        save_result(client, session_id, result_payload)
    except Exception:
        pass

    return QuestionResponse(
        session_id=session_id,
        summary=summary,
        prefilled_fields=prefilled_fields or [],
        is_complete=True,
        result=chat_response,
    )


def _estimate_procedure_with_groq(procedure_name: str, client: Client) -> Procedure:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage

    ref = client.table("procedures").select("name,base_cost,average_length_of_stay").execute().data or []
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, temperature=0.2)
            system = SystemMessage(content=(
                "You are a medical cost expert in India (2024 INR rates). "
                "Estimate procedure costs from known procedures. Return ONLY JSON."
            ))
            human = HumanMessage(content=(
                f"Procedure: \"{procedure_name}\"\n"
                f"Known: {json.dumps([{'name': p['name'], 'cost': p['base_cost']} for p in ref])}\n"
                "Return: {\"base_cost\": 95000, \"average_length_of_stay\": 4}"
            ))
            resp = llm.invoke([system, human])
            import re
            raw = re.sub(r"```(?:json)?", "", resp.content.strip()).strip().rstrip("```")
            data = json.loads(raw)
            return Procedure(
                id=0,
                name=procedure_name.title(),
                base_cost=float(data.get("base_cost", 80000)),
                average_length_of_stay=int(data.get("average_length_of_stay", 4)),
            )
        except Exception:
            pass
    return Procedure(id=0, name=procedure_name.title(), base_cost=80000.0, average_length_of_stay=4)


# ── Original /chat endpoint (unchanged) ──────────────────────────────────────

@app.post("/chat", response_model=QuestionResponse)
def chat(message: ChatMessage, client: Client = Depends(get_db)):
    """Original structured chat endpoint (unchanged)."""
    if not message.session_id:
        prefilled_answers = {}
        prefilled_fields = []
        opening_summary = None
        if message.patient_id:
            patient_ctx = fetch_patient_context(client, message.patient_id)
            if not patient_ctx:
                raise HTTPException(status_code=404, detail=f"Patient {message.patient_id} not found.")
            prefilled_answers, prefilled_fields = prefill_from_patient(patient_ctx)
            opening_summary = generate_opening_summary(patient_ctx, prefilled_fields)
        if not opening_summary:
            opening_summary = "👋 Hi! I'll help you estimate treatment costs. Let me ask a few questions."
        procedure_options = _get_procedure_options(client)
        city_options = _get_city_options(client)
        session_id = create_session(
            prefilled_answers=prefilled_answers,
            procedure_options=procedure_options,
            city_options=city_options,
            patient_context=opening_summary if message.patient_id else "",
        )
        first_q = get_next_question(session_id)
        if first_q is None:
            return _run_cost_engine(session_id, prefilled_answers, client, opening_summary, prefilled_fields)
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

    if not message.answer:
        raise HTTPException(status_code=422, detail="Provide 'answer' to continue.")
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


# ── History endpoints ─────────────────────────────────────────────────────────

@app.get("/history/patient/{patient_id}")
def get_patient_history(patient_id: int, client: Client = Depends(get_db)):
    sessions_list = get_all_sessions(client, patient_id)
    if not sessions_list:
        raise HTTPException(status_code=404, detail=f"No history for patient {patient_id}.")
    return {"patient_id": patient_id, "sessions": sessions_list}


@app.get("/history/{session_id}")
def get_session_history(session_id: str, client: Client = Depends(get_db)):
    history = load_history(client, session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found.")
    return history
