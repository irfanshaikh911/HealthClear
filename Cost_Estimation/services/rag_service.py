"""
RAG Service
-----------
Retrieves all relevant context from Supabase and uses LangChain + Groq
to power the /rag-chat endpoint.

Key responsibilities:
  1. Build a plain-text "knowledge context" from Supabase data (no embeddings needed —
     Groq's 128k context window is large enough to include all hospitals + procedures).
  2. Maintain a running set of "collected fields" in session state.
  3. Use LLM to intelligently extract patient information from free-form messages,
     determine what is still missing, and generate the next question naturally.
  4. When all required fields are collected, hand off to the cost engine.
"""
import json
import os
import re
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from supabase import Client

# Fields that must be collected before we can run the cost engine
REQUIRED_FIELDS = [
    "selected_procedure",
    "age",
    "gender",
    "city",
    "comorbidities",   # list[str]
    "smoking",          # bool
    "insurance_status",
    "budget_limit",     # float
    "room_preference",
]


# ── Option maps (defined early so _sanitize_extracted can reference them) ─────

# Static suggested options per field — shown as buttons in the UI
_STATIC_OPTIONS: dict[str, list[str]] = {
    "gender": ["Male", "Female"],
    "smoking": ["No, I don't smoke", "Yes, I smoke"],
    "insurance_status": ["Private Insurance", "Government / Ayushman Bharat", "No Insurance"],
    "room_preference": ["General Ward", "Semi-Private Room", "Private Room"],
    "budget_limit": [
        "Under ₹50,000",
        "₹50,000 – ₹1,00,000",
        "₹1,00,000 – ₹2,00,000",
        "₹2,00,000 – ₹5,00,000",
        "Above ₹5,00,000",
    ],
    "age": ["Under 18", "18–30", "31–45", "46–60", "61–75", "Above 75"],
}

# Budget option → float
BUDGET_OPTION_MAP: dict[str, float] = {
    "under ₹50,000": 40000.0,
    "₹50,000 – ₹1,00,000": 75000.0,
    "₹1,00,000 – ₹2,00,000": 150000.0,
    "₹2,00,000 – ₹5,00,000": 350000.0,
    "above ₹5,00,000": 600000.0,
}

# Age range → midpoint integer
AGE_RANGE_MAP: dict[str, int] = {
    "under 18": 14, "18–30": 24, "31–45": 38,
    "46–60": 53, "61–75": 68, "above 75": 78,
    "18-30": 24, "31-45": 38, "46-60": 53, "61-75": 68,
}

# Smoking option → bool
SMOKING_OPTION_MAP: dict[str, bool] = {
    "no, i don't smoke": False,
    "yes, i smoke": True,
}

# Insurance option → canonical string
INSURANCE_OPTION_MAP: dict[str, str] = {
    "private insurance": "private",
    "government / ayushman bharat": "government",
    "no insurance": "none",
}

# Room option → canonical string
ROOM_OPTION_MAP: dict[str, str] = {
    "general ward": "general",
    "semi-private room": "semi-private",
    "private room": "private",
}


def _get_llm(temperature: float = 0.3) -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        temperature=temperature,
    )


def _parse_json_safe(text: str) -> Optional[dict]:
    """
    Robustly parse JSON from LLM output — handles markdown fences,
    trailing text, and other noise.
    """
    # Strip markdown fences (```json ... ```)
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── Supabase context builder ──────────────────────────────────────────────────

def build_knowledge_context(client: Client) -> str:
    """
    Fetch all hospitals, procedures, and risk conditions from Supabase and
    format them as a plain-text knowledge block for the LLM system prompt.
    This is the RAG 'retrieval' step — no vector DB needed at this scale.
    """
    lines = []

    # Hospitals
    hosp_rows = client.table("hospitals").select("*").execute().data or []
    lines.append("== HOSPITALS ==")
    for h in hosp_rows:
        try:
            lines.append(
                f"  [{h['city'].title()}] {h['name']}: base_cost=₹{float(h['base_cost']):,.0f}, "
                f"success_rate={float(h['success_rate'])*100:.0f}%, "
                f"complication_rate={float(h['base_complication_rate'])*100:.1f}%, "
                f"recovery={h['average_recovery_days']} days, "
                f"room=₹{h['room_cost_per_day']}/day"
            )
        except Exception:
            pass

    # Procedures
    proc_rows = client.table("procedures").select("*").execute().data or []
    lines.append("\n== PROCEDURES ==")
    for p in proc_rows:
        try:
            lines.append(
                f"  {p['name']}: base_cost=₹{float(p['base_cost']):,.0f}, "
                f"avg_stay={p['average_length_of_stay']} days"
            )
        except Exception:
            pass

    # Risk conditions
    risk_rows = client.table("risk_conditions").select("*").execute().data or []
    lines.append("\n== RISK CONDITIONS (cost multipliers) ==")
    for r in risk_rows:
        try:
            lines.append(
                f"  {r['name']}: cost_multiplier=+{float(r['cost_multiplier'])*100:.0f}%"
            )
        except Exception:
            pass

    return "\n".join(lines)


def build_patient_context(client: Client, patient_id: int) -> str:
    """
    Fetch a specific patient's profile + active medical history from Supabase
    and format it as a text block for the LLM.
    """
    patient_res = (
        client.table("patients").select("*").eq("patient_id", patient_id).execute()
    )
    if not patient_res.data:
        return ""

    p = patient_res.data[0]
    history_res = (
        client.table("medical_history")
        .select("*")
        .eq("patient_id", patient_id)
        .in_("status", ["Ongoing", "Chronic"])
        .execute()
    )
    history = history_res.data or []
    conditions = ", ".join(h["condition_name"] for h in history) or "none"

    return (
        f"== PATIENT PROFILE ==\n"
        f"  Name: {p.get('full_name', 'Unknown')}\n"
        f"  DOB: {p.get('date_of_birth', 'Unknown')}\n"
        f"  Gender: {p.get('gender', 'Unknown')}\n"
        f"  Active conditions: {conditions}\n"
        f"  Medications: {p.get('medications', 'none')}\n"
        f"  Insurance: {p.get('insurance_type', 'Unknown')}\n"
    )


# ── Core RAG turn handler ─────────────────────────────────────────────────────

def process_rag_turn(
    user_message: str,
    collected: dict,
    knowledge_context: str,
    patient_context: str,
    message_history: list,
) -> dict:
    """
    One conversational turn of the RAG chatbot.

    Returns:
      {
        "reply": str,           # assistant message to send back
        "collected": dict,      # updated collected fields (may include new ones)
        "missing": list[str],   # fields still needed
        "is_complete": bool,    # True when all REQUIRED_FIELDS are collected
      }
    """
    llm = _get_llm()

    system_prompt = f"""You are a smart, compassionate healthcare cost estimation assistant in India.
Your job is to have a natural conversation with the patient to gather all necessary information,
then provide personalized hospital cost estimates.

You have access to the following real hospital and procedure data from our database:
{knowledge_context}

{("Patient profile from records:\n" + patient_context) if patient_context else ""}

REQUIRED INFORMATION to collect (in any order, skip already collected):
- selected_procedure: The medical procedure/treatment needed (exact name from the list above)
- age: Patient's age as an integer
- gender: "male" or "female"
- city: City where treatment is needed (from the hospital list above)
- comorbidities: List e.g. ["diabetes", "hypertension"] or [] if none
- smoking: true or false
- insurance_status: "private", "government", or "none"
- budget_limit: Budget in INR as a number (e.g. 150000.0)
- room_preference: "general", "semi-private", or "private"

ALREADY COLLECTED (DO NOT ASK AGAIN):
{json.dumps(collected, indent=2, default=str)}

RULES:
1. Extract ANY information provided by the patient in their current message.
2. NEVER ask for a field that is already in ALREADY COLLECTED.
3. Ask ONE question at a time for the most important missing field.
4. If the patient mentions a condition like "sugar" interpret it as "diabetes". Be smart.
5. Keep responses warm, natural, and brief (1-2 sentences + the question).
6. When ALL required fields are collected (none missing), set "ready": true.
7. Always respond ONLY with valid JSON. No markdown, no extra text.

RESPONSE FORMAT (strict JSON):
{{
  "reply": "<your message to the patient, including the next question>",
  "extracted": {{<only newly extracted key-value pairs from THIS message>}},
  "ready": false
}}

TYPE RULES for extracted values:
- age: integer
- smoking: boolean (true/false)  
- budget_limit: float number
- comorbidities: list of lowercase strings
- all others: lowercase string
"""

    # Build proper message history for LLM (using correct AIMessage type)
    messages = [SystemMessage(content=system_prompt)]
    for turn in message_history[-8:]:  # last 8 turns for context
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))  # proper AIMessage

    messages.append(HumanMessage(content=user_message))

    # ── BUTTON-CLICK SHORTCUT ────────────────────────────────────────────────
    # If the user's message exactly matches a known option for the next missing
    # field, store it directly without calling the LLM (faster, more reliable).
    missing_now = [f for f in REQUIRED_FIELDS if f not in collected]
    if missing_now:
        next_f = missing_now[0]
        all_options = generate_field_options(next_f, knowledge_context, collected)
        # Case-insensitive match against options
        match_val = next((o for o in all_options if o.lower() == user_message.strip().lower()), None)
        # Also accept if message matches any option substring (e.g. procedure name)
        if not match_val and next_f == "selected_procedure":
            match_val = next((o for o in all_options if o.lower() == user_message.strip().lower()), None)
        if match_val:
            # Directly store the matched option value via sanitize
            updated = dict(collected)
            updated.update(_sanitize_extracted({next_f: match_val}))
            new_missing = [f for f in REQUIRED_FIELDS if f not in updated]
            # Ask the LLM only to generate the next question (cheaply)
            next_question_key = new_missing[0] if new_missing else None
            fallback_questions = {
                "selected_procedure": "Great! Which city would you like to get treatment in?",
                "age": "How old are you?",
                "gender": "Are you male or female?",
                "city": "Which city would you like treatment in?",
                "comorbidities": "Do you have any health conditions like diabetes or hypertension? (You can pick from the options or type freely)",
                "smoking": "Do you currently smoke?",
                "insurance_status": "What type of insurance do you have?",
                "budget_limit": "What is your approximate budget for this treatment?",
                "room_preference": "Do you prefer a general ward, semi-private, or private room?",
            }
            is_complete_now = len(new_missing) == 0
            if is_complete_now:
                reply_text = "All information collected! Running your personalized cost estimate..."
            else:
                reply_text = fallback_questions.get(next_question_key or "", "Thank you! What else can you tell me?")
            return {
                "reply": reply_text,
                "collected": updated,
                "missing": new_missing,
                "is_complete": is_complete_now,
                "next_field": next_question_key,
            }
    # ── END BUTTON-CLICK SHORTCUT ────────────────────────────────────────────

    try:
        response = llm.invoke(messages)
        raw_content = response.content.strip()

        parsed = _parse_json_safe(raw_content)
        if not parsed:
            raise ValueError(f"Failed to parse JSON from LLM response: {raw_content[:200]}")

        reply: str = parsed.get("reply", "Could you tell me more?")
        extracted: dict = parsed.get("extracted", {})
        ready_signal: bool = parsed.get("ready", False)

        # Merge extracted into collected (validate and cast types)
        updated = dict(collected)
        updated.update(_sanitize_extracted(extracted))

        missing = [f for f in REQUIRED_FIELDS if f not in updated]
        # Complete if LLM said ready AND all fields actually present
        is_complete = (ready_signal or len(missing) == 0) and len([f for f in REQUIRED_FIELDS if f not in updated]) == 0

        return {
            "reply": reply.strip(),
            "collected": updated,
            "missing": missing,
            "is_complete": is_complete,
            "next_field": missing[0] if missing else None,
        }

    except Exception as e:
        # Graceful fallback — ask for the next missing field explicitly
        missing = [f for f in REQUIRED_FIELDS if f not in collected]
        next_field = missing[0] if missing else None
        fallback_questions = {
            "selected_procedure": "What medical procedure or treatment are you looking for?",
            "age": "How old are you?",
            "gender": "What is your gender?",
            "city": "Which city do you want treatment in?",
            "comorbidities": "Do you have any health conditions like diabetes or hypertension?",
            "smoking": "Do you currently smoke?",
            "insurance_status": "Do you have private insurance, government insurance, or none?",
            "budget_limit": "What is your approximate budget for this treatment (in ₹)?",
            "room_preference": "Do you prefer a general, semi-private, or private hospital room?",
        }
        reply = fallback_questions.get(next_field, "Could you tell me more about your requirements?")
        return {
            "reply": reply,
            "collected": collected,
            "missing": missing,
            "is_complete": False,
            "next_field": next_field,
        }


def _sanitize_extracted(extracted: dict) -> dict:
    """
    Clean and type-cast LLM-extracted fields to correct Python types.
    Also handles friendly option-button labels (e.g. 'Private Insurance' -> 'private').
    """
    out = {}
    for k, v in extracted.items():
        if k not in REQUIRED_FIELDS:
            continue
        if v is None:
            continue
        try:
            val_str = str(v).strip()
            val_lower = val_str.lower()

            if k == "age":
                if val_lower in AGE_RANGE_MAP:
                    out[k] = AGE_RANGE_MAP[val_lower]
                else:
                    out[k] = int(float(val_str.replace(",", "")))

            elif k == "smoking":
                if isinstance(v, bool):
                    out[k] = v
                elif val_lower in SMOKING_OPTION_MAP:
                    out[k] = SMOKING_OPTION_MAP[val_lower]
                else:
                    out[k] = val_lower in ("true", "yes", "1", "smoker", "i smoke")

            elif k == "budget_limit":
                if val_lower in BUDGET_OPTION_MAP:
                    out[k] = BUDGET_OPTION_MAP[val_lower]
                else:
                    cleaned = val_str.replace(",", "").replace("₹", "").replace(" ", "")
                    if "lakh" in cleaned.lower():
                        num = cleaned.lower().replace("lakh", "").strip()
                        out[k] = float(num) * 100000
                    else:
                        out[k] = float(cleaned)

            elif k == "insurance_status":
                if val_lower in INSURANCE_OPTION_MAP:
                    out[k] = INSURANCE_OPTION_MAP[val_lower]
                elif "private" in val_lower:
                    out[k] = "private"
                elif "gov" in val_lower or "ayushman" in val_lower:
                    out[k] = "government"
                else:
                    out[k] = "none"

            elif k == "room_preference":
                if val_lower in ROOM_OPTION_MAP:
                    out[k] = ROOM_OPTION_MAP[val_lower]
                elif "private" in val_lower:
                    out[k] = "private"
                elif "semi" in val_lower:
                    out[k] = "semi-private"
                else:
                    out[k] = "general"

            elif k == "comorbidities":
                if isinstance(v, list):
                    out[k] = [str(c).lower().strip() for c in v if c and str(c).lower().strip() not in ("none", "")]
                elif val_lower in ("none", "no", "nil", "", "nothing", "n/a"):
                    out[k] = []
                else:
                    parts = [p.strip().lower() for p in val_str.replace(",", "|").split("|") if p.strip()]
                    out[k] = [p for p in parts if p not in ("none", "no", "nil", "nothing")]

            else:
                out[k] = val_lower

        except Exception:
            pass
    return out


# ── Opening message generator ─────────────────────────────────────────────────


def generate_rag_opening(
    knowledge_context: str,
    patient_context: str,
    prefilled: dict,
) -> str:
    """
    Generate a personalized opening message for the RAG chatbot.
    Uses patient context if available, otherwise generic greeting.
    """
    llm = _get_llm(temperature=0.5)
    already = list(prefilled.keys())
    system_msg = SystemMessage(content=(
        "You are a warm, professional healthcare cost assistant in India. "
        "Write a brief (2-3 sentence) opening greeting for a patient. "
        "If patient profile is provided, greet them by first name and acknowledge their records. "
        "Tell them they can just chat naturally — no forms to fill. "
        "If some info is already known from records, mention it's already pre-filled. "
        "Be warm, short, and inviting. End with a question about what they need help with."
    ))
    human_msg = HumanMessage(content=(
        f"Patient context:\n{patient_context or 'Anonymous patient (no records)'}\n\n"
        f"Fields already known from records: {already or 'None'}\n\n"
        f"Write the opening greeting now (plain text, no JSON)."
    ))
    try:
        response = llm.invoke([system_msg, human_msg])
        return response.content.strip()
    except Exception:
        return (
            "👋 Hi! I'm your healthcare cost assistant. "
            "Just tell me what treatment you need, your city, and a bit about your health — "
            "I'll find the best hospitals and give you a personalized cost estimate!"
        )


# ── Smart field options generator ─────────────────────────────────────────────

def generate_field_options(
    field: str,
    knowledge_context: str,
    collected: dict,
) -> list[str]:
    """
    Return a list of suggested answer options for the given field.
    - Fixed-choice and numeric fields: static options from _STATIC_OPTIONS.
    - Procedure / city: parsed from the knowledge_context string (DB data).
    - Comorbidities: LLM-generated based on procedure context.
    """
    if field in _STATIC_OPTIONS:
        return _STATIC_OPTIONS[field]

    if field == "selected_procedure":
        procs = []
        in_proc_section = False
        for line in knowledge_context.splitlines():
            if line.strip().startswith("== PROCEDURES"):
                in_proc_section = True
                continue
            if in_proc_section:
                if line.strip().startswith("=="):
                    break
                m = re.match(r"\s+(.+?):\s+base_cost", line)
                if m:
                    procs.append(m.group(1).strip())
        return procs if procs else ["Knee Replacement", "Angioplasty", "Cataract Surgery", "Other"]

    if field == "city":
        cities: list[str] = []
        seen: set[str] = set()
        for line in knowledge_context.splitlines():
            m = re.match(r"\s+\[(.+?)\]", line)
            if m:
                c = m.group(1).strip().title()
                if c not in seen:
                    seen.add(c)
                    cities.append(c)
        return sorted(cities) if cities else ["Pune", "Mumbai", "Bangalore"]

    if field == "comorbidities":
        procedure = collected.get("selected_procedure", "")
        try:
            llm = _get_llm(temperature=0.3)
            sys_msg = SystemMessage(content=(
                "You are a medical assistant. List the most common comorbidities "
                "for a patient needing a specific procedure. "
                "Respond ONLY with a JSON array of strings. No extra text."
            ))
            hum_msg = HumanMessage(content=(
                f"Procedure: {procedure or 'general surgery'}\n"
                f"Give 5-6 common comorbidities. Always include 'None' as the last item.\n"
                f'Example: ["Diabetes", "Hypertension", "Obesity", "None"]'
            ))
            resp = llm.invoke([sys_msg, hum_msg])
            raw = _parse_json_safe(resp.content)
            if isinstance(raw, list):
                return [str(x) for x in raw]
        except Exception:
            pass
        return ["Diabetes", "Hypertension", "Obesity", "Heart Disease", "Asthma", "None"]

    return []

