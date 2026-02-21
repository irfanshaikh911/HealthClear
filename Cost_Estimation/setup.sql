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
    room_cost_per_day       NUMERIC NOT NULL
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
