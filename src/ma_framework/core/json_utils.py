import json
import re

def safe_json_loads(text: str) -> dict:
    if not text or not text.strip():
        raise json.JSONDecodeError("Empty model output", text or "", 0)

    cleaned = re.sub(r"```[a-zA-Z0-9_-]*\s*|\s*```", "", text).strip()

    return json.loads(cleaned)
