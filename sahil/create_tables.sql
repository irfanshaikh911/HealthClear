-- ============================================================
-- Run this SQL in your Supabase Dashboard → SQL Editor
-- ============================================================

-- 1. Hospitals
CREATE TABLE IF NOT EXISTS hospitals (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT NOT NULL,
    state       TEXT,
    tier        TEXT DEFAULT 'Tier2',
    registration_no TEXT UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Standard Prices
CREATE TABLE IF NOT EXISTS standard_prices (
    id          BIGSERIAL PRIMARY KEY,
    hospital_id BIGINT REFERENCES hospitals(id) ON DELETE SET NULL,
    item_name   TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit        TEXT DEFAULT 'per day',
    min_price   DOUBLE PRECISION NOT NULL,
    max_price   DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_standard_prices_item_name ON standard_prices(item_name);

-- 3. Bills
CREATE TABLE IF NOT EXISTS bills (
    id                 BIGSERIAL PRIMARY KEY,
    bill_uuid          TEXT UNIQUE NOT NULL,
    original_filename  TEXT NOT NULL,
    file_path          TEXT NOT NULL,
    file_type          TEXT NOT NULL,
    hospital_name      TEXT,
    patient_name       TEXT,
    patient_age        INTEGER,
    patient_gender     TEXT,
    ward_type          TEXT,
    admission_date     TEXT,
    discharge_date     TEXT,
    doctor_name        TEXT,
    total_billed       DOUBLE PRECISION,
    taxes_billed       DOUBLE PRECISION,
    discount_applied   DOUBLE PRECISION DEFAULT 0,
    net_payable        DOUBLE PRECISION,
    raw_extracted_json JSONB,
    status             TEXT DEFAULT 'PENDING',
    uploaded_at        TIMESTAMPTZ DEFAULT NOW(),
    processed_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_bills_bill_uuid ON bills(bill_uuid);

-- 4. Bill Line Items
CREATE TABLE IF NOT EXISTS bill_line_items (
    id            BIGSERIAL PRIMARY KEY,
    bill_id       BIGINT NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    item_name     TEXT NOT NULL,
    category      TEXT,
    quantity      DOUBLE PRECISION DEFAULT 1,
    unit          TEXT,
    unit_price    DOUBLE PRECISION NOT NULL,
    total_price   DOUBLE PRECISION NOT NULL,
    gst_percent   DOUBLE PRECISION,
    flag          TEXT,
    standard_min  DOUBLE PRECISION,
    standard_max  DOUBLE PRECISION,
    excess_amount DOUBLE PRECISION,
    severity      TEXT
);

-- 5. Verification Reports
CREATE TABLE IF NOT EXISTS verification_reports (
    id                 BIGSERIAL PRIMARY KEY,
    bill_id            BIGINT NOT NULL UNIQUE REFERENCES bills(id) ON DELETE CASCADE,
    verdict            TEXT NOT NULL,
    trust_score        INTEGER NOT NULL,
    total_billed       DOUBLE PRECISION,
    estimated_fair     DOUBLE PRECISION,
    total_overcharge   DOUBLE PRECISION,
    overcharge_percent DOUBLE PRECISION,
    total_items        INTEGER DEFAULT 0,
    flagged_items      INTEGER DEFAULT 0,
    overcharged_items  INTEGER DEFAULT 0,
    duplicate_items    INTEGER DEFAULT 0,
    math_error_items   INTEGER DEFAULT 0,
    unknown_items      INTEGER DEFAULT 0,
    findings_json      JSONB,
    summary_text       TEXT,
    recommendations    TEXT,
    generated_at       TIMESTAMPTZ DEFAULT NOW()
);
