"""
Questionnaire Engine
Manages session state, the 9-question flow, and Groq-powered "Other" handling.
Procedure and city options are loaded dynamically from Supabase — NOT hardcoded here.
"""
import json
import os
import uuid
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


# ── Static question template ──────────────────────────────────────────────────
# Questions with "options": None will have their options injected at runtime
# from the Supabase database (procedures, cities).

QUESTIONS = [
    {
        "key": "selected_procedure",
        "question": "🏥 What medical procedure or treatment are you looking for?",
        "options": None,          # ← filled dynamically from DB at session start
        "allow_other": True,
        "other_prompt": "Please describe your medical condition or what you need treated:",
        "field_type": "str",
        "force_map": False,       # ← False: free text is accepted; engine handles unknown procedures
    },
    {
        "key": "age",
        "question": "🎂 What is your age group?",
        "options": ["Under 20", "20-40", "41-60", "61-80", "Above 80"],
        "allow_other": False,
        "field_type": "age",
    },
    {
        "key": "gender",
        "question": "👤 What is your gender?",
        "options": ["Male", "Female"],
        "allow_other": True,
        "other_prompt": "Please specify your gender:",
        "field_type": "str",
    },
    {
        "key": "city",
        "question": "📍 Which city are you in?",
        "options": None,          # ← filled dynamically from DB at session start
        "allow_other": True,
        "other_prompt": "Please type your city name:",
        "field_type": "str",
    },
    {
        "key": "comorbidities",
        "question": "🩺 Do you have any of the following health conditions?",
        "options": ["Diabetes", "Hypertension", "Both (Diabetes & Hypertension)", "None"],
        "allow_other": True,
        "other_prompt": "Please describe your health conditions:",
        "field_type": "comorbidities",
    },
    {
        "key": "smoking",
        "question": "🚬 Do you currently smoke?",
        "options": ["Yes", "No"],
        "allow_other": False,
        "field_type": "bool",
    },
    {
        "key": "insurance_status",
        "question": "🛡️ What is your insurance status?",
        "options": ["Private", "Government", "None"],
        "allow_other": False,
        "field_type": "str",
    },
    {
        "key": "budget_limit",
        "question": "💰 What is your approximate budget limit?",
        "options": [
            "Below ₹50,000",
            "₹50,000 – ₹1,00,000",
            "₹1,00,000 – ₹2,00,000",
            "Above ₹2,00,000",
        ],
        "allow_other": True,
        "other_prompt": "Please type your budget in rupees (e.g. 150000):",
        "field_type": "budget",
    },
    {
        "key": "room_preference",
        "question": "🛏️ What type of hospital room do you prefer?",
        "options": ["General", "Semi-private", "Private"],
        "allow_other": False,
        "field_type": "str",
    },
]

# ── Value maps ────────────────────────────────────────────────────────────────

AGE_MAP = {
    "under 20": 15,
    "20-40": 30,
    "41-60": 50,
    "61-80": 70,
    "above 80": 85,
}

BUDGET_MAP = {
    "below ₹50,000": 50000.0,
    "₹50,000 – ₹1,00,000": 100000.0,
    "₹1,00,000 – ₹2,00,000": 200000.0,
    "above ₹2,00,000": 300000.0,
}

COMORBIDITY_MAP = {
    "diabetes": ["diabetes"],
    "hypertension": ["hypertension"],
    "both (diabetes & hypertension)": ["diabetes", "hypertension"],
    "none": [],
}

# ── In-memory session store ───────────────────────────────────────────────────

sessions: dict = {}


# ── LLM helper ───────────────────────────────────────────────────────────────

def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        temperature=0.3,
    )


# ── Session management ────────────────────────────────────────────────────────

def create_session(
    prefilled_answers: dict = None,
    procedure_options: list = None,
    city_options: list = None,
) -> str:
    """
    Create a new session.
    - prefilled_answers: from patient_service (skip known questions)
    - procedure_options: list of procedure names fetched from Supabase
    - city_options: list of city names fetched from Supabase
    """
    sid = str(uuid.uuid4())
    prefilled = prefilled_answers or {}

    # Build resolved questions with dynamic options injected
    resolved_questions = []
    for q in QUESTIONS:
        resolved_q = dict(q)
        if q["key"] == "selected_procedure" and procedure_options:
            resolved_q["options"] = procedure_options
        elif q["key"] == "city" and city_options:
            resolved_q["options"] = city_options
        elif resolved_q["options"] is None:
            resolved_q["options"] = []   # safety fallback
        resolved_questions.append(resolved_q)

    sessions[sid] = {
        "answers": dict(prefilled),
        "questions": resolved_questions,   # resolved, not QUESTIONS global
        "current_question_index": 0,
        "awaiting_other_text": False,
        "dynamic_options": None,
    }
    _skip_prefilled(sid)
    return sid


def _skip_prefilled(session_id: str):
    """Advance current_question_index past questions already answered."""
    state = sessions[session_id]
    qs = state["questions"]
    while state["current_question_index"] < len(qs):
        q = qs[state["current_question_index"]]
        if q["key"] in state["answers"]:
            state["current_question_index"] += 1
        else:
            break


def get_next_question(session_id: str) -> Optional[dict]:
    """Return the current unanswered question, or None if all done."""
    state = sessions[session_id]
    idx = state["current_question_index"]
    qs = state["questions"]
    if idx >= len(qs):
        return None
    q = qs[idx]
    opts = q["options"] + (["Other"] if q.get("allow_other") else [])
    return {
        "question": q["question"],
        "question_key": q["key"],
        "options": opts,
        "allow_other": q.get("allow_other", False),
        "awaiting_free_text": False,
    }


# ── Answer processing ─────────────────────────────────────────────────────────

def process_answer(session_id: str, answer: str) -> dict:
    """
    Process a user answer. Returns:
      {"type": "question", ...question fields...}
    OR
      {"type": "final", "collected_answers": dict}
    """
    state = sessions.get(session_id)
    if not state:
        return {"error": "Session not found or expired. Please start a new session."}

    qs = state["questions"]
    idx = state["current_question_index"]
    if idx >= len(qs):
        return {"type": "final", "collected_answers": state["answers"]}

    q = qs[idx]

    # ── Case 1: awaiting free text after "Other" ──────────────────────────
    if state["awaiting_other_text"]:
        groq_result = _call_groq_for_other(
            question_key=q["key"],
            question_text=q["question"],
            user_input=answer,
            existing_options=q["options"],
            force_map=q.get("force_map", False),
        )
        state["awaiting_other_text"] = False
        if groq_result.get("mapped_to"):
            _store_answer(state, q, groq_result["mapped_to"])
            state["current_question_index"] += 1
            _skip_prefilled(session_id)
        else:
            # New dynamic sub-options from Groq
            new_opts = groq_result.get("new_options", [answer])
            state["dynamic_options"] = new_opts
            return {
                "type": "question",
                "question": "Please choose the most relevant option:",
                "question_key": q["key"],
                "options": new_opts + ["Other"],
                "allow_other": True,
                "awaiting_free_text": False,
            }

    # ── Case 2: picking from Groq-generated dynamic options ───────────────
    elif state["dynamic_options"] is not None:
        if answer.lower() == "other":
            state["dynamic_options"] = None
            state["awaiting_other_text"] = True
            return {
                "type": "question",
                "question": q.get("other_prompt", f"Please describe: {q['question']}"),
                "question_key": q["key"],
                "options": [],
                "allow_other": False,
                "awaiting_free_text": True,
            }
        _store_answer(state, q, answer)
        state["dynamic_options"] = None
        state["current_question_index"] += 1
        _skip_prefilled(session_id)

    # ── Case 3: normal answer ─────────────────────────────────────────────
    else:
        if answer.lower() == "other":
            state["awaiting_other_text"] = True
            return {
                "type": "question",
                "question": q.get("other_prompt", f"Please describe: {q['question']}"),
                "question_key": q["key"],
                "options": [],
                "allow_other": False,
                "awaiting_free_text": True,
            }
        _store_answer(state, q, answer)
        state["current_question_index"] += 1
        _skip_prefilled(session_id)

    # ── Check completion ──────────────────────────────────────────────────
    if state["current_question_index"] >= len(qs):
        return {"type": "final", "collected_answers": state["answers"]}

    # Return next question
    next_q = qs[state["current_question_index"]]
    opts = next_q["options"] + (["Other"] if next_q.get("allow_other") else [])
    return {
        "type": "question",
        "question": next_q["question"],
        "question_key": next_q["key"],
        "options": opts,
        "allow_other": next_q.get("allow_other", False),
        "awaiting_free_text": False,
    }


# ── Groq "Other" handler ──────────────────────────────────────────────────────

def _call_groq_for_other(
    question_key: str,
    question_text: str,
    user_input: str,
    existing_options: list,
    force_map: bool = False,
) -> dict:
    """
    For 'selected_procedure': if user types free text, just accept it as-is
    (the cost engine will handle unknown procedures via Groq estimation).
    For other questions: map to existing option or generate sub-options.
    Returns {"mapped_to": str|None, "new_options": list[str]}
    """
    # Procedure: accept literally — don't force to existing names
    if question_key == "selected_procedure":
        return {"mapped_to": user_input, "new_options": []}

    # Other questions: try LLM mapping / sub-options
    llm = _get_llm()
    system_msg = SystemMessage(content=(
        "You are a medical assistant for a healthcare cost estimation system in India. "
        "Interpret patient responses and either map to an existing option or generate "
        "3-5 specific, relevant sub-options. Respond ONLY with valid JSON."
    ))
    human_msg = HumanMessage(content=(
        f"Question: \"{question_text}\"\n"
        f"Existing options: {existing_options}\n"
        f"Patient typed: \"{user_input}\"\n\n"
        f"Either map to one existing option OR generate 3-5 new specific options.\n"
        f"JSON: {{\"mapped_to\": null or \"<existing option>\", \"new_options\": [\"...\", \"...\"]}}"
    ))
    try:
        response = llm.invoke([system_msg, human_msg])
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception:
        return {"mapped_to": None, "new_options": [user_input]}


# ── Answer normalizer ─────────────────────────────────────────────────────────

def _store_answer(state: dict, question: dict, raw_answer: str):
    key = question["key"]
    field_type = question["field_type"]
    val = raw_answer.strip()

    if field_type == "age":
        state["answers"]["age"] = AGE_MAP.get(val.lower(), 30)

    elif field_type == "budget":
        budget = BUDGET_MAP.get(val.lower())
        if budget is None:
            try:
                budget = float(val.replace(",", "").replace("₹", "").replace(" ", ""))
            except ValueError:
                budget = 100000.0
        state["answers"]["budget_limit"] = budget

    elif field_type == "comorbidities":
        state["answers"]["comorbidities"] = COMORBIDITY_MAP.get(
            val.lower(), [val.lower()]
        )

    elif field_type == "bool":
        state["answers"]["smoking"] = val.lower() == "yes"

    else:
        state["answers"][key] = val.lower()


# ── Final assembly ────────────────────────────────────────────────────────────

def build_chat_request(answers: dict) -> dict:
    """Convert collected session answers into a ChatRequest-compatible dict."""
    return {
        "age": answers.get("age", 30),
        "gender": answers.get("gender", "male"),
        "city": answers.get("city", "pune"),
        "insurance_status": answers.get("insurance_status", "none"),
        "budget_limit": answers.get("budget_limit", 100000.0),
        "selected_procedure": answers.get("selected_procedure", ""),
        "comorbidities": answers.get("comorbidities", []),
        "smoking": answers.get("smoking", False),
        "room_preference": answers.get("room_preference", "general"),
    }


def build_known_summary(session_id: str) -> str:
    """
    Returns a short human-readable summary of what has been collected so far.
    """
    state = sessions.get(session_id)
    if not state:
        return ""

    answers = state.get("answers", {})
    if not answers:
        return ""

    LABEL_MAP = {
        "selected_procedure": "Procedure",
        "age":                "Age",
        "gender":             "Gender",
        "city":               "City",
        "comorbidities":      "Conditions",
        "smoking":            "Smoker",
        "insurance_status":   "Insurance",
        "budget_limit":       "Budget",
        "room_preference":    "Room",
    }

    parts = []
    for key, label in LABEL_MAP.items():
        val = answers.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            display = ", ".join(val) if val else "None"
        elif isinstance(val, bool):
            display = "Yes" if val else "No"
        elif isinstance(val, float) and key == "budget_limit":
            display = f"₹{val:,.0f}"
        else:
            display = str(val).title()
        parts.append(f"{label}: {display}")

    return "📋 Known so far: " + " | ".join(parts) if parts else ""
