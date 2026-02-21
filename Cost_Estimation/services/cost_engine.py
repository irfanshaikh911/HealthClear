from models import Hospital, Procedure

# Ayushman Bharat maximum coverage cap (Government scheme)
AYUSHMAN_BHARAT_CAP = 500_000.0   # ₹5,00,000


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
    """
    Adjusted complication rate = base_complication_rate × (1 + risk)
    """
    return round(hospital.base_complication_rate * (1 + total_risk), 4)


def calculate_insurance_breakdown(
    hospital: Hospital,
    personalized_cost: float,
    insurance_status: str,   # "private" | "government" | "none"
) -> dict:
    """
    Compute how much insurance covers at THIS hospital and the patient's net cost.

    Returns:
        {
            "insurance_accepted": bool,
            "amount_covered":     float,  # ₹ paid by insurance
            "patient_out_of_pocket": float,  # ₹ patient must pay
        }

    Rules:
    - "none"       → no coverage regardless of hospital
    - "government" → 100 % up to Ayushman Bharat cap (₹5L), only if hospital accepts it
                     (we treat insurance_coverage_pct == 1.0 as Ayushman empanelled)
    - "private"    → hospital.insurance_coverage_pct % of personalized cost,
                      only if hospital accepts insurance
    - Hospital that does NOT accept insurance → amount_covered = 0
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
        # Ayushman Bharat / PMJAY: covers up to ₹5L per annum
        raw_coverage = personalized_cost * hospital.insurance_coverage_pct
        capped = min(raw_coverage, AYUSHMAN_BHARAT_CAP)
        amount_covered = round(capped, 2)
    else:
        # Private insurance: covers hospital's declared coverage percentage
        amount_covered = round(personalized_cost * hospital.insurance_coverage_pct, 2)

    out_of_pocket = round(max(personalized_cost - amount_covered, 0.0), 2)

    return {
        "insurance_accepted": True,
        "amount_covered": amount_covered,
        "patient_out_of_pocket": out_of_pocket,
    }
