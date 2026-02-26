# Fly6 Zillow Pipeline

SQLite-first Zillow Research ingestion and underwriting API for LTR (ZIP) and flip (Metro) workflows.

## Architecture Overview

```text
                  +---------------------------+
                  |  Zillow datasets.yml      |
                  +-------------+-------------+
                                |
                                v
+-------------------+    +-------------+    +---------------------+
| src.zillow.cli    +--->+ SQLite DB   +<---+ zip_cbsa crosswalk  |
| init/verify/refresh|    | zillow.sqlite|   | zip -> cbsa mapping |
+---------+---------+    +------+------+    +----------+----------+
          |                       |                      |
          v                       v                      v
    logs/*.json           v_ltr_zip_latest       v_flip_metro_latest
                                  \              /
                                   \            /
                                    v          v
                                +------------------+
                                | FastAPI (/api)   |
                                | /profile /rank   |
                                | /similar /admin  |
                                +------------------+
```

## Quickstart

1. Clone repository
```bash
git clone https://github.com/gabriel-ai-assistant/fly6-zillow-pipeline.git
cd fly6-zillow-pipeline
```

2. Create runtime directories
```bash
mkdir -p /home/gabriel/fly6_data/zillow/{db,raw,geo,logs}
cp -n fly6_data/zillow/geo/zip_to_cbsa.csv /home/gabriel/fly6_data/zillow/geo/zip_to_cbsa.csv
cp -n fly6_data/zillow/datasets.yml /home/gabriel/fly6_data/zillow/datasets.yml
```

3. Create `.env`
```bash
cat > .env << 'ENVEOF'
ZILLOW_DATA_ROOT=/home/gabriel/fly6_data/zillow
ZILLOW_DB_PATH=/home/gabriel/fly6_data/zillow/db/zillow.sqlite
API_PORT=8471
ENVEOF
```

4. Build and run
```bash
docker compose build --no-cache
docker compose up -d
curl -s http://localhost:8471/health
```

## API Reference

Base URL: `http://localhost:8471`

### Health
```bash
curl -s http://localhost:8471/health
```

### Profile
```bash
curl -s "http://localhost:8471/profile/75069?strategy=both"
```

### Rank LTR
```bash
curl -s -X POST http://localhost:8471/rank/ltr \
  -H 'content-type: application/json' \
  -d '{"zips":["75069","94107","10001"],"zhvi_max":900000,"yield_min":0.02,"top_n":3}'
```

### Rank Flip Metros
```bash
curl -s -X POST http://localhost:8471/rank/flip-metros \
  -H 'content-type: application/json' \
  -d '{"cbsa_list":["19100","41860","35620"],"sort_by":"sale_to_list","top_n":3}'
```

### Select Flip Zips
```bash
curl -s -X POST http://localhost:8471/select-flip-zips \
  -H 'content-type: application/json' \
  -d '{"cbsa":"19100","zips_in_cbsa":["75069","94107"],"zhvi_min":250000,"zhvi_max":800000,"require_positive_zhvf":true,"top_n":5}'
```

### Similar Zips
```bash
curl -s -X POST http://localhost:8471/similar-zips \
  -H 'content-type: application/json' \
  -d '{"seed_zip":"75069","candidate_zips":["94107","10001","60614","80202"],"k":3}'
```

### Admin
```bash
curl -s -X POST http://localhost:8471/admin/refresh \
  -H 'content-type: application/json' \
  -d '{"mode":"both"}'

curl -s -X POST http://localhost:8471/admin/build-zip-cbsa
curl -s "http://localhost:8471/admin/verify-urls?mode=both"
curl -s "http://localhost:8471/admin/status?limit=20"
```

Interactive docs: `http://localhost:8471/docs`

## CLI Reference

```bash
python -m src.zillow.cli init
python -m src.zillow.cli build-zip-cbsa
python -m src.zillow.cli verify-urls --mode both
python -m src.zillow.cli refresh --mode both --date 2026-02-26
```

## Data Architecture

- LTR tier (ZIP-level): `zhvi_zip_allhomes`, `zori_zip_allhomes`
- Flip tier (Metro-level): `sale_to_list_metro`, `market_temp_metro`, `price_cuts_metro`, `inv_metro`, `days_pending_metro`
- ZIP selection for flip: ZIP proxy filters using `zhvi_zip_allhomes` and `zhvf_zip_allhomes`
- Mapping dependency: `zip_cbsa` table loaded from `geo/zip_to_cbsa.csv`

## Scheduling

Recommended cron schedule: monthly on the 20th.

```bash
0 4 20 * * cd /home/gabriel/fly6-zillow && docker exec zillow-pipeline python -m src.zillow.cli refresh --mode both --date $(date +\%F)
```

## Adding New Zillow Series

1. Add entry to `fly6_data/zillow/datasets.yml`.
2. Run `python -m src.zillow.cli init` to seed/update `series_meta`.
3. Extend parser/refresh logic to ingest that series into `zillow_facts`.
4. Update SQL views (`fly6_data/zillow/db/schema.sql`) if the series should appear in API outputs.
