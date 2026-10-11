from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Sequence

from src.errors import SchemaValidationError


ALLOWED_TASK_TYPES = ("A", "B", "C")
ALLOWED_CQ_TAGS = ("metacognitive", "cognitive", "motivational", "behavioural")
ALLOWED_DIFFICULTIES = ("easy", "medium", "hard")


class SchemaMixin:
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def ensure_mapping(name: str, value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaValidationError(f"{name} must be an object.")
    return value


def ensure_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(f"{name} must be a non-empty string.")
    return value.strip()


def ensure_int(name: str, value: Any, min_value: int = None, max_value: int = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaValidationError(f"{name} must be an integer.")
    if min_value is not None and value < min_value:
        raise SchemaValidationError(f"{name} must be >= {min_value}.")
    if max_value is not None and value > max_value:
        raise SchemaValidationError(f"{name} must be <= {max_value}.")
    return value


def ensure_list(name: str, value: Any) -> List[Any]:
    if not isinstance(value, list) or not value:
        raise SchemaValidationError(f"{name} must be a non-empty list.")
    return value


def ensure_string_list(name: str, value: Any, allowed: Sequence[str] = ()) -> List[str]:
    items = ensure_list(name, value)
    cleaned = [ensure_string(f"{name}[]", item) for item in items]
    if allowed:
        invalid = [item for item in cleaned if item not in allowed]
        if invalid:
            raise SchemaValidationError(f"{name} contains unsupported values: {invalid}")
    return cleaned


def ensure_single_cq(name: str, value: Any) -> List[str]:
    tags = ensure_string_list(name, value, allowed=ALLOWED_CQ_TAGS)
    if len(tags) != 1:
        raise SchemaValidationError(f"{name} must contain exactly one CQ tag.")
    return tags


def ensure_difficulty(name: str, value: Any) -> str:
    difficulty = ensure_string(name, value)
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise SchemaValidationError(f"{name} must be one of {ALLOWED_DIFFICULTIES}.")
    return difficulty


def require_keys(data: Dict[str, Any], keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise SchemaValidationError(f"Missing required fields: {missing}")
