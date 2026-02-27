CREATE TABLE IF NOT EXISTS series_meta (
  series_key TEXT PRIMARY KEY,
  category TEXT,
  geo_level TEXT,
  unit TEXT,
  series_name TEXT,
  required_for TEXT,
  enabled INTEGER DEFAULT 1,
  source_url TEXT,
  region_id_column TEXT,
  region_name_column TEXT,
  region_columns_json TEXT,
  date_column_regex TEXT,
  quality_rules_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS zillow_facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  series_key TEXT NOT NULL,
  geo_level TEXT NOT NULL,
  region_id TEXT NOT NULL,
  region_name TEXT,
  date TEXT NOT NULL,
  value REAL,
  flagged INTEGER DEFAULT 0,
  flag_reason TEXT,
  ingested_at TEXT DEFAULT (datetime('now')),
  UNIQUE(series_key, geo_level, region_id, date)
);

CREATE TABLE IF NOT EXISTS zip_cbsa (
  zip TEXT NOT NULL,
  cbsa TEXT NOT NULL,
  cbsa_name TEXT,
  state TEXT,
  res_ratio REAL,
  bus_ratio REAL,
  oth_ratio REAL,
  updated_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (zip, cbsa)
);

CREATE TABLE IF NOT EXISTS run_log (
  run_id TEXT NOT NULL,
  run_date TEXT NOT NULL,
  mode TEXT,
  series_key TEXT,
  status TEXT,
  rows_upserted INTEGER DEFAULT 0,
  rows_flagged INTEGER DEFAULT 0,
  error_msg TEXT,
  started_at TEXT,
  completed_at TEXT
);

-- Views (stubs - Agent 3 fills these)
-- v_ltr_zip_latest
-- v_flip_metro_latest

CREATE INDEX IF NOT EXISTS idx_facts_series_geo ON zillow_facts(series_key, geo_level);
CREATE INDEX IF NOT EXISTS idx_facts_region ON zillow_facts(region_id, series_key);
CREATE INDEX IF NOT EXISTS idx_facts_date ON zillow_facts(date);
