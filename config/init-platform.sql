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

-- Knowledge Graph (Company Brain, Phase 2 — siehe docs/09-COMPANY-BRAIN.md)
-- Relationales KG: Knoten + Kanten, kein Neo4j/AGE (P-Prinzip: kein Fach-Agent
-- mit eigenem Graph-Store). Ein Knoten = ein org:*/platform:*-Typ + external_id
-- pro Tenant; Upsert nur ueber den DP-Service (POST /v1/dataproduct/commit).
CREATE TABLE IF NOT EXISTS kg_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id VARCHAR NOT NULL,
  node_type VARCHAR NOT NULL,
  external_id VARCHAR NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}',
  k_path VARCHAR,
  dp_id UUID,
  produced_by VARCHAR NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, node_type, external_id)
);
CREATE INDEX IF NOT EXISTS idx_kgnodes_tenant_type ON kg_nodes (tenant_id, node_type);

CREATE TABLE IF NOT EXISTS kg_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id VARCHAR NOT NULL,
  edge_type VARCHAR NOT NULL,
  from_node_id UUID NOT NULL REFERENCES kg_nodes (id) ON DELETE CASCADE,
  to_node_id UUID NOT NULL REFERENCES kg_nodes (id) ON DELETE CASCADE,
  payload JSONB NOT NULL DEFAULT '{}',
  produced_by VARCHAR NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, edge_type, from_node_id, to_node_id)
);
CREATE INDEX IF NOT EXISTS idx_kgedges_tenant_type ON kg_edges (tenant_id, edge_type);
CREATE INDEX IF NOT EXISTS idx_kgedges_from ON kg_edges (from_node_id);
CREATE INDEX IF NOT EXISTS idx_kgedges_to ON kg_edges (to_node_id);

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
