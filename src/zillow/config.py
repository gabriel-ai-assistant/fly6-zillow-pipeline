from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = Path('/home/gabriel/fly6_data/zillow')


def _manual_load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_env() -> None:
    env_path = REPO_ROOT / '.env'
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(env_path, override=False)
    except Exception:
        _manual_load_dotenv(env_path)


load_env()

DATA_ROOT = Path(os.getenv('ZILLOW_DATA_ROOT', str(DEFAULT_DATA_ROOT))).expanduser()
DB_PATH = Path(os.getenv('ZILLOW_DB_PATH', str(DATA_ROOT / 'db' / 'zillow.sqlite'))).expanduser()
_default_repo_datasets = REPO_ROOT / 'fly6_data' / 'zillow' / 'datasets.yml'
DATASETS_YML_PATH = Path(os.getenv('ZILLOW_DATASETS_YML', str(_default_repo_datasets))).expanduser()
if not DATASETS_YML_PATH.exists():
    DATASETS_YML_PATH = DATA_ROOT / 'datasets.yml'

RAW_DIR = DATA_ROOT / 'raw'
GEO_DIR = DATA_ROOT / 'geo'
LOGS_DIR = DATA_ROOT / 'logs'
API_PORT = int(os.getenv('API_PORT', '8471'))


def ensure_data_dirs() -> None:
    for path in (DATA_ROOT, DB_PATH.parent, RAW_DIR, GEO_DIR, LOGS_DIR):
        path.mkdir(parents=True, exist_ok=True)
