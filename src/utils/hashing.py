import hashlib
from typing import Any, Dict, Iterable

from src.utils.json_utils import dumps_compact


def stable_hash(payload: Dict[str, Any], keys: Iterable[str] = ()) -> str:
    if keys:
        filtered = {key: payload.get(key) for key in keys}
    else:
        filtered = payload
    return hashlib.sha256(dumps_compact(filtered).encode("utf-8")).hexdigest()
