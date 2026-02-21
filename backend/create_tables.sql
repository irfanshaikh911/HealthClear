-- ============================================================
-- Run this SQL in your Supabase Dashboard → SQL Editor
-- ============================================================

-- 1. Bills
CREATE TABLE IF NOT EXISTS public.bills (
    id                 SERIAL NOT NULL,
    bill_uuid          CHARACTER VARYING(36) NOT NULL,
    user_id            INTEGER NULL,
    original_filename  CHARACTER VARYING(255) NOT NULL,
    file_path          CHARACTER VARYING(500) NOT NULL,
    file_type          CHARACTER VARYING(10) NOT NULL,
    hospital_name      CHARACTER VARYING(200) NULL,
    patient_name       CHARACTER VARYING(150) NULL,
    patient_age        INTEGER NULL,
    patient_gender     CHARACTER VARYING(10) NULL,
    ward_type          CHARACTER VARYING(50) NULL,
    admission_date     CHARACTER VARYING(30) NULL,
    discharge_date     CHARACTER VARYING(30) NULL,
    doctor_name        CHARACTER VARYING(150) NULL,
    total_billed       DOUBLE PRECISION NULL,
    taxes_billed       DOUBLE PRECISION NULL,
    discount_applied   DOUBLE PRECISION NULL,
    net_payable        DOUBLE PRECISION NULL,
    raw_extracted_json JSON NULL,
    status             CHARACTER VARYING(20) NULL,
    uploaded_at        TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    processed_at       TIMESTAMP WITH TIME ZONE NULL,
    CONSTRAINT bills_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;

CREATE UNIQUE INDEX IF NOT EXISTS ix_bills_bill_uuid
    ON public.bills USING btree (bill_uuid) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS ix_bills_id
    ON public.bills USING btree (id) TABLESPACE pg_default;

-- 2. Hospitals
CREATE TABLE IF NOT EXISTS public.hospitals (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    city            TEXT NOT NULL,
    state           TEXT,
    tier            TEXT DEFAULT 'Tier2',
    registration_no TEXT UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Standard Prices
CREATE TABLE IF NOT EXISTS public.standard_prices (
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

CREATE INDEX IF NOT EXISTS idx_standard_prices_item_name
    ON public.standard_prices(item_name);

-- 4. Bill Line Items
CREATE TABLE IF NOT EXISTS public.bill_line_items (
    id            BIGSERIAL PRIMARY KEY,
    bill_id       INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
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
CREATE TABLE IF NOT EXISTS public.verification_reports (
    id                 BIGSERIAL PRIMARY KEY,
    bill_id            INTEGER NOT NULL UNIQUE REFERENCES bills(id) ON DELETE CASCADE,
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
    findings_json      JSON,
    summary_text       TEXT,
    recommendations    TEXT,
    generated_at       TIMESTAMPTZ DEFAULT NOW()
);
