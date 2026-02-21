"""Verification engine — compares bill line items against standard prices.

Checks performed per item:
  1. Math check  (qty × unit_price == total_price)
  2. Duplicate   (same item appearing twice)
  3. Price match (fuzzy-match against standard_prices table)
  4. Overcharge  (unit_price > standard max + 10 % tolerance)
"""

from __future__ import annotations

import difflib
from typing import List, Optional

from supabase import Client

# ── Thresholds ────────────────────────────────────────────────
OVERCHARGE_THRESHOLD = 0.10     # 10 % tolerance above max
HIGH_SEVERITY_FACTOR = 2.0      # ≥ 2× the max  → HIGH
MEDIUM_SEVERITY_FACTOR = 1.5    # ≥ 1.5× the max → MEDIUM
MATH_ERROR_TOLERANCE = 1.0      # ₹1 rounding tolerance


# ── Helpers ───────────────────────────────────────────────────

def _find_standard_price(
    all_prices: list[dict],
    item_name: str,
    hospital_id: Optional[int] = None,
) -> Optional[dict]:
    """Fuzzy-match *item_name* against the pre-fetched standard prices list."""
    names = [p["item_name"].lower() for p in all_prices]
    matches = difflib.get_close_matches(item_name.lower(), names, n=1, cutoff=0.55)
    if not matches:
        return None

    matched_name = matches[0]
    matched_items = [p for p in all_prices if p["item_name"].lower() == matched_name]

    # Prefer hospital-specific price if available
    if hospital_id:
        specific = [m for m in matched_items if m.get("hospital_id") == hospital_id]
        if specific:
            return specific[0]

    # Fall back to global (no hospital_id) or first match
    global_items = [m for m in matched_items if m.get("hospital_id") is None]
    return global_items[0] if global_items else (matched_items[0] if matched_items else None)


def _check_math(item: dict) -> bool:
    """Return True if qty × unit_price ≈ total_price within tolerance."""
    expected = round(item.get("quantity", 1) * item.get("unit_price", 0), 2)
    actual = round(item.get("total_price", 0), 2)
    return abs(expected - actual) <= MATH_ERROR_TOLERANCE


def _get_severity(unit_price: float, standard_max: float) -> str:
    if standard_max == 0:
        return "HIGH"
    ratio = unit_price / standard_max
    if ratio >= HIGH_SEVERITY_FACTOR:
        return "HIGH"
    if ratio >= MEDIUM_SEVERITY_FACTOR:
        return "MEDIUM"
    return "LOW"


# ── Core verification ─────────────────────────────────────────

def verify_line_items(
    sb: Client,
    line_items_data: List[dict],
    hospital_id: Optional[int] = None,
) -> List[dict]:
    """Verify every line item and return a list of finding dicts."""
    # Fetch all standard prices once
    response = sb.table("standard_prices").select("*").execute()
    all_prices = response.data or []

    findings: list[dict] = []
    seen_items: dict[str, bool] = {}

    for item in line_items_data:
        item_name = item.get("item_name", "Unknown")
        quantity = float(item.get("quantity") or 1)
        unit_price = float(item.get("unit_price") or 0)
        total = float(item.get("total_price") or 0)
        category = item.get("category", "OTHER")
        unit = item.get("unit", "")

        finding: dict = {
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "unit": unit,
            "unit_price": unit_price,
            "total_price": total,
            "standard_min": None,
            "standard_max": None,
            "flag": "UNKNOWN",
            "severity": None,
            "excess_amount": None,
            "remark": "Item not found in standard price database.",
        }

        # 1) Math check
        if not _check_math(item):
            expected = round(quantity * unit_price, 2)
            finding.update(
                flag="MATH_ERROR",
                severity="HIGH",
                remark=f"Math error: {quantity} × ₹{unit_price} = ₹{expected}, but bill shows ₹{total}.",
            )
            findings.append(finding)
            continue

        # 2) Duplicate check
        key = item_name.lower().strip()
        if key in seen_items:
            finding.update(
                flag="DUPLICATE",
                severity="MEDIUM",
                remark=f"'{item_name}' appears more than once in the bill.",
            )
            findings.append(finding)
            continue
        seen_items[key] = True

        # 3) Standard price lookup
        standard = _find_standard_price(all_prices, item_name, hospital_id)
        if standard is None:
            finding.update(flag="UNKNOWN", remark="No standard price found. Manual review recommended.")
            findings.append(finding)
            continue

        finding["standard_min"] = standard["min_price"]
        finding["standard_max"] = standard["max_price"]

        # 4) Overcharge check
        if unit_price > standard["max_price"] * (1 + OVERCHARGE_THRESHOLD):
            excess = round((unit_price - standard["max_price"]) * quantity, 2)
            finding.update(
                flag="OVERCHARGED",
                severity=_get_severity(unit_price, standard["max_price"]),
                excess_amount=excess,
                remark=(
                    f"Billed ₹{unit_price}/unit but standard max is "
                    f"₹{standard['max_price']}/unit. Excess: ₹{excess}."
                ),
            )
        else:
            finding.update(
                flag="OK",
                remark=f"Price within standard range (₹{standard['min_price']}–₹{standard['max_price']}).",
            )

        findings.append(finding)

    return findings


# ── Report summary ────────────────────────────────────────────

def generate_report_summary(findings: List[dict], total_billed: float) -> dict:
    """Aggregate findings into a summary with verdict and trust score."""
    total_items = len(findings)
    overcharged = [f for f in findings if f["flag"] == "OVERCHARGED"]
    duplicates = [f for f in findings if f["flag"] == "DUPLICATE"]
    math_errors = [f for f in findings if f["flag"] == "MATH_ERROR"]
    unknown = [f for f in findings if f["flag"] == "UNKNOWN"]
    flagged = overcharged + duplicates + math_errors

    total_excess = sum(f.get("excess_amount") or 0 for f in overcharged)
    estimated_fair = round(total_billed - total_excess, 2) if total_billed else None
    overcharge_pct = (
        round(total_excess / total_billed * 100, 1)
        if total_billed and total_billed > 0
        else 0
    )

    # Trust score (0–100)
    score = 100
    score -= len(overcharged) * 10
    score -= len([f for f in overcharged if f.get("severity") == "HIGH"]) * 10
    score -= len(duplicates) * 8
    score -= len(math_errors) * 15
    score -= len(unknown) * 3
    trust_score = max(0, min(100, score))

    # Verdict
    if overcharge_pct >= 30 or any(f.get("severity") == "HIGH" for f in overcharged) or math_errors:
        verdict = "FRAUDULENT"
    elif flagged:
        verdict = "SUSPICIOUS"
    else:
        verdict = "CLEAN"

    # Human-readable summary
    if verdict == "CLEAN":
        summary = f"Bill appears legitimate. All {total_items} items verified within standard price ranges."
        recommendations = "No action required. Bill looks accurate."
    elif verdict == "SUSPICIOUS":
        summary = (
            f"Bill has {len(flagged)} suspicious item(s) out of {total_items}. "
            f"Estimated overcharge: ₹{total_excess:.2f} ({overcharge_pct}%)."
        )
        recommendations = (
            "1. Request itemized justification from hospital.\n"
            "2. Cross-check with insurance provider.\n"
            "3. Escalate to billing department if confirmed."
        )
    else:
        summary = (
            f"ALERT: Bill shows signs of fraudulent charging. "
            f"{len(flagged)} item(s) flagged. Total excess: ₹{total_excess:.2f} ({overcharge_pct}%)."
        )
        recommendations = (
            "1. Do NOT pay immediately.\n"
            "2. File complaint with hospital billing grievance cell.\n"
            "3. Contact State Medical Council or consumer forum.\n"
            "4. Report to IRDAI if insured."
        )

    return {
        "verdict": verdict,
        "trust_score": trust_score,
        "total_billed": total_billed,
        "estimated_fair": estimated_fair,
        "total_overcharge": round(total_excess, 2),
        "overcharge_percent": overcharge_pct,
        "total_items": total_items,
        "flagged_items": len(flagged),
        "overcharged_items": len(overcharged),
        "duplicate_items": len(duplicates),
        "math_error_items": len(math_errors),
        "unknown_items": len(unknown),
        "summary_text": summary,
        "recommendations": recommendations,
    }
