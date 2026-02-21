"""Pydantic response / request schemas for bill verification."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ── Upload ────────────────────────────────────────────────────

class BillUploadResponse(BaseModel):
    bill_uuid: str
    message: str
    status: str


# ── Status ────────────────────────────────────────────────────

class BillStatusResponse(BaseModel):
    bill_uuid: str
    status: str


# ── Line-item finding (used inside report) ────────────────────

class LineItemFinding(BaseModel):
    item_name: str
    category: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: float
    total_price: float
    standard_min: Optional[float] = None
    standard_max: Optional[float] = None
    flag: str
    severity: Optional[str] = None
    excess_amount: Optional[float] = None
    remark: str


# ── Full verification report ──────────────────────────────────

class VerificationReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bill_uuid: str
    report_id: int
    generated_at: datetime

    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    ward_type: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None

    verdict: str
    trust_score: int

    total_billed: Optional[float] = None
    estimated_fair_price: Optional[float] = None
    total_overcharge: Optional[float] = None
    overcharge_percent: Optional[float] = None

    total_items: int
    flagged_items: int
    overcharged_items: int
    duplicate_items: int
    math_error_items: int
    unknown_items: int

    findings: List[LineItemFinding]
    summary: str
    recommendations: str


# ── Bill history list item ────────────────────────────────────

class BillHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bill_uuid: str
    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    total_billed: Optional[float] = None
    status: str
    verdict: Optional[str] = None
    trust_score: Optional[int] = None
    uploaded_at: datetime
