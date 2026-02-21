"""
Run this from your BillVerification folder:
    python setup_project.py
It will create ALL missing files and folders automatically.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

files = {}

# ── __init__.py files ────────────────────────────────────────────────────────
files["app/__init__.py"] = ""
files["app/api/__init__.py"] = ""
files["app/api/routes/__init__.py"] = ""
files["app/core/__init__.py"] = ""
files["app/db/__init__.py"] = ""
files["app/models/__init__.py"] = ""
files["app/schemas/__init__.py"] = ""
files["app/services/__init__.py"] = ""
files["app/utils/__init__.py"] = ""

# ── app/core/config.py ───────────────────────────────────────────────────────
files["app/core/config.py"] = '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/bill_verification"
    GEMINI_API_KEY: str = ""
    SECRET_KEY: str = "changeme_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,pdf"
    APP_NAME: str = "Bill Verification System"
    DEBUG: bool = True

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
'''

# ── app/core/security.py ─────────────────────────────────────────────────────
files["app/core/security.py"] = '''from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.models.user import User
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
'''

# ── app/db/database.py ───────────────────────────────────────────────────────
files["app/db/database.py"] = '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
'''

# ── app/models/user.py ───────────────────────────────────────────────────────
files["app/models/user.py"] = '''from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    password   = Column(String(255), nullable=False)
    is_admin   = Column(Boolean, default=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
'''

# ── app/models/hospital.py ───────────────────────────────────────────────────
files["app/models/hospital.py"] = '''from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(200), nullable=False, index=True)
    city            = Column(String(100), nullable=False)
    state           = Column(String(100), nullable=True)
    tier            = Column(String(20), default="Tier2")
    registration_no = Column(String(100), nullable=True, unique=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    standard_prices = relationship("StandardPrice", back_populates="hospital")


class StandardPrice(Base):
    __tablename__ = "standard_prices"

    id          = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    item_name   = Column(String(200), nullable=False, index=True)
    category    = Column(String(50), nullable=False)
    unit        = Column(String(50), default="per day")
    min_price   = Column(Float, nullable=False)
    max_price   = Column(Float, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    hospital    = relationship("Hospital", back_populates="standard_prices")
'''

# ── app/models/bill.py ───────────────────────────────────────────────────────
files["app/models/bill.py"] = '''from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from app.db.database import Base


class BillStatus(str, enum.Enum):
    PENDING    = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"


class Bill(Base):
    __tablename__ = "bills"

    id                = Column(Integer, primary_key=True, index=True)
    bill_uuid         = Column(String(36), unique=True, index=True, nullable=False)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path         = Column(String(500), nullable=False)
    file_type         = Column(String(10), nullable=False)
    hospital_name     = Column(String(200), nullable=True)
    patient_name      = Column(String(150), nullable=True)
    patient_age       = Column(Integer, nullable=True)
    patient_gender    = Column(String(10), nullable=True)
    ward_type         = Column(String(50), nullable=True)
    admission_date    = Column(String(30), nullable=True)
    discharge_date    = Column(String(30), nullable=True)
    doctor_name       = Column(String(150), nullable=True)
    total_billed      = Column(Float, nullable=True)
    taxes_billed      = Column(Float, nullable=True)
    discount_applied  = Column(Float, nullable=True, default=0)
    net_payable       = Column(Float, nullable=True)
    raw_extracted_json= Column(JSON, nullable=True)
    status            = Column(String(20), default=BillStatus.PENDING)
    uploaded_at       = Column(DateTime(timezone=True), server_default=func.now())
    processed_at      = Column(DateTime(timezone=True), nullable=True)

    user       = relationship("User")
    line_items = relationship("BillLineItem", back_populates="bill", cascade="all, delete-orphan")
    report     = relationship("VerificationReport", back_populates="bill", uselist=False, cascade="all, delete-orphan")


class BillLineItem(Base):
    __tablename__ = "bill_line_items"

    id            = Column(Integer, primary_key=True, index=True)
    bill_id       = Column(Integer, ForeignKey("bills.id"), nullable=False)
    item_name     = Column(String(200), nullable=False)
    category      = Column(String(50), nullable=True)
    quantity      = Column(Float, default=1)
    unit          = Column(String(50), nullable=True)
    unit_price    = Column(Float, nullable=False)
    total_price   = Column(Float, nullable=False)
    gst_percent   = Column(Float, nullable=True)
    flag          = Column(String(20), nullable=True)
    standard_min  = Column(Float, nullable=True)
    standard_max  = Column(Float, nullable=True)
    excess_amount = Column(Float, nullable=True)
    severity      = Column(String(10), nullable=True)

    bill = relationship("Bill", back_populates="line_items")


class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id                 = Column(Integer, primary_key=True, index=True)
    bill_id            = Column(Integer, ForeignKey("bills.id"), nullable=False, unique=True)
    verdict            = Column(String(20), nullable=False)
    trust_score        = Column(Integer, nullable=False)
    total_billed       = Column(Float, nullable=True)
    estimated_fair     = Column(Float, nullable=True)
    total_overcharge   = Column(Float, nullable=True)
    overcharge_percent = Column(Float, nullable=True)
    total_items        = Column(Integer, default=0)
    flagged_items      = Column(Integer, default=0)
    overcharged_items  = Column(Integer, default=0)
    duplicate_items    = Column(Integer, default=0)
    math_error_items   = Column(Integer, default=0)
    unknown_items      = Column(Integer, default=0)
    findings_json      = Column(JSON, nullable=True)
    summary_text       = Column(Text, nullable=True)
    recommendations    = Column(Text, nullable=True)
    generated_at       = Column(DateTime(timezone=True), server_default=func.now())

    bill = relationship("Bill", back_populates="report")
'''

# ── app/schemas/schemas.py ───────────────────────────────────────────────────
files["app/schemas/schemas.py"] = '''from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool
    created_at: datetime
    class Config:
        from_attributes = True


class HospitalCreate(BaseModel):
    name: str
    city: str
    state: Optional[str] = None
    tier: str = "Tier2"
    registration_no: Optional[str] = None


class HospitalOut(HospitalCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class StandardPriceCreate(BaseModel):
    hospital_id: Optional[int] = None
    item_name: str
    category: str
    unit: str = "per day"
    min_price: float
    max_price: float


class StandardPriceOut(StandardPriceCreate):
    id: int
    class Config:
        from_attributes = True


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


class BulkPriceItem(BaseModel):
    item_name: str
    category: str
    unit: str
    min_price: float
    max_price: float
    hospital_id: Optional[int] = None


class BulkPriceUpload(BaseModel):
    items: List[BulkPriceItem]
'''

# ── app/services/file_service.py ─────────────────────────────────────────────
files["app/services/file_service.py"] = '''import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "application/pdf": "pdf",
}


async def save_upload(file: UploadFile, user_id: int) -> dict:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Only JPG, JPEG, PDF allowed.")

    ext = ALLOWED_MIME_TYPES[file.content_type]
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB.")

    bill_uuid = str(uuid.uuid4())
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, f"{bill_uuid}.{ext}")

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    return {
        "bill_uuid": bill_uuid,
        "file_path": file_path,
        "file_type": ext,
        "original_filename": file.filename,
    }
'''

# ── app/services/gemini_service.py ───────────────────────────────────────────
files["app/services/gemini_service.py"] = '''import json
import base64
import google.generativeai as genai
from pathlib import Path
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
'''

# ── app/services/verification_engine.py ──────────────────────────────────────
files["app/services/verification_engine.py"] = '''from sqlalchemy.orm import Session
from app.models.hospital import StandardPrice
from typing import List, Optional
import difflib

OVERCHARGE_THRESHOLD   = 0.10
HIGH_SEVERITY_FACTOR   = 2.0
MEDIUM_SEVERITY_FACTOR = 1.5
MATH_ERROR_TOLERANCE   = 1.0


def _find_standard_price(db: Session, item_name: str, hospital_id: Optional[int] = None):
    candidates = db.query(StandardPrice).all()
    names = [c.item_name.lower() for c in candidates]
    matches = difflib.get_close_matches(item_name.lower(), names, n=1, cutoff=0.55)
    if not matches:
        return None
    matched_name = matches[0]
    matched_items = [c for c in candidates if c.item_name.lower() == matched_name]
    if hospital_id:
        specific = [m for m in matched_items if m.hospital_id == hospital_id]
        if specific:
            return specific[0]
    global_items = [m for m in matched_items if m.hospital_id is None]
    return global_items[0] if global_items else (matched_items[0] if matched_items else None)


def _check_math(item_data: dict) -> bool:
    expected = round(item_data.get("quantity", 1) * item_data.get("unit_price", 0), 2)
    actual   = round(item_data.get("total_price", 0), 2)
    return abs(expected - actual) <= MATH_ERROR_TOLERANCE


def _get_severity(unit_price: float, standard_max: float) -> str:
    if standard_max == 0:
        return "HIGH"
    ratio = unit_price / standard_max
    if ratio >= HIGH_SEVERITY_FACTOR:
        return "HIGH"
    elif ratio >= MEDIUM_SEVERITY_FACTOR:
        return "MEDIUM"
    return "LOW"


def verify_line_items(db: Session, line_items_data: List[dict], hospital_id: Optional[int] = None) -> List[dict]:
    findings = []
    seen_items = {}

    for item in line_items_data:
        item_name  = item.get("item_name", "Unknown")
        quantity   = float(item.get("quantity") or 1)
        unit_price = float(item.get("unit_price") or 0)
        total      = float(item.get("total_price") or 0)
        category   = item.get("category", "OTHER")
        unit       = item.get("unit", "")

        finding = {
            "item_name"    : item_name,
            "category"     : category,
            "quantity"     : quantity,
            "unit"         : unit,
            "unit_price"   : unit_price,
            "total_price"  : total,
            "standard_min" : None,
            "standard_max" : None,
            "flag"         : "UNKNOWN",
            "severity"     : None,
            "excess_amount": None,
            "remark"       : "Item not found in standard price database.",
        }

        if not _check_math(item):
            finding["flag"]     = "MATH_ERROR"
            finding["severity"] = "HIGH"
            expected = round(quantity * unit_price, 2)
            finding["remark"]   = f"Math error: {quantity} x Rs{unit_price} = Rs{expected}, but bill shows Rs{total}."
            findings.append(finding)
            continue

        key = item_name.lower().strip()
        if key in seen_items:
            finding["flag"]     = "DUPLICATE"
            finding["severity"] = "MEDIUM"
            finding["remark"]   = f"\'{item_name}\' appears more than once in the bill."
            findings.append(finding)
            continue
        seen_items[key] = True

        standard = _find_standard_price(db, item_name, hospital_id)
        if standard is None:
            finding["flag"]   = "UNKNOWN"
            finding["remark"] = "No standard price found. Manual review recommended."
            findings.append(finding)
            continue

        finding["standard_min"] = standard.min_price
        finding["standard_max"] = standard.max_price

        if unit_price > standard.max_price * (1 + OVERCHARGE_THRESHOLD):
            excess = round((unit_price - standard.max_price) * quantity, 2)
            finding["flag"]          = "OVERCHARGED"
            finding["severity"]      = _get_severity(unit_price, standard.max_price)
            finding["excess_amount"] = excess
            finding["remark"]        = f"Billed Rs{unit_price}/unit but standard max is Rs{standard.max_price}/unit. Excess: Rs{excess}."
        else:
            finding["flag"]   = "OK"
            finding["remark"] = f"Price within standard range (Rs{standard.min_price}-Rs{standard.max_price})."

        findings.append(finding)
    return findings


def generate_report_summary(findings: List[dict], total_billed: float) -> dict:
    total_items   = len(findings)
    overcharged   = [f for f in findings if f["flag"] == "OVERCHARGED"]
    duplicates    = [f for f in findings if f["flag"] == "DUPLICATE"]
    math_errors   = [f for f in findings if f["flag"] == "MATH_ERROR"]
    unknown       = [f for f in findings if f["flag"] == "UNKNOWN"]
    flagged       = overcharged + duplicates + math_errors
    total_excess  = sum(f.get("excess_amount") or 0 for f in overcharged)
    estimated_fair= round(total_billed - total_excess, 2) if total_billed else None
    overcharge_pct= round((total_excess / total_billed * 100), 1) if total_billed and total_billed > 0 else 0

    score = 100
    score -= len(overcharged) * 10
    score -= len([f for f in overcharged if f.get("severity") == "HIGH"]) * 10
    score -= len(duplicates) * 8
    score -= len(math_errors) * 15
    score -= len(unknown) * 3
    trust_score = max(0, min(100, score))

    if overcharge_pct >= 30 or any(f.get("severity") == "HIGH" for f in overcharged) or math_errors:
        verdict = "FRAUDULENT"
    elif flagged:
        verdict = "SUSPICIOUS"
    else:
        verdict = "CLEAN"

    if verdict == "CLEAN":
        summary = f"Bill appears legitimate. All {total_items} items verified within standard price ranges."
        recommendations = "No action required. Bill looks accurate."
    elif verdict == "SUSPICIOUS":
        summary = f"Bill has {len(flagged)} suspicious item(s) out of {total_items}. Estimated overcharge: Rs{total_excess:.2f} ({overcharge_pct}%)."
        recommendations = "1. Request itemized justification from hospital.\\n2. Cross-check with insurance provider.\\n3. Escalate to billing department if confirmed."
    else:
        summary = f"ALERT: Bill shows signs of fraudulent charging. {len(flagged)} item(s) flagged. Total excess: Rs{total_excess:.2f} ({overcharge_pct}%)."
        recommendations = "1. Do NOT pay immediately.\\n2. File complaint with hospital billing grievance cell.\\n3. Contact State Medical Council or consumer forum.\\n4. Report to IRDAI if insured."

    return {
        "verdict"           : verdict,
        "trust_score"       : trust_score,
        "total_billed"      : total_billed,
        "estimated_fair"    : estimated_fair,
        "total_overcharge"  : round(total_excess, 2),
        "overcharge_percent": overcharge_pct,
        "total_items"       : total_items,
        "flagged_items"     : len(flagged),
        "overcharged_items" : len(overcharged),
        "duplicate_items"   : len(duplicates),
        "math_error_items"  : len(math_errors),
        "unknown_items"     : len(unknown),
        "summary_text"      : summary,
        "recommendations"   : recommendations,
    }
'''

# ── app/services/bill_service.py ─────────────────────────────────────────────
files["app/services/bill_service.py"] = '''from datetime import datetime
from sqlalchemy.orm import Session
from app.models.bill import Bill, BillLineItem, VerificationReport, BillStatus
from app.models.hospital import Hospital
from app.services.gemini_service import extract_bill_data
from app.services.verification_engine import verify_line_items, generate_report_summary


async def process_bill(bill_id: int, db: Session):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return
    try:
        bill.status = BillStatus.PROCESSING
        db.commit()

        result = await extract_bill_data(bill.file_path)
        if not result["success"]:
            bill.status = BillStatus.FAILED
            db.commit()
            return

        data = result["data"]
        bill.raw_extracted_json = data
        bill.hospital_name   = data.get("hospital_name")
        bill.patient_name    = data.get("patient_name")
        bill.patient_age     = data.get("patient_age")
        bill.patient_gender  = data.get("patient_gender")
        bill.ward_type       = data.get("ward_type")
        bill.admission_date  = data.get("admission_date")
        bill.discharge_date  = data.get("discharge_date")
        bill.doctor_name     = data.get("doctor_name")
        bill.total_billed    = data.get("subtotal") or data.get("net_payable")
        bill.taxes_billed    = data.get("total_tax")
        bill.discount_applied= data.get("discount") or 0
        bill.net_payable     = data.get("net_payable")

        hospital_id = None
        if bill.hospital_name:
            hospital = db.query(Hospital).filter(Hospital.name.ilike(f"%{bill.hospital_name}%")).first()
            if hospital:
                hospital_id = hospital.id

        raw_items = data.get("line_items", [])
        findings  = verify_line_items(db, raw_items, hospital_id)

        for raw, finding in zip(raw_items, findings):
            line = BillLineItem(
                bill_id      = bill.id,
                item_name    = finding["item_name"],
                category     = finding["category"],
                quantity     = finding["quantity"],
                unit         = finding["unit"],
                unit_price   = finding["unit_price"],
                total_price  = finding["total_price"],
                gst_percent  = raw.get("gst_percent"),
                flag         = finding["flag"],
                standard_min = finding["standard_min"],
                standard_max = finding["standard_max"],
                excess_amount= finding.get("excess_amount"),
                severity     = finding.get("severity"),
            )
            db.add(line)

        total_billed = bill.net_payable or bill.total_billed or 0
        summary = generate_report_summary(findings, total_billed)

        report = VerificationReport(
            bill_id            = bill.id,
            verdict            = summary["verdict"],
            trust_score        = summary["trust_score"],
            total_billed       = summary["total_billed"],
            estimated_fair     = summary["estimated_fair"],
            total_overcharge   = summary["total_overcharge"],
            overcharge_percent = summary["overcharge_percent"],
            total_items        = summary["total_items"],
            flagged_items      = summary["flagged_items"],
            overcharged_items  = summary["overcharged_items"],
            duplicate_items    = summary["duplicate_items"],
            math_error_items   = summary["math_error_items"],
            unknown_items      = summary["unknown_items"],
            findings_json      = findings,
            summary_text       = summary["summary_text"],
            recommendations    = summary["recommendations"],
        )
        db.add(report)

        bill.status       = BillStatus.COMPLETED
        bill.processed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        bill.status = BillStatus.FAILED
        db.commit()
        raise e
'''

# ── app/api/routes/auth.py ───────────────────────────────────────────────────
files["app/api/routes/auth.py"] = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserOut
from app.core.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = User(name=payload.name, email=payload.email, password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
'''

# ── app/api/routes/bills.py ──────────────────────────────────────────────────
files["app/api/routes/bills.py"] = '''from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.bill import Bill, BillStatus
from app.schemas.schemas import BillUploadResponse, VerificationReportOut, BillHistoryItem, LineItemFinding
from app.core.security import get_current_user
from app.services.file_service import save_upload
from app.services.bill_service import process_bill

router = APIRouter(prefix="/api/bills", tags=["Bill Verification"])


@router.post("/upload", response_model=BillUploadResponse, status_code=202)
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = await save_upload(file, current_user.id)
    bill = Bill(
        bill_uuid         = saved["bill_uuid"],
        user_id           = current_user.id,
        original_filename = saved["original_filename"],
        file_path         = saved["file_path"],
        file_type         = saved["file_type"],
        status            = BillStatus.PENDING,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    background_tasks.add_task(process_bill, bill.id, db)
    return BillUploadResponse(bill_uuid=saved["bill_uuid"], message="Bill uploaded. Processing in background.", status=BillStatus.PENDING)


@router.get("/report/{bill_uuid}", response_model=VerificationReportOut)
def get_report(bill_uuid: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.bill_uuid == bill_uuid, Bill.user_id == current_user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found.")
    if bill.status in [BillStatus.PROCESSING, BillStatus.PENDING]:
        raise HTTPException(status_code=202, detail=f"Still processing. Status: {bill.status}")
    if bill.status == BillStatus.FAILED:
        raise HTTPException(status_code=500, detail="Processing failed. Please re-upload.")
    if not bill.report:
        raise HTTPException(status_code=404, detail="Report not yet generated.")

    report   = bill.report
    findings = [LineItemFinding(**f) for f in (report.findings_json or [])]
    return VerificationReportOut(
        bill_uuid            = bill.bill_uuid,
        report_id            = report.id,
        generated_at         = report.generated_at,
        hospital_name        = bill.hospital_name,
        patient_name         = bill.patient_name,
        ward_type            = bill.ward_type,
        admission_date       = bill.admission_date,
        discharge_date       = bill.discharge_date,
        verdict              = report.verdict,
        trust_score          = report.trust_score,
        total_billed         = report.total_billed,
        estimated_fair_price = report.estimated_fair,
        total_overcharge     = report.total_overcharge,
        overcharge_percent   = report.overcharge_percent,
        total_items          = report.total_items,
        flagged_items        = report.flagged_items,
        overcharged_items    = report.overcharged_items,
        duplicate_items      = report.duplicate_items,
        math_error_items     = report.math_error_items,
        unknown_items        = report.unknown_items,
        findings             = findings,
        summary              = report.summary_text or "",
        recommendations      = report.recommendations or "",
    )


@router.get("/status/{bill_uuid}")
def get_status(bill_uuid: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.bill_uuid == bill_uuid, Bill.user_id == current_user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found.")
    return {"bill_uuid": bill_uuid, "status": bill.status}


@router.get("/history", response_model=List[BillHistoryItem])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.uploaded_at.desc()).all()
    return [BillHistoryItem(
        bill_uuid     = b.bill_uuid,
        hospital_name = b.hospital_name,
        patient_name  = b.patient_name,
        total_billed  = b.net_payable or b.total_billed,
        status        = b.status,
        verdict       = b.report.verdict if b.report else None,
        trust_score   = b.report.trust_score if b.report else None,
        uploaded_at   = b.uploaded_at,
    ) for b in bills]
'''

# ── app/api/routes/admin.py ──────────────────────────────────────────────────
files["app/api/routes/admin.py"] = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.hospital import Hospital, StandardPrice
from app.schemas.schemas import HospitalCreate, HospitalOut, StandardPriceCreate, StandardPriceOut, BulkPriceUpload
from app.core.security import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.post("/hospitals", response_model=HospitalOut, status_code=201)
def add_hospital(payload: HospitalCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    hospital = Hospital(**payload.model_dump())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


@router.get("/hospitals", response_model=List[HospitalOut])
def list_hospitals(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(Hospital).all()


@router.post("/prices", response_model=StandardPriceOut, status_code=201)
def add_price(payload: StandardPriceCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    price = StandardPrice(**payload.model_dump())
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


@router.get("/prices", response_model=List[StandardPriceOut])
def list_prices(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(StandardPrice).all()


@router.post("/prices/bulk", status_code=201)
def bulk_add_prices(payload: BulkPriceUpload, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    items = [StandardPrice(**item.model_dump()) for item in payload.items]
    db.bulk_save_objects(items)
    db.commit()
    return {"message": f"{len(items)} prices added successfully."}


@router.delete("/prices/{price_id}", status_code=204)
def delete_price(price_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    price = db.query(StandardPrice).filter(StandardPrice.id == price_id).first()
    if not price:
        raise HTTPException(status_code=404, detail="Price not found.")
    db.delete(price)
    db.commit()
'''

# ── app/main.py ──────────────────────────────────────────────────────────────
files["app/main.py"] = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.core.config import settings
from app.db.database import create_tables
from app.api.routes import auth, bills, admin

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered hospital bill verification using Gemini 1.5 Flash",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_tables()
    print(f"✅ {settings.APP_NAME} started!")

app.include_router(auth.router)
app.include_router(bills.router)
app.include_router(admin.router)

@app.get("/", tags=["Health"])
def health():
    return {"status": "running", "app": settings.APP_NAME, "docs": "/docs"}
'''

# ── seed_prices.py ───────────────────────────────────────────────────────────
files["seed_prices.py"] = '''import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, create_tables
from app.models.hospital import StandardPrice

PRICES = [
    {"item_name": "General Ward Bed",          "category": "BED",          "unit": "per day",     "min_price": 500,    "max_price": 2000},
    {"item_name": "Semi-Private Ward Bed",     "category": "BED",          "unit": "per day",     "min_price": 1500,   "max_price": 4000},
    {"item_name": "Private Ward Bed",          "category": "BED",          "unit": "per day",     "min_price": 3000,   "max_price": 8000},
    {"item_name": "ICU Bed",                   "category": "BED",          "unit": "per day",     "min_price": 5000,   "max_price": 15000},
    {"item_name": "NICU Bed",                  "category": "BED",          "unit": "per day",     "min_price": 6000,   "max_price": 18000},
    {"item_name": "HDU Bed",                   "category": "BED",          "unit": "per day",     "min_price": 3500,   "max_price": 9000},
    {"item_name": "Doctor Consultation",       "category": "CONSULTATION",  "unit": "per visit",  "min_price": 300,    "max_price": 1500},
    {"item_name": "Specialist Consultation",   "category": "CONSULTATION",  "unit": "per visit",  "min_price": 500,    "max_price": 3000},
    {"item_name": "Nursing Charges",           "category": "EQUIPMENT",     "unit": "per day",    "min_price": 200,    "max_price": 1000},
    {"item_name": "Diet Charges",              "category": "OTHER",         "unit": "per day",    "min_price": 150,    "max_price": 600},
    {"item_name": "Appendectomy",              "category": "PROCEDURE",     "unit": "one time",   "min_price": 40000,  "max_price": 100000},
    {"item_name": "Angioplasty",               "category": "PROCEDURE",     "unit": "one time",   "min_price": 100000, "max_price": 350000},
    {"item_name": "Normal Delivery",           "category": "PROCEDURE",     "unit": "one time",   "min_price": 15000,  "max_price": 50000},
    {"item_name": "C-Section",                 "category": "PROCEDURE",     "unit": "one time",   "min_price": 25000,  "max_price": 80000},
    {"item_name": "Endoscopy",                 "category": "PROCEDURE",     "unit": "one time",   "min_price": 3000,   "max_price": 8000},
    {"item_name": "Dialysis",                  "category": "PROCEDURE",     "unit": "per session","min_price": 1500,   "max_price": 4000},
    {"item_name": "Operation Theatre Charges", "category": "PROCEDURE",     "unit": "per hour",   "min_price": 5000,   "max_price": 20000},
    {"item_name": "Anaesthesia Charges",       "category": "PROCEDURE",     "unit": "per hour",   "min_price": 2000,   "max_price": 8000},
    {"item_name": "CBC Complete Blood Count",  "category": "LAB",           "unit": "per test",   "min_price": 200,    "max_price": 600},
    {"item_name": "Blood Culture",             "category": "LAB",           "unit": "per test",   "min_price": 800,    "max_price": 2000},
    {"item_name": "Lipid Profile",             "category": "LAB",           "unit": "per test",   "min_price": 400,    "max_price": 900},
    {"item_name": "Thyroid Profile",           "category": "LAB",           "unit": "per test",   "min_price": 500,    "max_price": 1200},
    {"item_name": "HbA1c",                     "category": "LAB",           "unit": "per test",   "min_price": 300,    "max_price": 700},
    {"item_name": "Urine Routine",             "category": "LAB",           "unit": "per test",   "min_price": 100,    "max_price": 300},
    {"item_name": "ECG",                       "category": "LAB",           "unit": "per test",   "min_price": 150,    "max_price": 500},
    {"item_name": "Echo Cardiography",         "category": "LAB",           "unit": "per test",   "min_price": 1500,   "max_price": 4000},
    {"item_name": "CT Scan Head",              "category": "LAB",           "unit": "per test",   "min_price": 3000,   "max_price": 8000},
    {"item_name": "MRI Brain",                 "category": "LAB",           "unit": "per test",   "min_price": 6000,   "max_price": 15000},
    {"item_name": "X-Ray Chest",               "category": "LAB",           "unit": "per test",   "min_price": 200,    "max_price": 600},
    {"item_name": "Ultrasound Abdomen",        "category": "LAB",           "unit": "per test",   "min_price": 500,    "max_price": 1500},
    {"item_name": "Ventilator Charges",        "category": "EQUIPMENT",     "unit": "per day",    "min_price": 3000,   "max_price": 10000},
    {"item_name": "Oxygen Charges",            "category": "EQUIPMENT",     "unit": "per day",    "min_price": 300,    "max_price": 1500},
    {"item_name": "IV Cannula",                "category": "EQUIPMENT",     "unit": "per piece",  "min_price": 30,     "max_price": 100},
    {"item_name": "Paracetamol 500mg",         "category": "MEDICINE",      "unit": "per tablet", "min_price": 1,      "max_price": 5},
    {"item_name": "Amoxicillin 500mg",         "category": "MEDICINE",      "unit": "per capsule","min_price": 5,      "max_price": 20},
    {"item_name": "Normal Saline 500ml",       "category": "MEDICINE",      "unit": "per bottle", "min_price": 40,     "max_price": 120},
    {"item_name": "Ringer Lactate 500ml",      "category": "MEDICINE",      "unit": "per bottle", "min_price": 40,     "max_price": 130},
]

def seed():
    create_tables()
    db = SessionLocal()
    try:
        existing = db.query(StandardPrice).count()
        if existing > 0:
            print(f"Already {existing} prices in DB. Skipping.")
            return
        items = [StandardPrice(hospital_id=None, **p) for p in PRICES]
        db.bulk_save_objects(items)
        db.commit()
        print(f"✅ Seeded {len(items)} standard prices successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
'''

# ─── Write all files ──────────────────────────────────────────────────────────
created = 0
for relative_path, content in files.items():
    full_path = os.path.join(BASE, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Created: {relative_path}")
    created += 1

print(f"\n🎉 Done! {created} files created successfully.")
print("\nNext steps:")
print("  1. python seed_prices.py")
print("  2. uvicorn app.main:app --reload")
print("  3. Open http://localhost:8000/docs")
