from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Union

from src.errors import SchemaValidationError
from src.models.base import (
    ALLOWED_TASK_TYPES,
    SchemaMixin,
    ensure_difficulty,
    ensure_int,
    ensure_list,
    ensure_mapping,
    ensure_single_cq,
    ensure_string,
    ensure_string_list,
)


def _validate_common_fields(data: Dict[str, Any], task_type: str) -> Dict[str, Any]:
    payload = ensure_mapping(f"item_{task_type}", data)
    if ensure_string(f"item_{task_type}.task_type", payload.get("task_type")) != task_type:
        raise SchemaValidationError(f"item_{task_type}.task_type must equal {task_type}.")
    return payload


@dataclass(frozen=True)
class BaseItem(SchemaMixin):
    seed_id: str
    item_id: str
    task_type: str
    regions: str
    countries: List[str]
    major_topic: str
    subtopic: str
    countries_or_regions: List[str]
    cq_tags: List[str]
    difficulty: str

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload.pop("countries_or_regions", None)
        return payload


@dataclass(frozen=True)
class TaskAItem(BaseItem):
    scenario: str
    question: str
    options: Dict[str, str]
    correct_option: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskAItem":
        payload = _validate_common_fields(data, "A")
        options = ensure_mapping("item_A.options", payload.get("options"))
        normalized_options = {}
        for option_key in ("A", "B", "C", "D"):
            normalized_options[option_key] = ensure_string(f"item_A.options.{option_key}", options.get(option_key))
        correct_option = ensure_string("item_A.correct_option", payload.get("correct_option"))
        if correct_option not in normalized_options:
            raise SchemaValidationError("item_A.correct_option must be one of A/B/C/D.")
        return cls(
            seed_id=ensure_string("item_A.seed_id", payload.get("seed_id")),
            item_id=ensure_string("item_A.item_id", payload.get("item_id")),
            task_type="A",
            **_metadata_fields(payload, "item_A"),
            scenario=ensure_string("item_A.scenario", payload.get("scenario")),
            question=ensure_string("item_A.question", payload.get("question")),
            options=normalized_options,
            correct_option=correct_option,
            cq_tags=ensure_single_cq("item_A.cq_tags", payload.get("cq_tags")),
            difficulty=ensure_difficulty("item_A.difficulty", payload.get("difficulty")),
        )


@dataclass(frozen=True)
class TaskBItem(BaseItem):
    scenario: str
    roles: Dict[str, str]
    dialogue_round: int
    dialogue: List[Dict[str, str]]
    label: str
    brief_reason: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskBItem":
        payload = _validate_common_fields(data, "B")
        roles = ensure_mapping("item_B.roles", payload.get("roles"))
        normalized_roles = {
            "local": ensure_string("item_B.roles.local", roles.get("local")),
            "newcomer": ensure_string("item_B.roles.newcomer", roles.get("newcomer")),
        }
        dialogue_round = ensure_int("item_B.dialogue_round", payload.get("dialogue_round"), min_value=2, max_value=4)
        dialogue = ensure_list("item_B.dialogue", payload.get("dialogue"))
        normalized_dialogue: List[Dict[str, str]] = []
        for index, item in enumerate(dialogue):
            turn = ensure_mapping(f"item_B.dialogue[{index}]", item)
            normalized_dialogue.append(
                {
                    "speaker": ensure_string(f"item_B.dialogue[{index}].speaker", turn.get("speaker")),
                    "text": ensure_string(f"item_B.dialogue[{index}].text", turn.get("text")),
                }
            )
        if len(normalized_dialogue) != dialogue_round * 2:
            raise SchemaValidationError("item_B.dialogue length must equal dialogue_round * 2.")
        label = ensure_string("item_B.label", payload.get("label"))
        if label not in ("appropriate", "inappropriate"):
            raise SchemaValidationError("item_B.label must be appropriate or inappropriate.")
        return cls(
            seed_id=ensure_string("item_B.seed_id", payload.get("seed_id")),
            item_id=ensure_string("item_B.item_id", payload.get("item_id")),
            task_type="B",
            **_metadata_fields(payload, "item_B"),
            scenario=ensure_string("item_B.scenario", payload.get("scenario")),
            roles=normalized_roles,
            dialogue_round=dialogue_round,
            dialogue=normalized_dialogue,
            label=label,
            brief_reason=ensure_string("item_B.brief_reason", payload.get("brief_reason")),
            cq_tags=ensure_single_cq("item_B.cq_tags", payload.get("cq_tags")),
            difficulty=ensure_difficulty("item_B.difficulty", payload.get("difficulty")),
        )


@dataclass(frozen=True)
class TaskCItem(BaseItem):
    scenario: str
    question: str
    rubric: List[Dict[str, str]]
    reference_outline: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskCItem":
        payload = _validate_common_fields(data, "C")
        rubric = ensure_list("item_C.rubric", payload.get("rubric"))
        normalized_rubric: List[Dict[str, str]] = []
        for index, item in enumerate(rubric):
            point = ensure_mapping(f"item_C.rubric[{index}]", item)
            normalized_rubric.append(
                {
                    "point": ensure_string(f"item_C.rubric[{index}].point", point.get("point")),
                    "score_rule": ensure_string(f"item_C.rubric[{index}].score_rule", point.get("score_rule")),
                }
            )
        if len(normalized_rubric) < 3:
            raise SchemaValidationError("item_C.rubric must contain at least 3 scoring points.")
        reference_outline = [
            ensure_string(f"item_C.reference_outline[{index}]", value)
            for index, value in enumerate(ensure_list("item_C.reference_outline", payload.get("reference_outline")))
        ]
        return cls(
            seed_id=ensure_string("item_C.seed_id", payload.get("seed_id")),
            item_id=ensure_string("item_C.item_id", payload.get("item_id")),
            task_type="C",
            **_metadata_fields(payload, "item_C"),
            scenario=ensure_string("item_C.scenario", payload.get("scenario")),
            question=ensure_string("item_C.question", payload.get("question")),
            rubric=normalized_rubric,
            reference_outline=reference_outline,
            cq_tags=ensure_single_cq("item_C.cq_tags", payload.get("cq_tags")),
            difficulty=ensure_difficulty("item_C.difficulty", payload.get("difficulty")),
        )


def parse_item_payload(data: Dict[str, Any]) -> Union[TaskAItem, TaskBItem, TaskCItem]:
    task_type = ensure_string("item.task_type", data.get("task_type"))
    if task_type not in ALLOWED_TASK_TYPES:
        raise SchemaValidationError(f"Unsupported task type: {task_type}")
    if task_type == "A":
        return TaskAItem.from_dict(data)
    if task_type == "B":
        return TaskBItem.from_dict(data)
    return TaskCItem.from_dict(data)


def _metadata_fields(payload: Dict[str, Any], name: str) -> Dict[str, Any]:
    regions = _optional_region(payload.get("regions"))
    countries = _optional_string_list(
        f"{name}.countries",
        payload.get("countries"),
        fallback=payload.get("countries_or_regions"),
        allow_empty=True,
    )
    countries_or_regions = _optional_string_list(
        f"{name}.countries_or_regions",
        payload.get("countries_or_regions"),
        fallback=countries or ([regions] if regions != "unspecified" else []),
        allow_empty=True,
    )
    return {
        "regions": regions,
        "countries": countries,
        "major_topic": _optional_string(payload.get("major_topic"), "unspecified"),
        "subtopic": _optional_string(payload.get("subtopic"), "unspecified"),
        "countries_or_regions": countries_or_regions,
    }


def _optional_string(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _optional_region(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list) and value:
        return ensure_string("item.regions[]", value[0])
    return "unspecified"


def _optional_string_list(name: str, value: Any, fallback: Any, allow_empty: bool = False) -> List[str]:
    if isinstance(value, list) and value:
        return ensure_string_list(name, value)
    if isinstance(value, str) and value.strip():
        return ensure_string_list(name, [value])
    if isinstance(fallback, list) and fallback:
        return ensure_string_list(name, fallback)
    if isinstance(fallback, str) and fallback.strip():
        return ensure_string_list(name, [fallback])
    if allow_empty:
        return []
    raise SchemaValidationError(f"{name} must be a non-empty list or string.")
