from typing import List


def calculate_total_risk(
    age: int,
    comorbidities: List[str],
    smoking: bool,
    all_risk_conditions: dict,
) -> float:
    """
    Returns the total additive risk multiplier based on patient profile.
    """
    total_risk: float = 0.0

    if age > 60:
        total_risk += all_risk_conditions.get("age_above_60", 0.05)

    for condition in comorbidities:
        key = condition.lower().strip()
        total_risk += all_risk_conditions.get(key, 0.0)

    if smoking:
        total_risk += all_risk_conditions.get("smoking", 0.06)

    return round(total_risk, 4)
