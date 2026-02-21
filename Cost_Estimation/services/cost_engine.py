from models import Hospital, Procedure


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
