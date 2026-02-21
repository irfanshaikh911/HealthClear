import json
import base64
import google.generativeai as genai
from pathlib import Path
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

EXTRACTION_PROMPT = """
You are a hospital bill analysis expert. Extract ALL information from this hospital bill.
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


def _load_file_as_part(file_path: str):
    path = Path(file_path)
    suffix = path.suffix.lower()
    with open(file_path, "rb") as f:
        data = f.read()
    if suffix in [".jpg", ".jpeg"]:
        return {"mime_type": "image/jpeg", "data": base64.b64encode(data).decode()}
    elif suffix == ".png":
        return {"mime_type": "image/png", "data": base64.b64encode(data).decode()}
    elif suffix == ".pdf":
        return {"mime_type": "application/pdf", "data": base64.b64encode(data).decode()}
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


async def extract_bill_data(file_path: str) -> dict:
    try:
        file_part = _load_file_as_part(file_path)
        response = model.generate_content([{"inline_data": file_part}, EXTRACTION_PROMPT])
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()
        extracted = json.loads(raw_text)
        return {"success": True, "data": extracted}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Failed to parse Gemini response: {str(e)}", "data": {}}
    except Exception as e:
        return {"success": False, "error": str(e), "data": {}}
