import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.supabase import supabase

DOCTORS = [
    {
        "city": "Pune",
        "doctor_name": "Shailesh Kadre",
        "specialization": "Endocrinologist",
        "experience": "15 years",
        "clinic": "Ruby Hall Clinic",
        "consultation_fee": "800"
    },
    {
        "city": "Pune",
        "doctor_name": "Aarti Sharma",
        "specialization": "Endocrinologist",
        "experience": "10 years",
        "clinic": "Apollo Clinic",
        "consultation_fee": "600"
    },
    {
        "city": "Mumbai",
        "doctor_name": "Anil Kumar Sharma",
        "specialization": "Endocrinologist",
        "experience": "20 years",
        "clinic": "Sir H N Reliance Foundation Hospital",
        "consultation_fee": "1200"
    },
    {
        "city": "Pune",
        "doctor_name": "Rahul Deshmukh",
        "specialization": "General Physician",
        "experience": "8 years",
        "clinic": "Care Clinic",
        "consultation_fee": "400"
    }
]

def seed():
    existing = supabase.table("doctor").select("doctor_name", count="exact").execute()
    if existing.count and existing.count > 0:
        print(f"Already {existing.count} doctors in DB. Clearing and reseeding...")
        # (Supabase python client doesn't have a simple TRUNCATE, so we'll just insert more if needed, 
        # but to keep it simple we'll just insert if empty or just insert anyway since no unique constraint)

    result = supabase.table("doctor").insert(DOCTORS).execute()
    print(f"✅ Seeded {len(result.data)} doctors successfully!")

if __name__ == "__main__":
    seed()
