from pydantic import BaseModel, Field
from typing import List, Optional


# ── Original cost-engine schemas (kept intact) ────────────────────────────────

class ChatRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    gender: str
    city: str
    insurance_status: str
    budget_limit: float
    selected_procedure: str
    comorbidities: List[str] = []
    smoking: bool = False
    room_preference: str = "general"


class HospitalResult(BaseModel):
    hospital_name: str
    personalized_cost: float
    success_rate: float
    adjusted_complication: float
    recovery_days: int
    value_score: float


class PersonalizedSummary(BaseModel):
    estimated_cost_range: List[float]
    budget_fit: bool
    insurance_note: str


class ChatResponse(BaseModel):
    personalized_summary: PersonalizedSummary
    hospital_comparison: List[HospitalResult]
    ai_explanation: str


# ── Conversational questionnaire schemas ──────────────────────────────────────

class ChatMessage(BaseModel):
    """
    Single endpoint schema for the conversational /chat flow.
    - To START a new session: send {patient_id} or just {}
    - To CONTINUE:           send {session_id, answer}
    """
    patient_id: Optional[int] = None
    session_id: Optional[str] = None
    answer: Optional[str] = None


class QuestionResponse(BaseModel):
    """
    Returned at every conversational step.
    When is_complete=True, the 'result' field contains the full hospital comparison.
    """
    session_id: str
    summary: Optional[str] = None          # personalized opening (patient_id flow)
    known_summary: Optional[str] = None    # running "here's what I know so far"
    question: Optional[str] = None
    question_key: Optional[str] = None
    options: List[str] = []
    allow_other: bool = False
    awaiting_free_text: bool = False
    prefilled_fields: List[str] = []       # fields auto-filled from patient record
    is_complete: bool = False
    result: Optional[ChatResponse] = None
