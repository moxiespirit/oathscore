-- OathScore initial schema
-- Run this in Supabase SQL Editor

CREATE TABLE pings (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  status_code INT,
  latency_ms INT,
  ok BOOLEAN DEFAULT TRUE,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE schema_snapshots (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  schema_hash TEXT NOT NULL,
  changed BOOLEAN DEFAULT FALSE,
  response_schema JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE freshness_checks (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  data_timestamp TEXT,
  age_seconds INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE docs_checks (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  found TEXT[],
  missing TEXT[],
  docs_accessible BOOLEAN DEFAULT FALSE,
  score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE forecast_snapshots (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  forecast_date DATE,
  forecast_value FLOAT,
  actual_value FLOAT,
  accuracy_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE daily_scores (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  score_date DATE NOT NULL,
  composite_score FLOAT,
  accuracy_score FLOAT,
  uptime_score FLOAT,
  freshness_score FLOAT,
  latency_score FLOAT,
  schema_score FLOAT,
  docs_score FLOAT,
  trust_score FLOAT,
  grade TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(api_name, score_date)
);

-- Indexes for common queries
CREATE INDEX idx_pings_api_time ON pings(api_name, created_at DESC);
CREATE INDEX idx_schemas_api ON schema_snapshots(api_name, created_at DESC);
CREATE INDEX idx_freshness_api ON freshness_checks(api_name, created_at DESC);
CREATE INDEX idx_scores_api_date ON daily_scores(api_name, score_date DESC);

-- Enable Row Level Security (allow anonymous reads)
ALTER TABLE pings ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE freshness_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecast_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_scores ENABLE ROW LEVEL SECURITY;

-- Policies: anon can read, service_role can write
CREATE POLICY "anon_read_pings" ON pings FOR SELECT USING (true);
CREATE POLICY "anon_read_schemas" ON schema_snapshots FOR SELECT USING (true);
CREATE POLICY "anon_read_freshness" ON freshness_checks FOR SELECT USING (true);
CREATE POLICY "anon_read_docs" ON docs_checks FOR SELECT USING (true);
CREATE POLICY "anon_read_forecasts" ON forecast_snapshots FOR SELECT USING (true);
CREATE POLICY "anon_read_scores" ON daily_scores FOR SELECT USING (true);

-- Service role insert policies
CREATE POLICY "service_insert_pings" ON pings FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_schemas" ON schema_snapshots FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_freshness" ON freshness_checks FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_docs" ON docs_checks FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_forecasts" ON forecast_snapshots FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_scores" ON daily_scores FOR INSERT WITH CHECK (true);
