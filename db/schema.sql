-- =============================================================================
-- Supabase SQL Schema
-- Run this in your Supabase SQL Editor (Database → SQL Editor → New Query)
-- =============================================================================

-- 1. decisions — stores every ordering decision made by the agent
CREATE TABLE IF NOT EXISTS decisions (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    drug_col        TEXT        NOT NULL,
    units_ordered   NUMERIC     NOT NULL,
    predicted_surge BOOLEAN     NOT NULL,
    confidence      NUMERIC     NOT NULL,
    anomaly_detected BOOLEAN    NOT NULL DEFAULT FALSE,
    reasoning       TEXT,
    status          TEXT        NOT NULL DEFAULT 'executed'  -- 'executed' | 'pending' | 'rejected'
);

-- 2. outcomes — records whether a decision was correct (for adaptive memory)
CREATE TABLE IF NOT EXISTS outcomes (
    id              BIGSERIAL PRIMARY KEY,
    decision_id     BIGINT      REFERENCES decisions(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actual_surge    BOOLEAN,
    stock_out       BOOLEAN     DEFAULT FALSE,
    overstock_pct   NUMERIC,
    notes           TEXT
);

-- 3. pending_approvals — high-value orders awaiting manager sign-off
CREATE TABLE IF NOT EXISTS pending_approvals (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    drug_col        TEXT        NOT NULL,
    units_ordered   NUMERIC     NOT NULL,
    estimated_cost  NUMERIC     NOT NULL,
    plan_json       JSONB,
    status          TEXT        NOT NULL DEFAULT 'pending',  -- 'pending' | 'approved' | 'rejected'
    reviewed_at     TIMESTAMPTZ,
    reviewer_note   TEXT
);

-- Enable Row-Level Security (optional but recommended)
ALTER TABLE decisions         ENABLE ROW LEVEL SECURITY;
ALTER TABLE outcomes          ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_approvals ENABLE ROW LEVEL SECURITY;
