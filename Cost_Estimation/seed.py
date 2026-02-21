from supabase import Client


HOSPITALS = [
    {"name": "Ruby Hall Clinic", "city": "Pune", "base_cost": 50000.0, "success_rate": 0.92, "base_complication_rate": 0.05, "average_recovery_days": 5, "room_cost_per_day": 3500.0},
    {"name": "Sahyadri Super Speciality Hospital", "city": "Pune", "base_cost": 45000.0, "success_rate": 0.89, "base_complication_rate": 0.06, "average_recovery_days": 6, "room_cost_per_day": 3000.0},
    {"name": "Jehangir Hospital", "city": "Pune", "base_cost": 55000.0, "success_rate": 0.94, "base_complication_rate": 0.04, "average_recovery_days": 4, "room_cost_per_day": 4000.0},
    {"name": "KEM Hospital", "city": "Pune", "base_cost": 30000.0, "success_rate": 0.85, "base_complication_rate": 0.08, "average_recovery_days": 7, "room_cost_per_day": 2000.0},
    {"name": "Deenanath Mangeshkar Hospital", "city": "Pune", "base_cost": 48000.0, "success_rate": 0.91, "base_complication_rate": 0.055, "average_recovery_days": 5, "room_cost_per_day": 3200.0},
]

PROCEDURES = [
    # Orthopaedic
    {"name": "Knee Replacement",        "base_cost": 120000.0, "average_length_of_stay": 5},
    {"name": "Hip Replacement",         "base_cost": 130000.0, "average_length_of_stay": 6},
    {"name": "Spinal Surgery",          "base_cost": 150000.0, "average_length_of_stay": 7},
    # General Surgery
    {"name": "Gallbladder Surgery",     "base_cost":  60000.0, "average_length_of_stay": 3},
    {"name": "Appendectomy",            "base_cost":  45000.0, "average_length_of_stay": 3},
    {"name": "Hernia Repair",           "base_cost":  55000.0, "average_length_of_stay": 2},
    # Cardiac
    {"name": "Angioplasty",             "base_cost": 180000.0, "average_length_of_stay": 4},
    {"name": "Bypass Surgery",          "base_cost": 300000.0, "average_length_of_stay": 10},
    # Gynaecology
    {"name": "C-section",               "base_cost":  50000.0, "average_length_of_stay": 4},
    {"name": "Hysterectomy",            "base_cost":  80000.0, "average_length_of_stay": 5},
    # ENT
    {"name": "Tonsillectomy",           "base_cost":  30000.0, "average_length_of_stay": 2},
    # Urology
    {"name": "Kidney Stone Removal",    "base_cost":  70000.0, "average_length_of_stay": 3},
    {"name": "Prostate Surgery",        "base_cost":  90000.0, "average_length_of_stay": 5},
    # Ophthalmology
    {"name": "Cataract Surgery",        "base_cost":  25000.0, "average_length_of_stay": 1},
    # Thyroid
    {"name": "Thyroid Surgery",         "base_cost":  65000.0, "average_length_of_stay": 3},
]

RISK_CONDITIONS = [
    {"name": "diabetes", "cost_multiplier": 0.08, "complication_multiplier": 0.08},
    {"name": "hypertension", "cost_multiplier": 0.04, "complication_multiplier": 0.04},
    {"name": "smoking", "cost_multiplier": 0.06, "complication_multiplier": 0.06},
    {"name": "age_above_60", "cost_multiplier": 0.05, "complication_multiplier": 0.05},
]


def seed(client: Client) -> None:
    # ── Hospitals (insert once) ─────────────────────────────────────────────
    existing_hospitals = client.table("hospitals").select("id").execute().data
    if not existing_hospitals:
        client.table("hospitals").insert(HOSPITALS).execute()
        print("  ✓ Seeded hospitals.")
    else:
        print("  · Hospitals already seeded, skipping.")

    # ── Procedures (upsert by name — adds new ones automatically) ──────────
    client.table("procedures").upsert(PROCEDURES, on_conflict="name").execute()
    print(f"  ✓ Procedures upserted ({len(PROCEDURES)} total).")

    # ── Risk Conditions (upsert by name) ────────────────────────────────────
    client.table("risk_conditions").upsert(RISK_CONDITIONS, on_conflict="name").execute()
    print(f"  ✓ Risk conditions upserted ({len(RISK_CONDITIONS)} total).")

    print("Seeding complete.")


if __name__ == "__main__":
    from database import get_db
    print("Running seed script…")
    seed(get_db())
