from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from supabase import Client
from typing import List
from app.db.database import get_supabase
from app.models.bill import BillStatus
from app.schemas.schemas import BillUploadResponse, VerificationReportOut, BillHistoryItem, LineItemFinding
from app.services.file_service import save_upload
from app.services.bill_service import process_bill

router = APIRouter(prefix="/api/bills", tags=["Bill Verification"])


@router.post("/upload", response_model=BillUploadResponse, status_code=202)
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sb: Client = Depends(get_supabase),
):
    saved = await save_upload(file)
    bill_data = {
        "bill_uuid"         : saved["bill_uuid"],
        "original_filename" : saved["original_filename"],
        "file_path"         : saved["file_path"],
        "file_type"         : saved["file_type"],
        "status"            : BillStatus.PENDING,
    }
    result = sb.table("bills").insert(bill_data).execute()
    bill = result.data[0]
    background_tasks.add_task(process_bill, bill["id"], sb)
    return BillUploadResponse(
        bill_uuid=saved["bill_uuid"],
        message="Bill uploaded. Processing in background.",
        status=BillStatus.PENDING,
    )


@router.get("/report/{bill_uuid}", response_model=VerificationReportOut)
def get_report(bill_uuid: str, sb: Client = Depends(get_supabase)):
    result = sb.table("bills").select("*").eq("bill_uuid", bill_uuid).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Bill not found.")
    bill = result.data[0]

    if bill["status"] in [BillStatus.PROCESSING, BillStatus.PENDING]:
        raise HTTPException(status_code=202, detail=f"Still processing. Status: {bill['status']}")
    if bill["status"] == BillStatus.FAILED:
        raise HTTPException(status_code=500, detail="Processing failed. Please re-upload.")

    # Fetch the verification report
    rpt_result = sb.table("verification_reports").select("*").eq("bill_id", bill["id"]).execute()
    if not rpt_result.data:
        raise HTTPException(status_code=404, detail="Report not yet generated.")
    report = rpt_result.data[0]

    findings = [LineItemFinding(**f) for f in (report.get("findings_json") or [])]
    return VerificationReportOut(
        bill_uuid            = bill["bill_uuid"],
        report_id            = report["id"],
        generated_at         = report["generated_at"],
        hospital_name        = bill.get("hospital_name"),
        patient_name         = bill.get("patient_name"),
        ward_type            = bill.get("ward_type"),
        admission_date       = bill.get("admission_date"),
        discharge_date       = bill.get("discharge_date"),
        verdict              = report["verdict"],
        trust_score          = report["trust_score"],
        total_billed         = report.get("total_billed"),
        estimated_fair_price = report.get("estimated_fair"),
        total_overcharge     = report.get("total_overcharge"),
        overcharge_percent   = report.get("overcharge_percent"),
        total_items          = report.get("total_items", 0),
        flagged_items        = report.get("flagged_items", 0),
        overcharged_items    = report.get("overcharged_items", 0),
        duplicate_items      = report.get("duplicate_items", 0),
        math_error_items     = report.get("math_error_items", 0),
        unknown_items        = report.get("unknown_items", 0),
        findings             = findings,
        summary              = report.get("summary_text") or "",
        recommendations      = report.get("recommendations") or "",
    )


@router.get("/status/{bill_uuid}")
def get_status(bill_uuid: str, sb: Client = Depends(get_supabase)):
    result = sb.table("bills").select("bill_uuid, status").eq("bill_uuid", bill_uuid).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Bill not found.")
    return {"bill_uuid": bill_uuid, "status": result.data[0]["status"]}


@router.get("/history", response_model=List[BillHistoryItem])
def get_history(sb: Client = Depends(get_supabase)):
    result = sb.table("bills").select("*").order("uploaded_at", desc=True).execute()
    bills = result.data or []

    history = []
    for b in bills:
        # Fetch report for each bill (if exists) to show verdict/trust_score
        rpt = sb.table("verification_reports").select("verdict, trust_score").eq("bill_id", b["id"]).execute()
        rpt_data = rpt.data[0] if rpt.data else None
        history.append(BillHistoryItem(
            bill_uuid     = b["bill_uuid"],
            hospital_name = b.get("hospital_name"),
            patient_name  = b.get("patient_name"),
            total_billed  = b.get("net_payable") or b.get("total_billed"),
            status        = b["status"],
            verdict       = rpt_data["verdict"] if rpt_data else None,
            trust_score   = rpt_data["trust_score"] if rpt_data else None,
            uploaded_at   = b["uploaded_at"],
        ))
    return history
