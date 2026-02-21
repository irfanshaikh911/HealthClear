"""
Patient Service — fetches patient profile from Supabase,
maps conditions to risk factors via Groq, generates personalized opening.
"""
import json
from datetime import date
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from supabase import Client

from app.core.config import settings

# Known risk condition names (must match risk_conditions table)
KNOWN_RISK_CONDITIONS = ["diabetes", "hypertension", "smoking"]


def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    )


def _calculate_age(dob_str: str) -> int:
    """Calculate age from date_of_birth string (YYYY-MM-DD)."""
    try:
        dob = date.fromisoformat(dob_str)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 30


def fetch_patient_context(client: Client, patient_id: int) -> Optional[dict]:
    """Returns patient profile + active medical history, or None."""
    patient_res = (
        client.table("patients")
        .select("*")
        .eq("patient_id", patient_id)
        .execute()
    )
    if not patient_res.data:
        return None

    patient = patient_res.data[0]
    history_res = (
        client.table("medical_history")
        .select("*")
        .eq("patient_id", patient_id)
        .in_("status", ["Ongoing", "Chronic"])
        .execute()
    )

    return {
        "patient": patient,
        "medical_history": history_res.data or [],
    }


def map_conditions_to_risk(conditions: list[str]) -> dict:
    """Uses Groq to map arbitrary condition names to known risk factors."""
    if not conditions:
        return {"mapped": [], "unmapped": []}

    llm = _get_llm()
    system_msg = SystemMessage(content=(
        "You are a medical data assistant. Map patient conditions to risk factors. "
        "Always respond with valid JSON only, no extra text."
    ))
    human_msg = HumanMessage(content=(
        f"Map these patient conditions: {conditions}\n"
        f"to these known risk factors: {KNOWN_RISK_CONDITIONS}\n"
        f"A condition maps only if it clearly matches (e.g. 'Type 2 Diabetes' → 'diabetes').\n"
        f'Return ONLY JSON: {{"mapped": ["..."], "unmapped": ["..."]}}'
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
        return {"mapped": [], "unmapped": conditions}


def generate_opening_summary(patient_ctx: dict, prefilled_fields: list[str]) -> str:
    """Calls Groq to generate a warm, personalized opening message."""
    patient = patient_ctx["patient"]
    history = patient_ctx["medical_history"]
    name = patient.get("full_name", "there").split()[0]
    dob = patient.get("date_of_birth", "")
    age = _calculate_age(dob) if dob else "unknown"
    gender = patient.get("gender", "")
    conditions = [h["condition_name"] for h in history]
    conditions_str = ", ".join(conditions) if conditions else "no recorded conditions"

    llm = _get_llm()
    system_msg = SystemMessage(content=(
        "You are a compassionate healthcare assistant in India. "
        "Write a brief, warm, 2-3 sentence opening message to a patient. "
        "Mention their name, what you see in their records, and that you "
        "need a few more details to estimate treatment costs. "
        "Keep it concise and professional."
    ))
    human_msg = HumanMessage(content=(
        f"Patient name: {name}\n"
        f"Age: {age}\n"
        f"Gender: {gender}\n"
        f"Active medical conditions: {conditions_str}\n"
        f"Fields already known from records: {prefilled_fields}\n"
        f"Write the opening greeting now."
    ))
    try:
        response = llm.invoke([system_msg, human_msg])
        return response.content.strip()
    except Exception:
        return (
            f"Hi {name}! I can see your health records. "
            f"I just need a few more details to estimate your treatment costs."
        )


def prefill_from_patient(patient_ctx: dict) -> tuple[dict, list[str]]:
    """
    Extracts known fields from patient data.
    Returns (prefilled_answers_dict, list_of_prefilled_field_names)
    """
    patient = patient_ctx["patient"]
    history = patient_ctx["medical_history"]
    answers = {}
    prefilled = []

    # Age from date_of_birth
    dob = patient.get("date_of_birth")
    if dob:
        answers["age"] = _calculate_age(dob)
        prefilled.append("age")

    # Gender
    gender = patient.get("gender")
    if gender:
        answers["gender"] = gender.lower()
        prefilled.append("gender")

    # Comorbidities from active medical history
    active_conditions = [h["condition_name"] for h in history]
    if active_conditions:
        mapping = map_conditions_to_risk(active_conditions)
        answers["comorbidities"] = mapping.get("mapped", [])
        prefilled.append("comorbidities")

    # Check smoking from medications/notes
    all_notes = " ".join(
        (h.get("notes") or "") + " " + (h.get("condition_name") or "")
        for h in history
    ).lower()
    medications = (patient.get("medications") or "").lower()
    if "smok" in all_notes or "nicotine" in medications:
        answers["smoking"] = True
        prefilled.append("smoking")

    return answers, prefilled
