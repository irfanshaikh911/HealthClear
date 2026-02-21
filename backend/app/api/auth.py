"""Simple auth endpoints — register, login, me, onboarding.

No JWT/bcrypt — keeps passwords as plain text in Supabase `users` table
(matching the existing schema). Returns user data directly.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from supabase import Client

from app.db.supabase import get_supabase

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ── Schemas ───────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class OnboardingRequest(BaseModel):
    full_name: str
    date_of_birth: str
    gender: str
    blood_type: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    is_pregnant: Optional[bool] = False
    organ_donor: Optional[bool] = False
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_history: Optional[str] = None


# ── Register ──────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest, client: Client = Depends(get_supabase)):
    # Check if email already exists
    existing = (
        client.table("users")
        .select("id")
        .eq("email", body.email)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Insert new user
    new_user = client.table("users").insert({
        "name": body.name,
        "email": body.email,
        "password": body.password,
        "is_admin": False,
        "is_active": True,
    }).execute()

    if not new_user.data:
        raise HTTPException(status_code=500, detail="Failed to create account.")

    user = new_user.data[0]
    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "patient_id": user.get("patient_id"),
            "profileComplete": user.get("patient_id") is not None,
        }
    }


# ── Login ─────────────────────────────────────────────────────

@router.post("/login")
def login(body: LoginRequest, client: Client = Depends(get_supabase)):
    result = (
        client.table("users")
        .select("*")
        .eq("email", body.email)
        .eq("password", body.password)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user = result.data[0]

    # If user has a patient_id, fetch the patient profile
    patient = None
    if user.get("patient_id"):
        p_result = (
            client.table("patients")
            .select("*")
            .eq("patient_id", user["patient_id"])
            .execute()
        )
        if p_result.data:
            patient = p_result.data[0]

    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "patient_id": user.get("patient_id"),
            "profileComplete": user.get("patient_id") is not None,
            **(patient or {}),
        }
    }


# ── Me (get current user by id) ──────────────────────────────

@router.get("/me/{user_id}")
def get_me(user_id: int, client: Client = Depends(get_supabase)):
    result = (
        client.table("users")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found.")

    user = result.data[0]

    patient = None
    if user.get("patient_id"):
        p_result = (
            client.table("patients")
            .select("*")
            .eq("patient_id", user["patient_id"])
            .execute()
        )
        if p_result.data:
            patient = p_result.data[0]

    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "patient_id": user.get("patient_id"),
            "profileComplete": user.get("patient_id") is not None,
            **(patient or {}),
        }
    }


# ── Onboarding (create patient profile) ──────────────────────

@router.post("/onboarding/{user_id}")
def complete_onboarding(user_id: int, body: OnboardingRequest, client: Client = Depends(get_supabase)):
    # Check user exists
    user_result = (
        client.table("users")
        .select("id, patient_id")
        .eq("id", user_id)
        .execute()
    )
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found.")

    user = user_result.data[0]

    # If patient already exists, update it
    if user.get("patient_id"):
        client.table("patients").update({
            "full_name": body.full_name,
            "date_of_birth": body.date_of_birth,
            "gender": body.gender,
            "blood_type": body.blood_type,
            "height_cm": body.height_cm,
            "weight_kg": body.weight_kg,
            "is_pregnant": body.is_pregnant,
            "organ_donor": body.organ_donor,
            "allergies": body.allergies,
            "medications": body.medications,
            "medical_history": body.medical_history,
        }).eq("patient_id", user["patient_id"]).execute()

        return {"patient_id": user["patient_id"], "updated": True}

    # Create new patient
    patient_result = client.table("patients").insert({
        "full_name": body.full_name,
        "date_of_birth": body.date_of_birth,
        "gender": body.gender,
        "blood_type": body.blood_type,
        "height_cm": body.height_cm,
        "weight_kg": body.weight_kg,
        "is_pregnant": body.is_pregnant,
        "organ_donor": body.organ_donor,
        "allergies": body.allergies,
        "medications": body.medications,
        "medical_history": body.medical_history,
    }).execute()

    if not patient_result.data:
        raise HTTPException(status_code=500, detail="Failed to create patient profile.")

    patient_id = patient_result.data[0]["patient_id"]

    # Link patient to user
    client.table("users").update({
        "patient_id": patient_id
    }).eq("id", user_id).execute()

    return {"patient_id": patient_id, "updated": False}
