"""
services/rag_service.py  — HealthClear Enhanced RAG Service
============================================================

Key design decisions
--------------------
* NO hardcoded questions.  The LLM decides what to ask next based on what it
  already knows and what is still missing.
* Supports BOTH free-text chat AND clickable option buttons — the LLM figures
  out the intent regardless of how the user expresses themselves.
* Triage step: LLM decides if condition likely needs surgery/hospital admission
  or just a doctor consultation, then branches the flow accordingly.
* Prior-consultation branch: asks what a previous doctor said, whether it helped,
  and factors that into recommendations.
* All state lives in the caller (main.py _rag_sessions dict + Supabase
  chat_history).  This file is pure logic — no global mutable state.

Session `collected` dict keys
------------------------------
Core (all paths)
  symptom            str   — what the patient described (free-form kept intact)
  urgency            str   — severity / how long
  city               str   — city for hospital/doctor search
  budget             str   — budget range string
  has_insurance      bool
  insurance_type     str   — "government" | "private" | "none"

Triage output (set by _triage_condition)
  recommendation_type  str  — "hospital" | "specialist" | "gp"
  specialization       str  — mapped specialization for doctor search
  triage_reason        str  — LLM's reasoning (stored for transparency)
  needs_surgery        bool — convenience flag

Prior-consultation branch (only when prev_consultation == "yes_doctor")
  prev_consultation    str  — "yes_doctor" | "yes_self" | "no"
  prev_advice_text     str  — what the earlier doctor said
  prev_advice_helped   str  — "yes" | "partial" | "no" | "not_followed"

Hospital path extras
  procedure            str  — procedure name (derived or asked)
  age                  int
  comorbidities        list[str]
  smoking              bool

Preference
  preference           str  — "experienced" | "cheapest" | "best_success" | "any"
"""

import json
import os
import re
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.core.config import settings

# ── Groq client factory ───────────────────────────────────────────────────────

def _llm(temperature: float = 0.3) -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.GROQ_API_KEY,
        temperature=temperature,
    )


# ── Required-field sets per path ──────────────────────────────────────────────

# Fields needed before triage can fire
PRE_TRIAGE_FIELDS = {"symptom", "urgency"}

# Fields needed for BOTH hospital and doctor paths
COMMON_FIELDS = {"city", "budget", "has_insurance"}

# Additional fields only for hospital path
HOSPITAL_EXTRA_FIELDS = {"procedure", "age", "comorbidities", "smoking", "preference"}

# Fields that are asked dynamically by LLM (not listed as REQUIRED so engine
# doesn't block on them — LLM will ask if relevant)
DYNAMIC_OPTIONAL = {"prev_consultation", "prev_advice_text", "prev_advice_helped",
                    "insurance_type", "specialization"}

# The minimal set the engine checks for "complete" — varies by path, resolved at runtime
REQUIRED_FIELDS = PRE_TRIAGE_FIELDS | COMMON_FIELDS  # extended after triage


# ── Knowledge context builder (called once per session) ───────────────────────

def build_knowledge_context(client) -> str:
    """
    Pulls hospitals, procedures, risk_conditions, doctors from Supabase and
    returns a compact text block injected into every LLM system prompt.
    """
    lines = []

    # Hospitals
    h_res = client.table("hospitals").select(
        "name,city,base_cost,success_rate,accepts_insurance,insurance_coverage_available"
    ).execute()
    if h_res.data:
        lines.append("=== HOSPITALS IN DATABASE ===")
        for h in h_res.data:
            ins = "accepts insurance" if h["accepts_insurance"] else "no insurance"
            lines.append(
                f"  • {h['name']} ({h['city']}) — base cost ₹{h['base_cost']:,.0f}, "
                f"success rate {h['success_rate']}%, {ins}, "
                f"coverage: {h.get('insurance_coverage_available','N/A')}"
            )

    # Procedures
    p_res = client.table("procedures").select("name,base_cost,average_length_of_stay").execute()
    if p_res.data:
        lines.append("\n=== PROCEDURES IN DATABASE ===")
        for p in p_res.data:
            lines.append(
                f"  • {p['name']} — base ₹{p['base_cost']:,.0f}, avg stay {p['average_length_of_stay']} days"
            )

    # Doctors
    try:
        d_res = client.table("doctor").select(
            "doctor_name,specialization,experience,city,consultation_fee,clinic"
        ).execute()
        if d_res.data:
            lines.append("\n=== DOCTORS IN DATABASE ===")
            for d in d_res.data:
                lines.append(
                    f"  • Dr. {d['doctor_name']} ({d['specialization']}, {d['experience']}) "
                    f"— {d['city']}, fee {d['consultation_fee']}, clinic: {d.get('clinic','N/A')}"
                )
    except Exception:
        pass  # gracefully skip if doctor table query fails transiently

    # Risk conditions
    r_res = client.table("risk_conditions").select("name,cost_multiplier").execute()
    if r_res.data:
        lines.append("\n=== RISK CONDITIONS (cost multipliers) ===")
        for r in r_res.data:
            lines.append(f"  • {r['name']}: ×{r['cost_multiplier']}")

    return "\n".join(lines)


def build_patient_context(client, patient_id: int) -> str:
    """
    Fetches patient profile + medical history and returns a human-readable
    summary to embed in the LLM system prompt.
    """
    pat = client.table("patients").select("*").eq("patient_id", patient_id).single().execute()
    if not pat.data:
        return ""
    p = pat.data

    hist = client.table("medical_history").select("*").eq("patient_id", patient_id).execute()

    from datetime import date
    try:
        dob = date.fromisoformat(str(p.get("date_of_birth", "")))
        age = (date.today() - dob).days // 365
    except Exception:
        age = "unknown"

    lines = [
        f"=== PATIENT PROFILE ===",
        f"Name: {p.get('full_name', 'Unknown')}",
        f"Age: {age}",
        f"Gender: {p.get('gender', 'Unknown')}",
        f"Blood type: {p.get('blood_type', 'Unknown')}",
        f"Height: {p.get('height_cm', '?')} cm, Weight: {p.get('weight_kg', '?')} kg",
        f"Allergies: {p.get('allergies') or 'None reported'}",
        f"Current medications: {p.get('medications') or 'None reported'}",
        f"Medical history notes: {p.get('medical_history') or 'None'}",
        f"Organ donor: {'Yes' if p.get('organ_donor') else 'No'}",
    ]
    if p.get("is_pregnant"):
        lines.append("⚠️  Patient is currently pregnant.")

    if hist.data:
        lines.append("\nDiagnosed conditions:")
        for h in hist.data:
            lines.append(
                f"  • {h['condition_name']} ({h.get('status','?')}) "
                f"— diagnosed {h.get('diagnosis_date','unknown')}"
                + (f": {h['notes']}" if h.get("notes") else "")
            )

    return "\n".join(lines)


# ── Opening message ───────────────────────────────────────────────────────────

def generate_rag_opening(knowledge_ctx: str, patient_ctx: str, prefilled: dict) -> str:
    """
    Generate a warm, personalized opening message.
    If patient is known, greet by name and acknowledge their conditions.
    Always present the two top-level intents as clear options.
    """
    system = SystemMessage(content=f"""You are HealthClear, a warm and knowledgeable healthcare assistant.
You help patients in India find the right doctor or hospital and understand treatment costs.

{patient_ctx if patient_ctx else "No patient profile loaded — treat as anonymous user."}

{knowledge_ctx}

TASK: Write a personalized opening message that:
1. Greets the patient by name if known, otherwise greet warmly.
2. If they have known conditions, briefly acknowledge them (e.g. "I see you're managing diabetes").
3. Clearly present TWO paths they can take:
   - 🩺 Ask a general health / medication question
   - 🏥 Get a doctor or hospital recommendation
4. Also mention they can just type freely — they don't need to click options.
5. Keep it concise, warm, human. No bullet-point lists. 2-3 short paragraphs max.
6. End with an open invitation like "What can I help you with today?"

Return ONLY the message text — no JSON, no metadata.""")

    resp = _llm(temperature=0.5).invoke([system])
    return resp.content.strip()


# ── Core turn processor ───────────────────────────────────────────────────────

def process_rag_turn(
    user_message: str,
    collected: dict,
    knowledge_context: str,
    patient_context: str,
    message_history: list[dict],
) -> dict:
    """
    Main entry point called by the /rag-chat endpoint on every user turn.

    Returns a dict:
    {
        "reply": str,               — assistant message to show user
        "collected": dict,          — updated collected fields
        "missing": list[str],       — still-missing required fields
        "is_complete": bool,        — True = ready to run cost engine
        "next_field": str | None,   — hint for frontend to show options
        "suggested_options": list,  — option buttons for next_field
        "intent": str,              — "hospital" | "doctor" | "general_qa" | "unknown"
    }
    """

    # Step 1 — Extract any new structured info from the user message
    collected = _extract_fields(user_message, collected, knowledge_context, patient_context, message_history)

    # Step 2 — Detect top-level intent if not yet known
    if "intent" not in collected:
        collected = _detect_intent(user_message, collected, message_history)

    intent = collected.get("intent", "unknown")

    # Step 3 — Handle general Q&A intent immediately (no questionnaire needed)
    if intent == "general_qa":
        reply = _answer_general_question(user_message, collected, knowledge_context, patient_context, message_history)
        # After answering, offer to switch to recommendation path
        reply += "\n\n---\nWould you like me to find a doctor or hospital for you? Just say the word."
        return {
            "reply": reply,
            "collected": collected,
            "missing": [],
            "is_complete": False,
            "next_field": None,
            "suggested_options": ["Find a doctor for me", "Find a hospital", "Ask another question"],
            "intent": intent,
        }

    # Step 4 — Triage (only after we have symptom + urgency)
    if (
        "recommendation_type" not in collected
        and "symptom" in collected
        and "urgency" in collected
        and intent in ("hospital", "doctor", "unknown")
    ):
        collected = _triage_condition(collected, knowledge_context, patient_context)

    rec_type = collected.get("recommendation_type")  # "hospital" | "specialist" | "gp"

    # Step 5 — Prior consultation follow-up (only if we know rec_type and haven't asked yet)
    if rec_type and "prev_consultation" not in collected:
        reply, opts = _ask_prior_consultation(collected, message_history)
        return {
            "reply": reply,
            "collected": collected,
            "missing": _compute_missing(collected, rec_type),
            "is_complete": False,
            "next_field": "prev_consultation",
            "suggested_options": opts,
            "intent": intent,
        }

    # If prev_consultation = yes_doctor and we don't have advice text yet
    if (
        collected.get("prev_consultation") == "yes_doctor"
        and "prev_advice_text" not in collected
    ):
        reply = _ask_prev_advice(collected, message_history)
        return {
            "reply": reply,
            "collected": collected,
            "missing": _compute_missing(collected, rec_type),
            "is_complete": False,
            "next_field": "prev_advice_text",
            "suggested_options": [],
            "intent": intent,
        }

    if (
        collected.get("prev_consultation") == "yes_doctor"
        and "prev_advice_text" in collected
        and "prev_advice_helped" not in collected
    ):
        reply, opts = _ask_advice_helped(collected, message_history)
        return {
            "reply": reply,
            "collected": collected,
            "missing": _compute_missing(collected, rec_type),
            "is_complete": False,
            "next_field": "prev_advice_helped",
            "suggested_options": opts,
            "intent": intent,
        }

    # Step 6 — Compute what's still missing and ask for it
    missing = _compute_missing(collected, rec_type)

    if not missing:
        # ── All required info collected — signal completion ────────────────
        closing_reply = _generate_completion_message(collected, knowledge_context, patient_context)
        return {
            "reply": closing_reply,
            "collected": collected,
            "missing": [],
            "is_complete": True,
            "next_field": None,
            "suggested_options": [],
            "intent": intent,
        }

    # Step 7 — Ask the LLM for the next question (dynamic, context-aware)
    reply, next_field, opts = _ask_next_question(
        missing=missing,
        collected=collected,
        knowledge_context=knowledge_context,
        patient_context=patient_context,
        message_history=message_history,
        user_message=user_message,
    )

    return {
        "reply": reply,
        "collected": collected,
        "missing": missing,
        "is_complete": False,
        "next_field": next_field,
        "suggested_options": opts,
        "intent": intent,
    }


# ── Field extractor ───────────────────────────────────────────────────────────

_EXTRACT_SYSTEM = """You are a medical information extractor.
Extract structured data from a patient's message and return ONLY valid JSON.

Fields to extract (include only fields you're confident about):
  symptom            : string — what they described (keep their words, expand if needed)
  urgency            : string — how long / how severe ("started today", "chronic", "few days", etc.)
  city               : string — city name for hospital search (title case)
  budget             : string — one of: "under_1000", "1000_10000", "10000_50000", "50000_200000", "above_200000"
  has_insurance      : boolean
  insurance_type     : string — "government" | "private" | "none"
  procedure          : string — specific medical procedure if mentioned
  age                : integer
  comorbidities      : list of strings — e.g. ["diabetes", "hypertension"]
  smoking            : boolean
  preference         : string — "experienced" | "cheapest" | "best_success" | "any"
  prev_consultation  : string — "yes_doctor" | "yes_self" | "no"
  prev_advice_text   : string — what a previous doctor said
  prev_advice_helped : string — "yes" | "partial" | "no" | "not_followed"
  intent             : string — "general_qa" | "hospital" | "doctor" | "unknown"

Rules:
- Return {} if nothing can be extracted confidently.
- Do NOT invent values. Only extract what the user actually said.
- For symptoms expressed casually ("my knee hurts", "I've been feverish"), set symptom field.
- If user says "find me a hospital" or "need surgery" → intent: "hospital"
- If user says "doctor recommendation", "consult", "specialist" → intent: "doctor"
- If user says "what is", "explain", "tell me about", "is it safe" → intent: "general_qa"
- Return pure JSON only — no markdown, no explanation."""


def _extract_fields(
    user_message: str,
    collected: dict,
    knowledge_context: str,
    patient_context: str,
    message_history: list[dict],
) -> dict:
    """Run LLM extraction and merge new fields into collected (never overwrite existing)."""
    history_text = _format_history(message_history[-6:])  # last 3 turns for context

    system = SystemMessage(content=_EXTRACT_SYSTEM)
    human = HumanMessage(content=(
        f"Conversation so far:\n{history_text}\n\n"
        f"Already collected: {json.dumps(collected)}\n\n"
        f"New patient message: \"{user_message}\"\n\n"
        "Extract new fields from the new message only. Return JSON."
    ))

    try:
        resp = _llm(temperature=0.0).invoke([system, human])
        raw = resp.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        extracted = json.loads(raw)
        # Merge: overwrite if a new non-empty value was extracted from the new message
        for k, v in extracted.items():
            if v is not None and v != "" and v != []:
                collected[k] = v
    except Exception:
        pass  # extraction failure is non-fatal; LLM will ask again

    return collected


# ── Intent detection ──────────────────────────────────────────────────────────

def _detect_intent(user_message: str, collected: dict, message_history: list[dict]) -> dict:
    """
    If extraction didn't set intent, use a lightweight classifier.
    Sets collected["intent"].
    """
    system = SystemMessage(content=(
        "Classify the patient's intent from their message. "
        "Return ONLY one of: general_qa | hospital | doctor | unknown\n"
        "- general_qa: asking about symptoms, medications, diseases, what something means\n"
        "- hospital: needs surgery, procedure, admission, hospital recommendation\n"
        "- doctor: needs a doctor/specialist consultation, no surgery mentioned\n"
        "- unknown: not enough info yet"
    ))
    human = HumanMessage(content=f"Patient message: \"{user_message}\"")
    try:
        resp = _llm(temperature=0.0).invoke([system, human])
        intent = resp.content.strip().lower().split()[0]
        if intent in ("general_qa", "hospital", "doctor", "unknown"):
            collected["intent"] = intent
    except Exception:
        collected["intent"] = "unknown"
    return collected


# ── Triage ────────────────────────────────────────────────────────────────────

def _triage_condition(collected: dict, knowledge_context: str, patient_context: str) -> dict:
    """
    Given symptom + urgency (and optional prior history), decide:
      recommendation_type: "hospital" | "specialist" | "gp"
      specialization: which doctor type to look for
      needs_surgery: bool
      triage_reason: short explanation
    """
    system = SystemMessage(content=f"""You are a medical triage assistant in India.
Given a patient's symptoms, decide the appropriate care pathway.

{patient_context}

{knowledge_context}

Return ONLY valid JSON with these fields:
{{
  "recommendation_type": "hospital" | "specialist" | "gp",
  "needs_surgery": true | false,
  "specialization": "<doctor specialization to look for, e.g. Cardiologist>",
  "triage_reason": "<1-2 sentence reason for this decision>"
}}

Guidelines:
- "hospital" = likely needs admission, surgery, or emergency care
- "specialist" = needs a specialist doctor consultation (no surgery expected)
- "gp" = general physician / primary care is sufficient
- Be conservative — only recommend "hospital" if symptoms strongly suggest it
- Consider patient's existing conditions from profile when triaging""")

    human = HumanMessage(content=(
        f"Symptom: {collected.get('symptom', 'unknown')}\n"
        f"Urgency: {collected.get('urgency', 'unknown')}\n"
        f"Prior advice: {collected.get('prev_advice_text', 'none')}\n"
        f"Prior advice helped: {collected.get('prev_advice_helped', 'unknown')}"
    ))

    try:
        resp = _llm(temperature=0.1).invoke([system, human])
        raw = re.sub(r"```(?:json)?", "", resp.content.strip()).strip().rstrip("```").strip()
        data = json.loads(raw)
        collected["recommendation_type"] = data.get("recommendation_type", "gp")
        collected["needs_surgery"] = data.get("needs_surgery", False)
        collected["specialization"] = data.get("specialization", "General Physician")
        collected["triage_reason"] = data.get("triage_reason", "")
        # Sync intent with triage
        if collected["recommendation_type"] == "hospital":
            collected["intent"] = "hospital"
        else:
            collected["intent"] = "doctor"
    except Exception:
        collected["recommendation_type"] = "gp"
        collected["needs_surgery"] = False
        collected["specialization"] = "General Physician"

    return collected


# ── Prior consultation questions ──────────────────────────────────────────────

def _ask_prior_consultation(collected: dict, message_history: list[dict]) -> tuple[str, list]:
    """LLM generates a contextual question about prior doctor visits."""
    symptom = collected.get("symptom", "this condition")
    system = SystemMessage(content=(
        "You are a warm healthcare assistant. Ask the patient if they have already "
        "seen a doctor or tried any treatment for their condition. "
        "Keep it conversational, empathetic, 1-2 sentences. "
        "Reference their specific symptom/condition naturally."
    ))
    human = HumanMessage(content=f"Patient's condition: {symptom}")
    try:
        resp = _llm(temperature=0.4).invoke([system, human])
        reply = resp.content.strip()
    except Exception:
        reply = f"Before I suggest the best next step for {symptom} — have you already consulted a doctor or tried any treatment for this?"

    opts = [
        "Yes, I saw a doctor before",
        "Yes, I tried home remedies / self-medicated",
        "No, first time seeking help",
    ]
    return reply, opts


def _ask_prev_advice(collected: dict, message_history: list[dict]) -> str:
    symptom = collected.get("symptom", "this")
    system = SystemMessage(content=(
        "You are a warm healthcare assistant. Ask the patient what the previous doctor "
        "told them — their diagnosis and what treatment was recommended. "
        "Be empathetic and explain why this helps you give a better recommendation. "
        "Keep it to 2-3 sentences."
    ))
    human = HumanMessage(content=f"Symptom: {symptom}")
    try:
        resp = _llm(temperature=0.4).invoke([system, human])
        return resp.content.strip()
    except Exception:
        return ("That's helpful to know. Could you share what the doctor diagnosed or advised? "
                "Even rough details like 'they said it might be X and prescribed Y' would help me suggest better options.")


def _ask_advice_helped(collected: dict, message_history: list[dict]) -> tuple[str, list]:
    advice = collected.get("prev_advice_text", "that treatment")
    system = SystemMessage(content=(
        "You are a warm healthcare assistant. Ask the patient whether following the previous "
        "doctor's advice helped their condition. Be brief and empathetic. 1-2 sentences."
    ))
    human = HumanMessage(content=f"Previous advice: {advice}")
    try:
        resp = _llm(temperature=0.4).invoke([system, human])
        reply = resp.content.strip()
    except Exception:
        reply = "Did following that advice help your condition at all?"

    opts = [
        "Yes, it helped significantly",
        "Partially — some improvement",
        "No improvement at all",
        "I didn't follow the advice",
    ]
    return reply, opts


# ── Missing fields calculator ─────────────────────────────────────────────────

def _compute_missing(collected: dict, rec_type: Optional[str]) -> list[str]:
    """
    Returns ordered list of still-missing required fields based on recommendation type.
    """
    base = ["symptom", "urgency", "city", "budget", "has_insurance"]

    if rec_type == "hospital":
        # For hospital path we also need procedure details for cost engine
        extended = base + ["procedure", "age", "preference"]
    else:
        extended = base + ["preference"]

    return [f for f in extended if f not in collected]


# ── Dynamic next-question generator ──────────────────────────────────────────

_NEXT_Q_SYSTEM = """You are HealthClear, a conversational healthcare assistant.
You are collecting information from a patient to recommend the right doctor or hospital.
Ask for ONE missing piece of information in a natural, conversational way.
- Never ask multiple questions at once.
- Reference what you already know about the patient to make it feel personal.
- If asking about budget, give realistic Indian rupee ranges as examples.
- If asking about city, mention that you'll search for doctors/hospitals there.
- If asking about procedure (surgery/treatment name), explain you need it to estimate costs.
- Keep each question to 1-3 sentences.
- End with a question mark.

Also return EXACTLY 3 short suggested option buttons that would answer your question. If gathering a purely free-text field like `prev_advice_text` where buttons don't make sense, return 0 options.
Return JSON:
{
  "question": "<your question text>",
  "next_field": "<field key you're asking about>",
  "options": ["option1", "option2", ...]
}"""


def _ask_next_question(
    missing: list[str],
    collected: dict,
    knowledge_context: str,
    patient_context: str,
    message_history: list[dict],
    user_message: str,
) -> tuple[str, str, list]:
    """
    Ask the LLM to generate the next contextual question for the first missing field.
    Returns (question_text, next_field_key, options_list).
    """
    next_field = missing[0]
    history_text = _format_history(message_history[-4:])

    # Build a summary of what's been collected for LLM context
    collected_summary = _human_readable_collected(collected)

    system = SystemMessage(content=_NEXT_Q_SYSTEM)
    human = HumanMessage(content=(
        f"Patient context:\n{patient_context}\n\n"
        f"What we know so far:\n{collected_summary}\n\n"
        f"Recent conversation:\n{history_text}\n\n"
        f"Still need: {missing}\n"
        f"Ask about: '{next_field}'\n\n"
        f"Available in DB:\n{_field_db_hints(next_field, knowledge_context)}\n\n"
        "Return JSON only."
    ))

    try:
        resp = _llm(temperature=0.45).invoke([system, human])
        raw = re.sub(r"```(?:json)?", "", resp.content.strip()).strip().rstrip("```").strip()
        data = json.loads(raw)
        return data.get("question", ""), data.get("next_field", next_field), data.get("options", [])
    except Exception:
        # Fallback questions per field
        fallbacks = {
            "symptom": ("What symptom or health issue brought you here today?",
                         ["Chest pain", "Fever", "Joint pain", "Digestive issues", "Other"]),
            "urgency": ("How long have you been experiencing this, and how severe does it feel?",
                         ["Started today — very urgent", "Few days", "Weeks/months", "Chronic"]),
            "city": ("Which city are you in? I'll search for hospitals and doctors there.", []),
            "budget": ("What's your approximate budget for this treatment?",
                        ["Under ₹1,000", "₹1K–₹10K", "₹10K–₹50K", "₹50K–₹2L", "₹2L+ / Insurance"]),
            "has_insurance": ("Do you have health insurance?",
                               ["Yes — government scheme", "Yes — private insurance", "No insurance"]),
            "procedure": ("Do you know the name of the procedure or surgery you need?", []),
            "age": ("Could you share your age? It helps me factor in risk and costs.", []),
            "preference": ("What matters most to you in choosing a hospital or doctor?",
                            ["Most experienced", "Lowest cost", "Highest success rate", "No preference"]),
        }
        q, opts = fallbacks.get(next_field, (f"Could you tell me about your {next_field}?", []))
        return q, next_field, opts


def _field_db_hints(field: str, knowledge_context: str) -> str:
    """Extract relevant DB options for a given field to help LLM craft accurate options."""
    if field == "city":
        cities = re.findall(r"\((\w[\w\s]+)\) —", knowledge_context)
        return "Cities available: " + ", ".join(set(cities)) if cities else ""
    if field == "procedure":
        procs = re.findall(r"  • (.+?) — base", knowledge_context)
        return "Procedures in DB: " + ", ".join(procs[:10]) if procs else ""
    return ""


# ── General Q&A answerer ──────────────────────────────────────────────────────

def _answer_general_question(
    user_message: str,
    collected: dict,
    knowledge_context: str,
    patient_context: str,
    message_history: list[dict],
) -> str:
    """
    Answer a general health / medication / disease question using RAG
    (patient profile + DB knowledge as context).
    """
    history_msgs = [
        (HumanMessage if m["role"] == "user" else AIMessage)(content=m["content"])
        for m in message_history[-6:]
    ]

    system = SystemMessage(content=f"""You are HealthClear, a knowledgeable and empathetic healthcare assistant in India.
Answer the patient's health question using their profile and the hospital/doctor database as context.

{patient_context}

{knowledge_context}

Guidelines:
- Be warm, clear, and non-alarmist.
- Always recommend consulting a real doctor for diagnosis/treatment decisions.
- If the patient's profile reveals relevant conditions or medications, factor those in.
- Keep answers concise (2-3 sentences max).
- Never diagnose. Explain possibilities and recommend professional consultation.
- If a doctor or hospital in the DB is clearly relevant, mention them naturally.""")

    human = HumanMessage(content=user_message)
    try:
        resp = _llm(temperature=0.4).invoke([system] + history_msgs + [human])
        return resp.content.strip()
    except Exception:
        return ("That's a great question. Based on what you've described, I'd recommend consulting "
                "a doctor who can examine you properly. Would you like me to find a suitable specialist near you?")


# ── Completion message ────────────────────────────────────────────────────────

def _generate_completion_message(collected: dict, knowledge_context: str, patient_context: str) -> str:
    """
    Generate a brief message confirming all info has been collected and results are being prepared.
    """
    rec_type = collected.get("recommendation_type", "gp")
    symptom = collected.get("symptom", "your condition")
    city = collected.get("city", "your city")

    if rec_type == "hospital":
        action = f"finding the best hospitals in {city} for your treatment"
    else:
        spec = collected.get("specialization", "specialist")
        action = f"finding the best {spec} doctors in {city} for you"

    system = SystemMessage(content=(
        "You are HealthClear. Write a strict 1-sentence message (maximum 15 words) telling the patient "
        "you have everything you need and are now preparing their personalized recommendation. "
        "Mention the specific condition/symptom and city if possible. "
        f"Action being taken: {action}."
    ))
    human = HumanMessage(content=f"Symptom: {symptom}, City: {city}, Type: {rec_type}")
    try:
        resp = _llm(temperature=0.4).invoke([system, human])
        return resp.content.strip()
    except Exception:
        return f"Perfect, I have everything I need! Let me find the best options in {city} for {symptom} right away. 🔍"


# ── Supabase retry helper ─────────────────────────────────────────────────────

import time as _time

def _supabase_query_with_retry(query_fn, max_retries: int = 3, delay: float = 1.0):
    """
    Execute a Supabase query with retry logic to handle transient
    Cloudflare 1101 / Worker exceptions from Supabase's PostgREST.
    
    query_fn: a callable that returns a Supabase query result (call .execute() inside)
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            result = query_fn()
            return result.data or []
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                _time.sleep(delay * (attempt + 1))  # progressive backoff
    raise last_error


# ── Doctor recommendation builder (for non-hospital path) ─────────────────────

def build_doctor_recommendation(collected: dict, client) -> dict:
    """
    Called by main.py when rec_type is "specialist" or "gp".
    Returns a structured doctor recommendation dict instead of hospital cost engine output.
    """
    city = collected.get("city", "")
    specialization = collected.get("specialization", "General Physician")
    budget = collected.get("budget", "")
    prev_advice_helped = collected.get("prev_advice_helped", "")
    symptom = collected.get("symptom", "")

    # Fetch matching doctors (with retry for transient Supabase errors)
    doctors = []
    
    # 1. Try exact city + specialty match
    if city and specialization:
        doctors = _supabase_query_with_retry(
            lambda: client.table("doctor")
            .select("*")
            .ilike("city", f"%{city}%")
            .ilike("specialization", f"%{specialization}%")
            .execute()
        )

    # 2. Fallback: try GP in that city
    if not doctors and city:
        doctors = _supabase_query_with_retry(
            lambda: client.table("doctor")
            .select("*")
            .ilike("city", f"%{city}%")
            .ilike("specialization", "%General%")
            .execute()
        )
        
    # 3. Last resort in city: ANY doctor in that city
    if not doctors and city:
        doctors = _supabase_query_with_retry(
            lambda: client.table("doctor")
            .select("*")
            .ilike("city", f"%{city}%")
            .execute()
        )

    # 4. Global fallback: Try exact specialty in ANY city
    if not doctors and specialization:
        doctors = _supabase_query_with_retry(
            lambda: client.table("doctor")
            .select("*")
            .ilike("specialization", f"%{specialization}%")
            .execute()
        )

    # 5. Ultimate fallback: Any doctor in ANY city
    if not doctors:
        doctors = _supabase_query_with_retry(
            lambda: client.table("doctor")
            .select("*")
            .limit(5)
            .execute()
        )

    # Sort: if previous advice didn't help, prefer most experienced
    def _parse_exp(exp_str: str) -> int:
        try:
            return int(re.search(r"\d+", str(exp_str)).group())
        except Exception:
            return 0

    if prev_advice_helped in ("no", "partial"):
        doctors = sorted(doctors, key=lambda d: _parse_exp(d.get("experience", "0")), reverse=True)

    # Budget filter (don't exclude all if none match)
    if budget and budget != "above_200000":
        budget_map = {
            "under_1000": 1000, "1000_10000": 10000,
            "10000_50000": 50000, "50000_200000": 200000,
        }
        max_fee = budget_map.get(budget, float("inf"))
        budget_filtered = [
            d for d in doctors
            if _parse_fee(d.get("consultation_fee", "0")) <= max_fee
        ]
        if budget_filtered:
            doctors = budget_filtered

    top_doctors = doctors[:3]

    # Use LLM to generate personalized explanation
    explanation = _generate_doctor_explanation(top_doctors, collected)

    return {
        "type": "doctor_recommendation",
        "specialization": specialization,
        "triage_reason": collected.get("triage_reason", ""),
        "doctors": top_doctors,
        "ai_explanation": explanation,
        "prior_consultation_note": _prior_consult_note(collected),
    }


def _parse_fee(fee_str: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", str(fee_str)))
    except Exception:
        return 0.0


def _prior_consult_note(collected: dict) -> str:
    if collected.get("prev_consultation") == "yes_doctor":
        helped = collected.get("prev_advice_helped", "")
        advice = collected.get("prev_advice_text", "")
        if helped in ("no", "partial"):
            return (f"Since a previous consultation ({advice[:80]}...) didn't fully help, "
                    "I've prioritized more experienced doctors who may offer a fresh perspective.")
        elif helped == "yes":
            return "Since previous treatment helped, I'm recommending doctors in the same specialization for follow-up care."
    elif collected.get("prev_consultation") == "yes_self":
        return "You mentioned trying home remedies — it's a good time to get a professional opinion."
    return ""


def _generate_doctor_explanation(doctors: list, collected: dict) -> str:
    if not doctors:
        return "No doctors found matching your criteria in this city. Consider expanding to nearby cities."

    symptom = collected.get("symptom", "your condition")
    doctor_list = "\n".join(
        f"  • Dr. {d['doctor_name']} ({d.get('specialization','?')}, {d.get('experience','?')}) "
        f"— {d.get('clinic','?')}, fee {d.get('consultation_fee','?')}"
        for d in doctors
    )

    system = SystemMessage(content=(
        "You are HealthClear. Write a brief, warm explanation (3-4 sentences) of why these doctors "
        "are good choices for the patient's condition. Mention their experience and how it relates "
        "to the symptom. If the patient had a bad prior consultation, acknowledge that and explain "
        "how these doctors can offer a second opinion. Be encouraging and professional."
    ))
    human = HumanMessage(content=(
        f"Patient symptom: {symptom}\n"
        f"Prior consultation helped: {collected.get('prev_advice_helped', 'N/A')}\n"
        f"Doctors:\n{doctor_list}"
    ))
    try:
        resp = _llm(temperature=0.4).invoke([system, human])
        return resp.content.strip()
    except Exception:
        return f"Based on your symptoms, these {collected.get('specialization','specialist')} doctors in {collected.get('city','')} are well-suited to help you."


# ── Utilities ─────────────────────────────────────────────────────────────────

def _format_history(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        role = "Patient" if m.get("role") == "user" else "HealthClear"
        lines.append(f"{role}: {m.get('content', '')}")
    return "\n".join(lines) if lines else "No prior conversation."


def _human_readable_collected(collected: dict) -> str:
    labels = {
        "symptom": "Symptom/condition",
        "urgency": "Urgency",
        "city": "City",
        "budget": "Budget",
        "has_insurance": "Has insurance",
        "insurance_type": "Insurance type",
        "procedure": "Procedure",
        "age": "Age",
        "comorbidities": "Other conditions",
        "smoking": "Smoker",
        "preference": "Preference",
        "prev_consultation": "Prior consultation",
        "prev_advice_text": "Previous doctor's advice",
        "prev_advice_helped": "Did prior advice help",
        "recommendation_type": "Care pathway",
        "specialization": "Specialization needed",
    }
    lines = []
    for k, label in labels.items():
        if k in collected:
            lines.append(f"  {label}: {collected[k]}")
    return "\n".join(lines) if lines else "Nothing collected yet."


# ── Option generator for frontend buttons ─────────────────────────────────────

def generate_field_options(field: Optional[str], knowledge_context: str, collected: dict) -> list:
    """
    Called by main.py to populate frontend option buttons for the next field.
    Returns a list of strings.
    """
    if not field:
        return []

    static_opts = {
        "urgency": ["Just started — urgent", "A few days", "Several weeks", "Months / chronic"],
        "has_insurance": ["Yes — government (Ayushman Bharat)", "Yes — private insurance", "No insurance"],
        "budget": ["Under ₹1,000", "₹1,000–₹10,000", "₹10,000–₹50,000", "₹50,000–₹2,00,000", "₹2L+ or fully insured"],
        "prev_consultation": ["Yes, saw a doctor", "Yes, tried home remedies", "No — first time"],
        "prev_advice_helped": ["Yes, it helped", "Partially helped", "No improvement", "Didn't follow it"],
        "preference": ["Most experienced doctor", "Lowest cost", "Best success rate", "Closest to me", "No preference"],
        "smoking": ["Yes", "No", "Former smoker"],
    }

    if field in static_opts:
        return static_opts[field]

    if field == "city":
        cities = re.findall(r"\((\w[\w ]+)\) —", knowledge_context)
        return sorted(set(cities))[:8] if cities else []

    if field == "procedure":
        procs = re.findall(r"  • (.+?) — base", knowledge_context)
        return procs[:8] if procs else []

    return []
