import json
from datetime import datetime
from pathlib import Path

RUNS_DIR = Path("generated/runs")

def new_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def save_run(run_id: str, payload: dict) -> str:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / f"{run_id}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(out_path)