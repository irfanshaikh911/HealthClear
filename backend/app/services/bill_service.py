"""Bill processing orchestrator.

Pipeline:
  - Images → Groq vision model (no OCR needed)
  - PDFs with text → PyPDF2 extract → Groq text model
  - PDFs without text → Groq vision model (scanned PDFs)
  Then: verify → store (Supabase).
"""

import os
from datetime import datetime, timezone

from supabase import Client

from app.models.enums import BillStatus
from app.services.ocr_service import extract_text
from app.services.groq_service import extract_bill_data, extract_bill_data_from_image
from app.services.verification_engine import verify_line_items, generate_report_summary


def _is_image(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff")


async def process_bill(bill_id: int, sb: Client) -> None:
    """Full bill processing pipeline — runs as a background task.

    1. Mark bill as PROCESSING
    2. Extract data: vision model for images, text model for PDFs
    3. Update bill record with extracted fields
    4. Verify each line item against standard prices
    5. Insert line items into DB
    6. Generate verification report
    7. Mark bill as COMPLETED
    """
    result = sb.table("bills").select("*").eq("id", bill_id).single().execute()
    bill = result.data
    if not bill:
        return

    try:
        # ── 1. Mark as processing ─────────────────────────────
        sb.table("bills").update({"status": BillStatus.PROCESSING}).eq("id", bill_id).execute()

        file_path = bill["file_path"]

        # ── 2. Extract data ───────────────────────────────────
        if _is_image(file_path):
            # Images → send directly to Groq vision model
            extraction = await extract_bill_data_from_image(file_path)
        else:
            # PDFs → try text extraction first
            bill_text = extract_text(file_path)
            if bill_text:
                extraction = await extract_bill_data(bill_text)
            else:
                # Scanned PDF with no selectable text → vision model
                extraction = await extract_bill_data_from_image(file_path)

        if not extraction["success"]:
            print(f"Extraction failed: {extraction.get('error')}")
            sb.table("bills").update({"status": BillStatus.FAILED}).eq("id", bill_id).execute()
            return

        data = extraction["data"]

        # ── 3. Update bill with extracted info ────────────────
        sb.table("bills").update({
            "raw_extracted_json": data,
            "hospital_name": data.get("hospital_name"),
            "patient_name": data.get("patient_name"),
            "patient_age": data.get("patient_age"),
            "patient_gender": data.get("patient_gender"),
            "ward_type": data.get("ward_type"),
            "admission_date": data.get("admission_date"),
            "discharge_date": data.get("discharge_date"),
            "doctor_name": data.get("doctor_name"),
            "total_billed": data.get("subtotal") or data.get("net_payable"),
            "taxes_billed": data.get("total_tax"),
            "discount_applied": data.get("discount") or 0,
            "net_payable": data.get("net_payable"),
        }).eq("id", bill_id).execute()

        # ── 4. Look up hospital ───────────────────────────────
        hospital_id = None
        if data.get("hospital_name"):
            h_result = (
                sb.table("hospitals")
                .select("id")
                .ilike("name", f"%{data['hospital_name']}%")
                .limit(1)
                .execute()
            )
            if h_result.data:
                hospital_id = h_result.data[0]["id"]

        # ── 5. Verify line items ──────────────────────────────
        raw_items = data.get("line_items", [])
        findings = verify_line_items(sb, raw_items, hospital_id)

        # ── 6. Insert line items ──────────────────────────────
        line_items_to_insert = []
        for raw, finding in zip(raw_items, findings):
            line_items_to_insert.append({
                "bill_id": bill_id,
                "item_name": finding["item_name"],
                "category": finding["category"],
                "quantity": finding["quantity"],
                "unit": finding["unit"],
                "unit_price": finding["unit_price"],
                "total_price": finding["total_price"],
                "gst_percent": raw.get("gst_percent"),
                "flag": finding["flag"],
                "standard_min": finding["standard_min"],
                "standard_max": finding["standard_max"],
                "excess_amount": finding.get("excess_amount"),
                "severity": finding.get("severity"),
            })
        if line_items_to_insert:
            sb.table("bill_line_items").insert(line_items_to_insert).execute()

        # ── 7. Generate verification report ───────────────────
        total_billed = data.get("net_payable") or data.get("subtotal") or 0
        summary = generate_report_summary(findings, total_billed)

        sb.table("verification_reports").insert({
            "bill_id": bill_id,
            "verdict": summary["verdict"],
            "trust_score": summary["trust_score"],
            "total_billed": summary["total_billed"],
            "estimated_fair": summary["estimated_fair"],
            "total_overcharge": summary["total_overcharge"],
            "overcharge_percent": summary["overcharge_percent"],
            "total_items": summary["total_items"],
            "flagged_items": summary["flagged_items"],
            "overcharged_items": summary["overcharged_items"],
            "duplicate_items": summary["duplicate_items"],
            "math_error_items": summary["math_error_items"],
            "unknown_items": summary["unknown_items"],
            "findings_json": findings,
            "summary_text": summary["summary_text"],
            "recommendations": summary["recommendations"],
        }).execute()

        # ── 8. Mark as completed ──────────────────────────────
        sb.table("bills").update({
            "status": BillStatus.COMPLETED,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", bill_id).execute()

    except Exception as exc:
        print(f"Bill processing error: {exc}")
        sb.table("bills").update({"status": BillStatus.FAILED}).eq("id", bill_id).execute()
        raise exc
