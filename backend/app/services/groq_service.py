"""Groq LLM service — sends extracted bill text to Groq for structured JSON extraction."""

import json

from groq import Groq

from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

EXTRACTION_PROMPT = """You are a hospital bill analysis expert. Analyze the following bill text and extract ALL information.
Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{
  "hospital_name": "string or null",
  "hospital_city": "string or null",
  "patient_name": "string or null",
  "patient_age": number or null,
  "patient_gender": "Male/Female/Other or null",
  "ward_type": "ICU/General/Private/Semi-Private or null",
  "admission_date": "string or null",
  "discharge_date": "string or null",
  "doctor_name": "string or null",
  "bill_number": "string or null",
  "bill_date": "string or null",
  "line_items": [
    {
      "item_name": "exact name from bill",
      "category": "BED/MEDICINE/PROCEDURE/LAB/EQUIPMENT/CONSULTATION/OTHER",
      "quantity": number,
      "unit": "days/tablets/units/etc",
      "unit_price": number,
      "total_price": number,
      "gst_percent": number or null
    }
  ],
  "subtotal": number or null,
  "total_tax": number or null,
  "discount": number or null,
  "net_payable": number or null,
  "currency": "INR"
}
Rules:
- Extract EVERY line item visible in the bill
- All prices must be numbers only (no currency symbols)
- Do NOT add any text outside the JSON
"""


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


async def extract_bill_data(bill_text: str) -> dict:
    """Send extracted bill text to Groq LLM for structured data extraction.

    Returns {"success": True, "data": {...}} on success,
            {"success": False, "error": "...", "data": {}} on failure.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": EXTRACTION_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"Here is the hospital bill text:\n\n{bill_text}",
                },
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=4096,
        )

        raw_text = chat_completion.choices[0].message.content
        raw_text = _strip_markdown_fences(raw_text)
        extracted = json.loads(raw_text)
        return {"success": True, "data": extracted}

    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": f"Failed to parse Groq response: {exc}",
            "data": {},
        }
    except Exception as exc:
        return {"success": False, "error": str(exc), "data": {}}
