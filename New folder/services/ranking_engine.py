"""
Ranking Engine
Ranks hospitals by value score and generates a Groq-powered AI explanation.
"""
import json
import os
from typing import List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from schemas import HospitalResult


def compute_value_score(
    success_rate: float,
    personalized_cost: float,
    adjusted_complication: float,
) -> float:
    """
    value_score = (success_rate × 100) ÷ (personalized_cost / 100000)
                  − (adjusted_complication × 50)
    Higher is better.
    """
    if personalized_cost == 0:
        return 0.0
    score = (success_rate * 100) / (personalized_cost / 100000) - (
        adjusted_complication * 50
    )
    return round(score, 4)


def rank_hospitals(results: List[HospitalResult]) -> List[HospitalResult]:
    """Sort hospitals by value_score descending (best first)."""
    return sorted(results, key=lambda h: h.value_score, reverse=True)


def generate_ai_explanation(top_two: List[HospitalResult]) -> str:
    """
    Uses Groq LLM to generate a clear, friendly tradeoff explanation comparing the
    top 2 hospitals. Falls back to a rule-based explanation if Groq is unavailable.
    """
    if len(top_two) == 0:
        return "No hospitals available for comparison."

    if len(top_two) == 1:
        h = top_two[0]
        return (
            f"{h.hospital_name} is the only available option with an estimated cost of "
            f"₹{h.personalized_cost:,.0f}, a {h.success_rate * 100:.1f}% success rate, "
            f"and a {h.adjusted_complication * 100:.2f}% complication risk."
        )

    h1, h2 = top_two[0], top_two[1]

    # Try Groq first
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=groq_key,
                temperature=0.5,
            )
            system_msg = SystemMessage(content=(
                "You are a compassionate healthcare cost advisor in India. "
                "Compare two hospitals for a patient in 3-4 concise, plain-English sentences. "
                "Mention which is cheaper, which has higher success rate, which has lower "
                "complication risk, and give a clear final recommendation. "
                "Use ₹ for rupees. Be warm but precise."
            ))
            human_msg = HumanMessage(content=(
                f"Hospital 1: {h1.hospital_name}\n"
                f"  Estimated cost: ₹{h1.personalized_cost:,.0f}\n"
                f"  Success rate: {h1.success_rate * 100:.1f}%\n"
                f"  Complication risk: {h1.adjusted_complication * 100:.2f}%\n"
                f"  Value score: {h1.value_score:.2f}\n\n"
                f"Hospital 2: {h2.hospital_name}\n"
                f"  Estimated cost: ₹{h2.personalized_cost:,.0f}\n"
                f"  Success rate: {h2.success_rate * 100:.1f}%\n"
                f"  Complication risk: {h2.adjusted_complication * 100:.2f}%\n"
                f"  Value score: {h2.value_score:.2f}\n\n"
                f"Write a patient-friendly comparison and recommend the best option."
            ))
            response = llm.invoke([system_msg, human_msg])
            return response.content.strip()
        except Exception:
            pass  # fall through to rule-based

    # Rule-based fallback
    cost_diff = abs(h1.personalized_cost - h2.personalized_cost)
    cheaper = h1.hospital_name if h1.personalized_cost < h2.personalized_cost else h2.hospital_name
    higher_success = h1.hospital_name if h1.success_rate > h2.success_rate else h2.hospital_name
    lower_complication = (
        h1.hospital_name if h1.adjusted_complication < h2.adjusted_complication else h2.hospital_name
    )
    return (
        f"Top recommendation: {h1.hospital_name} (Value Score: {h1.value_score:.2f}) "
        f"vs {h2.hospital_name} (Value Score: {h2.value_score:.2f}). "
        f"{cheaper} is more affordable (cost difference: ₹{cost_diff:,.0f}). "
        f"{higher_success} has the better success rate "
        f"({max(h1.success_rate, h2.success_rate) * 100:.1f}%). "
        f"{lower_complication} has a lower complication risk "
        f"({min(h1.adjusted_complication, h2.adjusted_complication) * 100:.2f}%). "
        f"Overall, {h1.hospital_name} offers the best value for your risk profile."
    )
