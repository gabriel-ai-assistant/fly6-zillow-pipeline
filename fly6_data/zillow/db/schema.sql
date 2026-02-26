CREATE TABLE IF NOT EXISTS series_meta (
  series_key TEXT PRIMARY KEY,
  category TEXT,
  geo_level TEXT,
  unit TEXT,
  series_name TEXT,
  required_for TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  source_url TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zillow_facts (
  series_key TEXT NOT NULL,
  geo_level TEXT NOT NULL,
  region_id TEXT NOT NULL,
  region_name TEXT,
  date TEXT NOT NULL,
  value REAL,
  flagged INTEGER NOT NULL DEFAULT 0,
  run_date TEXT,
  PRIMARY KEY (series_key, geo_level, region_id, date)
);

CREATE TABLE IF NOT EXISTS zip_cbsa (
  zip TEXT NOT NULL,
  cbsa TEXT NOT NULL,
  cbsa_name TEXT,
  state TEXT,
  res_ratio REAL,
  bus_ratio REAL,
  oth_ratio REAL,
  PRIMARY KEY (zip, cbsa)
);

CREATE TABLE IF NOT EXISTS run_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  details TEXT
);

CREATE VIEW IF NOT EXISTS v_ltr_zip_latest AS
SELECT
  z.region_id AS zip,
  z.region_name,
  z.date AS zhvi_date,
  z.value AS zhvi,
  r.date AS zori_date,
  r.value AS zori,
  CASE WHEN z.value > 0 AND r.value IS NOT NULL
    THEN (r.value * 12.0) / z.value ELSE NULL END AS gross_yield,
  z.flagged AS zhvi_flagged,
  r.flagged AS zori_flagged
FROM zillow_facts z
LEFT JOIN zillow_facts r
  ON r.region_id = z.region_id
  AND r.series_key IN ('zori_zip_allhomes','zori_zip_sfr')
  AND r.date = (SELECT MAX(date) FROM zillow_facts WHERE series_key = r.series_key AND region_id = r.region_id)
WHERE z.series_key IN ('zhvi_zip_allhomes','zhvi_zip_sfr')
  AND z.date = (SELECT MAX(date) FROM zillow_facts WHERE series_key = z.series_key AND region_id = z.region_id);

CREATE VIEW IF NOT EXISTS v_flip_metro_latest AS
SELECT
  f.region_id AS cbsa,
  f.region_name AS metro_name,
  MAX(CASE WHEN f.series_key = 'sale_to_list_metro' THEN f.value END) AS sale_to_list,
  MAX(CASE WHEN f.series_key = 'market_temp_metro' THEN f.value END) AS market_heat,
  MAX(CASE WHEN f.series_key = 'price_cuts_metro' THEN f.value END) AS price_cut_pct,
  MAX(CASE WHEN f.series_key = 'inv_metro' THEN f.value END) AS inventory,
  MAX(CASE WHEN f.series_key = 'days_pending_metro' THEN f.value END) AS days_to_pending,
  MAX(CASE WHEN f.series_key = 'days_close_metro' THEN f.value END) AS days_to_close,
  MAX(CASE WHEN f.series_key = 'new_listings_metro' THEN f.value END) AS new_listings,
  MAX(CASE WHEN f.series_key = 'median_list_price_metro' THEN f.value END) AS median_list_price
FROM zillow_facts f
WHERE f.date = (SELECT MAX(date) FROM zillow_facts WHERE series_key = f.series_key AND region_id = f.region_id)
GROUP BY f.region_id, f.region_name;
