"""Cost engine — personalized cost, complication rate, and insurance breakdown."""

from app.models.assistant_models import Hospital, Procedure

# Ayushman Bharat maximum coverage cap (Government scheme)
AYUSHMAN_BHARAT_CAP = 500_000.0  # ₹5,00,000


def calculate_personalized_cost(
    hospital: Hospital,
    procedure: Procedure,
    total_risk: float,
) -> float:
    """
    Personalized cost = procedure base cost × (1 + risk)
                        + (LOS × room cost per day)
    """
    risk_adjusted_cost = procedure.base_cost * (1 + total_risk)
    room_cost = procedure.average_length_of_stay * hospital.room_cost_per_day
    return round(risk_adjusted_cost + room_cost, 2)


def calculate_adjusted_complication(
    hospital: Hospital,
    total_risk: float,
) -> float:
    """Adjusted complication rate = base_complication_rate × (1 + risk)"""
    return round(hospital.base_complication_rate * (1 + total_risk), 4)


def calculate_insurance_breakdown(
    hospital: Hospital,
    personalized_cost: float,
    insurance_status: str,
) -> dict:
    """
    Compute how much insurance covers at THIS hospital.

    Rules:
    - "none"       → no coverage
    - "government" → 100% up to Ayushman Bharat cap (₹5L), if hospital accepts
    - "private"    → hospital.insurance_coverage_pct of cost, if hospital accepts
    """
    ins = insurance_status.lower().strip()

    if ins == "none":
        return {
            "insurance_accepted": False,
            "amount_covered": 0.0,
            "patient_out_of_pocket": round(personalized_cost, 2),
        }

    if not hospital.accepts_insurance:
        return {
            "insurance_accepted": False,
            "amount_covered": 0.0,
            "patient_out_of_pocket": round(personalized_cost, 2),
        }

    # Hospital accepts insurance
    if ins == "government":
        raw_coverage = personalized_cost * hospital.insurance_coverage_pct
        capped = min(raw_coverage, AYUSHMAN_BHARAT_CAP)
        amount_covered = round(capped, 2)
    else:
        amount_covered = round(personalized_cost * hospital.insurance_coverage_pct, 2)

    out_of_pocket = round(max(personalized_cost - amount_covered, 0.0), 2)

    return {
        "insurance_accepted": True,
        "amount_covered": amount_covered,
        "patient_out_of_pocket": out_of_pocket,
    }
