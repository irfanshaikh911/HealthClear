import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import supabase

PRICES = [
    {"item_name": "General Ward Bed",          "category": "BED",          "unit": "per day",     "min_price": 500,    "max_price": 2000},
    {"item_name": "Semi-Private Ward Bed",     "category": "BED",          "unit": "per day",     "min_price": 1500,   "max_price": 4000},
    {"item_name": "Private Ward Bed",          "category": "BED",          "unit": "per day",     "min_price": 3000,   "max_price": 8000},
    {"item_name": "ICU Bed",                   "category": "BED",          "unit": "per day",     "min_price": 5000,   "max_price": 15000},
    {"item_name": "NICU Bed",                  "category": "BED",          "unit": "per day",     "min_price": 6000,   "max_price": 18000},
    {"item_name": "HDU Bed",                   "category": "BED",          "unit": "per day",     "min_price": 3500,   "max_price": 9000},
    {"item_name": "Doctor Consultation",       "category": "CONSULTATION",  "unit": "per visit",  "min_price": 300,    "max_price": 1500},
    {"item_name": "Specialist Consultation",   "category": "CONSULTATION",  "unit": "per visit",  "min_price": 500,    "max_price": 3000},
    {"item_name": "Nursing Charges",           "category": "EQUIPMENT",     "unit": "per day",    "min_price": 200,    "max_price": 1000},
    {"item_name": "Diet Charges",              "category": "OTHER",         "unit": "per day",    "min_price": 150,    "max_price": 600},
    {"item_name": "Appendectomy",              "category": "PROCEDURE",     "unit": "one time",   "min_price": 40000,  "max_price": 100000},
    {"item_name": "Angioplasty",               "category": "PROCEDURE",     "unit": "one time",   "min_price": 100000, "max_price": 350000},
    {"item_name": "Normal Delivery",           "category": "PROCEDURE",     "unit": "one time",   "min_price": 15000,  "max_price": 50000},
    {"item_name": "C-Section",                 "category": "PROCEDURE",     "unit": "one time",   "min_price": 25000,  "max_price": 80000},
    {"item_name": "Endoscopy",                 "category": "PROCEDURE",     "unit": "one time",   "min_price": 3000,   "max_price": 8000},
    {"item_name": "Dialysis",                  "category": "PROCEDURE",     "unit": "per session","min_price": 1500,   "max_price": 4000},
    {"item_name": "Operation Theatre Charges", "category": "PROCEDURE",     "unit": "per hour",   "min_price": 5000,   "max_price": 20000},
    {"item_name": "Anaesthesia Charges",       "category": "PROCEDURE",     "unit": "per hour",   "min_price": 2000,   "max_price": 8000},
    {"item_name": "CBC Complete Blood Count",  "category": "LAB",           "unit": "per test",   "min_price": 200,    "max_price": 600},
    {"item_name": "Blood Culture",             "category": "LAB",           "unit": "per test",   "min_price": 800,    "max_price": 2000},
    {"item_name": "Lipid Profile",             "category": "LAB",           "unit": "per test",   "min_price": 400,    "max_price": 900},
    {"item_name": "Thyroid Profile",           "category": "LAB",           "unit": "per test",   "min_price": 500,    "max_price": 1200},
    {"item_name": "HbA1c",                     "category": "LAB",           "unit": "per test",   "min_price": 300,    "max_price": 700},
    {"item_name": "Urine Routine",             "category": "LAB",           "unit": "per test",   "min_price": 100,    "max_price": 300},
    {"item_name": "ECG",                       "category": "LAB",           "unit": "per test",   "min_price": 150,    "max_price": 500},
    {"item_name": "Echo Cardiography",         "category": "LAB",           "unit": "per test",   "min_price": 1500,   "max_price": 4000},
    {"item_name": "CT Scan Head",              "category": "LAB",           "unit": "per test",   "min_price": 3000,   "max_price": 8000},
    {"item_name": "MRI Brain",                 "category": "LAB",           "unit": "per test",   "min_price": 6000,   "max_price": 15000},
    {"item_name": "X-Ray Chest",               "category": "LAB",           "unit": "per test",   "min_price": 200,    "max_price": 600},
    {"item_name": "Ultrasound Abdomen",        "category": "LAB",           "unit": "per test",   "min_price": 500,    "max_price": 1500},
    {"item_name": "Ventilator Charges",        "category": "EQUIPMENT",     "unit": "per day",    "min_price": 3000,   "max_price": 10000},
    {"item_name": "Oxygen Charges",            "category": "EQUIPMENT",     "unit": "per day",    "min_price": 300,    "max_price": 1500},
    {"item_name": "IV Cannula",                "category": "EQUIPMENT",     "unit": "per piece",  "min_price": 30,     "max_price": 100},
    {"item_name": "Paracetamol 500mg",         "category": "MEDICINE",      "unit": "per tablet", "min_price": 1,      "max_price": 5},
    {"item_name": "Amoxicillin 500mg",         "category": "MEDICINE",      "unit": "per capsule","min_price": 5,      "max_price": 20},
    {"item_name": "Normal Saline 500ml",       "category": "MEDICINE",      "unit": "per bottle", "min_price": 40,     "max_price": 120},
    {"item_name": "Ringer Lactate 500ml",      "category": "MEDICINE",      "unit": "per bottle", "min_price": 40,     "max_price": 130},
]

def seed():
    # Check if already seeded
    existing = supabase.table("standard_prices").select("id", count="exact").execute()
    if existing.count and existing.count > 0:
        print(f"Already {existing.count} prices in DB. Skipping.")
        return

    # Insert all prices in one batch
    result = supabase.table("standard_prices").insert(PRICES).execute()
    print(f"✅ Seeded {len(result.data)} standard prices successfully!")

if __name__ == "__main__":
    seed()
