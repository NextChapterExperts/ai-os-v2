-- Phase 0 — Platform DB bootstrap (P17 + Scheduler/Skills/Checkpoints)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Audit log (v1-ähnlich + Hash-Chain P17)
CREATE TABLE IF NOT EXISTS ai_os_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id VARCHAR NOT NULL,
  event_type VARCHAR NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}',
  prev_hash CHAR(64),
  entry_hash CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_aioslog_tenant_created
  ON ai_os_log (tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_aioslog_chain
  ON ai_os_log (tenant_id, created_at);

CREATE TABLE IF NOT EXISTS schedule_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  cron_expr VARCHAR NOT NULL,
  workflow_name VARCHAR NOT NULL,
  delivery_channels JSONB DEFAULT '[]',
  last_run_at TIMESTAMPTZ,
  next_run_at TIMESTAMPTZ,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_checkpoints (
  thread_id VARCHAR NOT NULL,
  checkpoint_id VARCHAR NOT NULL,
  parent_id VARCHAR,
  type VARCHAR,
  checkpoint BYTEA,
  metadata JSONB,
  PRIMARY KEY (thread_id, checkpoint_id)
);

CREATE TABLE IF NOT EXISTS skills (
  id VARCHAR PRIMARY KEY,
  tenant_id VARCHAR NOT NULL,
  title VARCHAR NOT NULL,
  description TEXT,
  file_path VARCHAR NOT NULL,
  version INT DEFAULT 1,
  success_rate FLOAT,
  use_count INT DEFAULT 0,
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_skills_tenant ON skills (tenant_id);
CREATE INDEX IF NOT EXISTS idx_skills_fts
  ON skills USING gin (to_tsvector('german', coalesce(title, '') || ' ' || coalesce(description, '')));

CREATE TABLE IF NOT EXISTS run_receipts (
  run_id UUID PRIMARY KEY,
  tenant_id VARCHAR NOT NULL,
  workflow_name VARCHAR NOT NULL,
  cost_micro_usd BIGINT DEFAULT 0,
  model_calls JSONB DEFAULT '[]',
  permission_scopes JSONB DEFAULT '[]',
  cloud_escalations JSONB DEFAULT '[]',
  chain_hash CHAR(64) NOT NULL,
  signature TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_receipts_tenant
  ON run_receipts (tenant_id, created_at);
