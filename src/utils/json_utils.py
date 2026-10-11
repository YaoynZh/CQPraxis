import json
from typing import Any

from src.errors import JSONParseError


def extract_json_payload(raw_text: str) -> Any:
    text = raw_text.strip()
    if not text:
        raise JSONParseError("Model output is empty.")

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for start_token, end_token in (("{", "}"), ("[", "]")):
        start = text.find(start_token)
        end = text.rfind(end_token)
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise JSONParseError("Model output is not valid JSON.")


def dumps_compact(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
