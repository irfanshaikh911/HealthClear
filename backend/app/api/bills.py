"""Bill verification API endpoints.

POST /api/bills/upload          Upload a bill (JPG/PNG/PDF)
GET  /api/bills/status/{uuid}   Check processing status
GET  /api/bills/report/{uuid}   Get full verification report
GET  /api/bills/history         List all past bills
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from supabase import Client

from app.db.supabase import get_supabase
from app.models.enums import BillStatus
from app.schemas.bills import (
    BillHistoryItem,
    BillStatusResponse,
    BillUploadResponse,
    LineItemFinding,
    VerificationReportOut,
)
from app.services.bill_service import process_bill
from app.services.file_service import save_upload

router = APIRouter(prefix="/api/bills", tags=["Bill Verification"])


# ── Upload ────────────────────────────────────────────────────

@router.post("/upload", response_model=BillUploadResponse, status_code=202)
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sb: Client = Depends(get_supabase),
):
    """Upload a bill image/PDF. Processing starts in the background."""
    saved = await save_upload(file)

    bill_data = {
        "bill_uuid": saved["bill_uuid"],
        "original_filename": saved["original_filename"],
        "file_path": saved["file_path"],
        "file_type": saved["file_type"],
        "status": BillStatus.PENDING,
    }
    result = sb.table("bills").insert(bill_data).execute()
    bill = result.data[0]

    background_tasks.add_task(process_bill, bill["id"], sb)

    return BillUploadResponse(
        bill_uuid=saved["bill_uuid"],
        message="Bill uploaded. Processing in background.",
        status=BillStatus.PENDING,
    )


# ── Status ────────────────────────────────────────────────────

@router.get("/status/{bill_uuid}", response_model=BillStatusResponse)
def get_status(bill_uuid: str, sb: Client = Depends(get_supabase)):
    """Check the processing status of a bill."""
    result = (
        sb.table("bills")
        .select("bill_uuid, status")
        .eq("bill_uuid", bill_uuid)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Bill not found.")
    return BillStatusResponse(
        bill_uuid=bill_uuid,
        status=result.data[0]["status"],
    )


# ── Report ────────────────────────────────────────────────────

@router.get("/report/{bill_uuid}", response_model=VerificationReportOut)
def get_report(bill_uuid: str, sb: Client = Depends(get_supabase)):
    """Get the full verification report for a processed bill."""
    result = sb.table("bills").select("*").eq("bill_uuid", bill_uuid).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Bill not found.")
    bill = result.data[0]

    if bill["status"] in (BillStatus.PROCESSING, BillStatus.PENDING):
        raise HTTPException(
            status_code=202,
            detail=f"Still processing. Status: {bill['status']}",
        )
    if bill["status"] == BillStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail="Processing failed. Please re-upload.",
        )

    # Fetch the verification report
    rpt_result = (
        sb.table("verification_reports")
        .select("*")
        .eq("bill_id", bill["id"])
        .execute()
    )
    if not rpt_result.data:
        raise HTTPException(status_code=404, detail="Report not yet generated.")
    report = rpt_result.data[0]

    findings = [LineItemFinding(**f) for f in (report.get("findings_json") or [])]

    return VerificationReportOut(
        bill_uuid=bill["bill_uuid"],
        report_id=report["id"],
        generated_at=report["generated_at"],
        hospital_name=bill.get("hospital_name"),
        patient_name=bill.get("patient_name"),
        ward_type=bill.get("ward_type"),
        admission_date=bill.get("admission_date"),
        discharge_date=bill.get("discharge_date"),
        verdict=report["verdict"],
        trust_score=report["trust_score"],
        total_billed=report.get("total_billed"),
        estimated_fair_price=report.get("estimated_fair"),
        total_overcharge=report.get("total_overcharge"),
        overcharge_percent=report.get("overcharge_percent"),
        total_items=report.get("total_items", 0),
        flagged_items=report.get("flagged_items", 0),
        overcharged_items=report.get("overcharged_items", 0),
        duplicate_items=report.get("duplicate_items", 0),
        math_error_items=report.get("math_error_items", 0),
        unknown_items=report.get("unknown_items", 0),
        findings=findings,
        summary=report.get("summary_text") or "",
        recommendations=report.get("recommendations") or "",
    )


# ── History ───────────────────────────────────────────────────

@router.get("/history", response_model=List[BillHistoryItem])
def get_history(sb: Client = Depends(get_supabase)):
    """List all past bills with their verdict and trust score."""
    result = (
        sb.table("bills")
        .select("*")
        .order("uploaded_at", desc=True)
        .execute()
    )
    bills = result.data or []

    history: list[BillHistoryItem] = []
    for b in bills:
        rpt = (
            sb.table("verification_reports")
            .select("verdict, trust_score")
            .eq("bill_id", b["id"])
            .execute()
        )
        rpt_data = rpt.data[0] if rpt.data else None
        history.append(
            BillHistoryItem(
                bill_uuid=b["bill_uuid"],
                hospital_name=b.get("hospital_name"),
                patient_name=b.get("patient_name"),
                total_billed=b.get("net_payable") or b.get("total_billed"),
                status=b["status"],
                verdict=rpt_data["verdict"] if rpt_data else None,
                trust_score=rpt_data["trust_score"] if rpt_data else None,
                uploaded_at=b["uploaded_at"],
            )
        )
    return history
