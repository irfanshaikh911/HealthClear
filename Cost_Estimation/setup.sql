-- ============================================================
-- Healthcare Cost Estimation Platform — Supabase Table Setup
-- Run this in Supabase Dashboard → SQL Editor before starting
-- ============================================================

-- Hospitals table
CREATE TABLE IF NOT EXISTS hospitals (
    id                      SERIAL PRIMARY KEY,
    name                    TEXT NOT NULL,
    city                    TEXT NOT NULL,
    base_cost               NUMERIC NOT NULL,
    success_rate            NUMERIC NOT NULL,
    base_complication_rate  NUMERIC NOT NULL,
    average_recovery_days   INTEGER NOT NULL,
    room_cost_per_day       NUMERIC NOT NULL,
    accepts_insurance       BOOLEAN NOT NULL DEFAULT TRUE,
    insurance_coverage_pct  NUMERIC NOT NULL DEFAULT 0.0
);

-- Procedures table
CREATE TABLE IF NOT EXISTS procedures (
    id                      SERIAL PRIMARY KEY,
    name                    TEXT NOT NULL UNIQUE,
    base_cost               NUMERIC NOT NULL,
    average_length_of_stay  INTEGER NOT NULL
);

-- Risk conditions table
CREATE TABLE IF NOT EXISTS risk_conditions (
    name                    TEXT PRIMARY KEY,
    cost_multiplier         NUMERIC NOT NULL,
    complication_multiplier NUMERIC NOT NULL
);

-- Chat history table (RAG chatbot conversation log)
CREATE TABLE IF NOT EXISTS chat_history (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL UNIQUE,
    patient_id      INTEGER,
    messages        JSONB NOT NULL DEFAULT '[]',
    answers         JSONB NOT NULL DEFAULT '{}',
    result          JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Migration: run if hospitals table already exists
-- ============================================================
ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS accepts_insurance      BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS insurance_coverage_pct NUMERIC NOT NULL DEFAULT 0.0;
