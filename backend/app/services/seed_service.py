"""Seed service — seeds hospitals, procedures, and risk conditions on startup."""

from supabase import Client

HOSPITALS = [
    {
        "name": "Ruby Hall Clinic", "city": "Pune",
        "base_cost": 50000.0, "success_rate": 0.92,
        "base_complication_rate": 0.05, "average_recovery_days": 5,
        "room_cost_per_day": 3500.0,
        "accepts_insurance": True, "insurance_coverage_pct": 0.75,
    },
    {
        "name": "Sahyadri Super Speciality Hospital", "city": "Pune",
        "base_cost": 45000.0, "success_rate": 0.89,
        "base_complication_rate": 0.06, "average_recovery_days": 6,
        "room_cost_per_day": 3000.0,
        "accepts_insurance": True, "insurance_coverage_pct": 0.70,
    },
    {
        "name": "Jehangir Hospital", "city": "Pune",
        "base_cost": 55000.0, "success_rate": 0.94,
        "base_complication_rate": 0.04, "average_recovery_days": 4,
        "room_cost_per_day": 4000.0,
        "accepts_insurance": True, "insurance_coverage_pct": 0.80,
    },
    {
        "name": "KEM Hospital", "city": "Pune",
        "base_cost": 30000.0, "success_rate": 0.85,
        "base_complication_rate": 0.08, "average_recovery_days": 7,
        "room_cost_per_day": 2000.0,
        "accepts_insurance": True, "insurance_coverage_pct": 1.00,
    },
    {
        "name": "Deenanath Mangeshkar Hospital", "city": "Pune",
        "base_cost": 48000.0, "success_rate": 0.91,
        "base_complication_rate": 0.055, "average_recovery_days": 5,
        "room_cost_per_day": 3200.0,
        "accepts_insurance": True, "insurance_coverage_pct": 0.72,
    },
]

PROCEDURES = [
    {"name": "Knee Replacement",     "base_cost": 120000.0, "average_length_of_stay": 5},
    {"name": "Hip Replacement",      "base_cost": 130000.0, "average_length_of_stay": 6},
    {"name": "Spinal Surgery",       "base_cost": 150000.0, "average_length_of_stay": 7},
    {"name": "Gallbladder Surgery",  "base_cost":  60000.0, "average_length_of_stay": 3},
    {"name": "Appendectomy",         "base_cost":  45000.0, "average_length_of_stay": 3},
    {"name": "Hernia Repair",        "base_cost":  55000.0, "average_length_of_stay": 2},
    {"name": "Angioplasty",          "base_cost": 180000.0, "average_length_of_stay": 4},
    {"name": "Bypass Surgery",       "base_cost": 300000.0, "average_length_of_stay": 10},
    {"name": "C-section",            "base_cost":  50000.0, "average_length_of_stay": 4},
    {"name": "Hysterectomy",         "base_cost":  80000.0, "average_length_of_stay": 5},
    {"name": "Tonsillectomy",        "base_cost":  30000.0, "average_length_of_stay": 2},
    {"name": "Kidney Stone Removal", "base_cost":  70000.0, "average_length_of_stay": 3},
    {"name": "Prostate Surgery",     "base_cost":  90000.0, "average_length_of_stay": 5},
    {"name": "Cataract Surgery",     "base_cost":  25000.0, "average_length_of_stay": 1},
    {"name": "Thyroid Surgery",      "base_cost":  65000.0, "average_length_of_stay": 3},
]

RISK_CONDITIONS = [
    {"name": "diabetes",      "cost_multiplier": 0.08, "complication_multiplier": 0.08},
    {"name": "hypertension",  "cost_multiplier": 0.04, "complication_multiplier": 0.04},
    {"name": "smoking",       "cost_multiplier": 0.06, "complication_multiplier": 0.06},
    {"name": "age_above_60",  "cost_multiplier": 0.05, "complication_multiplier": 0.05},
]


def seed(client: Client) -> None:
    """Seed hospitals, procedures, and risk conditions. Safe to run on every startup."""
    # ── Hospitals ────────────────────────────────────────────────────────────
    existing: dict = {}
    for row in (client.table("hospitals").select("id,name").execute().data or []):
        if row["name"] not in existing:
            existing[row["name"]] = row

    to_insert = []
    for h in HOSPITALS:
        if h["name"] in existing:
            row_id = existing[h["name"]]["id"]
            try:
                client.table("hospitals").update({
                    "accepts_insurance":      h["accepts_insurance"],
                    "insurance_coverage_pct": h["insurance_coverage_pct"],
                }).eq("id", row_id).execute()
            except Exception:
                pass
        else:
            to_insert.append(h)

    if to_insert:
        client.table("hospitals").insert(to_insert).execute()
        print(f"  [OK] Inserted {len(to_insert)} new hospital(s).")

    updated = len(HOSPITALS) - len(to_insert)
    print(f"  [OK] Hospitals seeded: {updated} updated, {len(to_insert)} inserted.")

    # ── Procedures ─────────────────────────────────────────────────────────
    client.table("procedures").upsert(PROCEDURES, on_conflict="name").execute()
    print(f"  [OK] Procedures upserted ({len(PROCEDURES)} total).")

    # ── Risk Conditions ────────────────────────────────────────────────────
    client.table("risk_conditions").upsert(RISK_CONDITIONS, on_conflict="name").execute()
    print(f"  [OK] Risk conditions upserted ({len(RISK_CONDITIONS)} total).")

    print("  Seeding complete.")
