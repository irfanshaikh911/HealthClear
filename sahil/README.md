# 🏥 Bill Verification System
AI-powered hospital bill verification using **FastAPI + Gemini 1.5 Flash + PostgreSQL**

---

## 📁 Project Structure

```
bill-verification-system/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/routes/
│   │   ├── auth.py                # Register / Login / Me
│   │   ├── bills.py               # Upload / Report / Status / History
│   │   └── admin.py               # Manage hospitals & standard prices
│   ├── core/
│   │   ├── config.py              # Settings from .env
│   │   └── security.py            # JWT auth
│   ├── db/
│   │   └── database.py            # SQLAlchemy engine & session
│   ├── models/
│   │   ├── user.py                # User table
│   │   ├── hospital.py            # Hospital + StandardPrice tables
│   │   └── bill.py                # Bill + LineItems + Report tables
│   ├── schemas/
│   │   └── schemas.py             # All Pydantic models
│   └── services/
│       ├── gemini_service.py      # Gemini 1.5 Flash OCR extraction
│       ├── file_service.py        # File upload handler
│       ├── verification_engine.py # Core price comparison logic
│       └── bill_service.py        # Full pipeline orchestrator
├── seed_prices.py                 # One-time DB seed for standard prices
├── requirements.txt
└── .env.example
```

---

## ⚡ Setup

### 1. Clone & install dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup PostgreSQL
```sql
CREATE DATABASE bill_verification;
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in:
# - DATABASE_URL
# - GEMINI_API_KEY  (get free at https://aistudio.google.com)
# - SECRET_KEY
```

### 4. Seed the standard price database
```bash
python seed_prices.py
```

### 5. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Open API docs
```
http://localhost:8000/docs
```

---

## 🔄 API Flow

```
POST /api/auth/register     → Create account
POST /api/auth/login        → Get JWT token

POST /api/bills/upload      → Upload JPG/JPEG/PDF bill (with Bearer token)
                              → Returns bill_uuid immediately
                              → Processing happens in background

GET  /api/bills/status/{bill_uuid}   → Check processing status
GET  /api/bills/report/{bill_uuid}   → Get full verification report
GET  /api/bills/history              → View all past bills

# Admin only
POST /api/admin/hospitals            → Add hospital
POST /api/admin/prices               → Add standard price
POST /api/admin/prices/bulk          → Bulk seed prices
```

---

## 📊 Report Verdict Guide

| Verdict | Trust Score | Meaning |
|---|---|---|
| ✅ CLEAN | 80–100 | All items within standard range |
| ⚠️ SUSPICIOUS | 40–79 | Some overcharges or duplicates found |
| 🚨 FRAUDULENT | 0–39 | Major overcharges, math errors, or duplicates |

---

## 🚩 Verification Checks

| Flag | Description |
|---|---|
| `OK` | Price within standard range |
| `OVERCHARGED` | Unit price > standard maximum by >10% |
| `DUPLICATE` | Same item appears more than once |
| `MATH_ERROR` | qty × unit_price ≠ total_price |
| `UNKNOWN` | Item not found in standard price DB |

---

## 📄 Sample Report Response

```json
{
  "bill_uuid": "abc-123",
  "verdict": "SUSPICIOUS",
  "trust_score": 62,
  "total_billed": 85000,
  "estimated_fair_price": 52000,
  "total_overcharge": 33000,
  "overcharge_percent": 38.8,
  "total_items": 12,
  "flagged_items": 3,
  "findings": [
    {
      "item_name": "ICU Bed",
      "billed_unit_price": 25000,
      "standard_max": 15000,
      "flag": "OVERCHARGED",
      "severity": "HIGH",
      "excess_amount": 30000,
      "remark": "Billed ₹25000/day but standard max is ₹15000/day. Excess: ₹30000."
    }
  ],
  "summary": "⚠️ Bill has 3 suspicious items. Estimated overcharge: ₹33000 (38.8%)",
  "recommendations": "1. Request itemized justification from hospital..."
}
```

---

## 🔑 Getting Gemini API Key (Free)

1. Go to [https://aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key**
3. Copy key → paste in `.env` as `GEMINI_API_KEY`

**Free tier:** 1500 requests/day — sufficient for most use cases.
