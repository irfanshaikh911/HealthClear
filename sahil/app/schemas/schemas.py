from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BillUploadResponse(BaseModel):
    bill_uuid: str
    message: str
    status: str


class LineItemFinding(BaseModel):
    item_name: str
    category: Optional[str]
    quantity: float
    unit: Optional[str]
    unit_price: float
    total_price: float
    standard_min: Optional[float]
    standard_max: Optional[float]
    flag: str
    severity: Optional[str]
    excess_amount: Optional[float]
    remark: str


class VerificationReportOut(BaseModel):
    bill_uuid: str
    report_id: int
    generated_at: datetime
    hospital_name: Optional[str]
    patient_name: Optional[str]
    ward_type: Optional[str]
    admission_date: Optional[str]
    discharge_date: Optional[str]
    verdict: str
    trust_score: int
    total_billed: Optional[float]
    estimated_fair_price: Optional[float]
    total_overcharge: Optional[float]
    overcharge_percent: Optional[float]
    total_items: int
    flagged_items: int
    overcharged_items: int
    duplicate_items: int
    math_error_items: int
    unknown_items: int
    findings: List[LineItemFinding]
    summary: str
    recommendations: str
    class Config:
        from_attributes = True


class BillHistoryItem(BaseModel):
    bill_uuid: str
    hospital_name: Optional[str]
    patient_name: Optional[str]
    total_billed: Optional[float]
    status: str
    verdict: Optional[str]
    trust_score: Optional[int]
    uploaded_at: datetime
    class Config:
        from_attributes = True
