"""
Data model definitions as Python dataclasses.
Tables must exist in Supabase — run the SQL in setup.sql first.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Hospital:
    id: int
    name: str
    city: str
    base_cost: float
    success_rate: float
    base_complication_rate: float
    average_recovery_days: int
    room_cost_per_day: float
    accepts_insurance: bool = True
    insurance_coverage_pct: float = 0.0   # fraction of cost covered (0.0 – 1.0)

    @classmethod
    def from_dict(cls, d: dict) -> "Hospital":
        return cls(
            id=d["id"],
            name=d["name"],
            city=d["city"],
            base_cost=float(d["base_cost"]),
            success_rate=float(d["success_rate"]),
            base_complication_rate=float(d["base_complication_rate"]),
            average_recovery_days=int(d["average_recovery_days"]),
            room_cost_per_day=float(d["room_cost_per_day"]),
            accepts_insurance=bool(d.get("accepts_insurance", True)),
            insurance_coverage_pct=float(d.get("insurance_coverage_pct", 0.0)),
        )


@dataclass
class Procedure:
    id: int
    name: str
    base_cost: float
    average_length_of_stay: int

    @classmethod
    def from_dict(cls, d: dict) -> "Procedure":
        return cls(
            id=d["id"],
            name=d["name"],
            base_cost=float(d["base_cost"]),
            average_length_of_stay=int(d["average_length_of_stay"]),
        )


@dataclass
class RiskCondition:
    name: str
    cost_multiplier: float
    complication_multiplier: float

    @classmethod
    def from_dict(cls, d: dict) -> "RiskCondition":
        return cls(
            name=d["name"],
            cost_multiplier=float(d["cost_multiplier"]),
            complication_multiplier=float(d["complication_multiplier"]),
        )
