"""Pydantic schemas for the AI Assistant (cost estimation + conversational chat)."""

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Cost engine schemas ───────────────────────────────────────────────────────

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
    insurance_accepted: bool = True
    amount_covered: float = 0.0
    patient_out_of_pocket: float = 0.0


class PersonalizedSummary(BaseModel):
    estimated_cost_range: List[float]
    budget_fit: bool
    insurance_note: str
    insurance_accepted_count: int = 0


class ChatResponse(BaseModel):
    personalized_summary: PersonalizedSummary
    hospital_comparison: List[HospitalResult]
    ai_explanation: str


# ── Conversational questionnaire schemas ──────────────────────────────────────

class ChatMessage(BaseModel):
    """
    /chat schema.
    - START: send {patient_id} or {}
    - CONTINUE: send {session_id, answer}
    """
    patient_id: Optional[int] = None
    session_id: Optional[str] = None
    answer: Optional[str] = None


class QuestionResponse(BaseModel):
    session_id: str
    summary: Optional[str] = None
    known_summary: Optional[str] = None
    question: Optional[str] = None
    question_key: Optional[str] = None
    options: List[str] = []
    allow_other: bool = False
    awaiting_free_text: bool = False
    prefilled_fields: List[str] = []
    is_complete: bool = False
    result: Optional[ChatResponse] = None


# ── RAG chat schemas ──────────────────────────────────────────────────────────

class RagChatMessage(BaseModel):
    """
    /rag-chat schema.
    - Start: send {} or {patient_id: 1}
    - Continue: send {session_id: "...", message: "I need knee surgery in Pune"}
    """
    patient_id: Optional[int] = None
    session_id: Optional[str] = None
    message: Optional[str] = None


class RagChatResponse(BaseModel):
    session_id: str
    reply: str
    missing_fields: list = []
    collected: dict = {}
    is_complete: bool = False
    result: Optional[ChatResponse] = None
    next_field: Optional[str] = None
    suggested_options: list = []
