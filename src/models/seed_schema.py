from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.models.base import (
    ALLOWED_CQ_TAGS,
    ALLOWED_TASK_TYPES,
    SchemaMixin,
    ensure_mapping,
    ensure_string,
    ensure_string_list,
    require_keys,
)
from src.errors import SchemaValidationError


@dataclass(frozen=True)
class SourceReference(SchemaMixin):
    title: str
    url: str
    publisher: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceReference":
        payload = ensure_mapping("source[]", data)
        require_keys(payload, ("title", "url", "publisher"))
        return cls(
            title=ensure_string("source[].title", payload["title"]),
            url=ensure_string("source[].url", payload["url"]),
            publisher=ensure_string("source[].publisher", payload["publisher"]),
        )


@dataclass(frozen=True)
class SeedRecord(SchemaMixin):
    seed_id: str
    title: str
    regions: str
    countries: List[str]
    major_topic: str
    subtopic: str
    culture_point: str
    knowledge: str
    common_misunderstanding: str
    typical_scenario: str
    suitable_task_types: List[str]
    cq_tags: List[str]
    source: List[SourceReference]
    countries_or_regions: List[str]
    context: str
    extras: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeedRecord":
        payload = ensure_mapping("seed", data)
        require_keys(payload, ("seed_id", "knowledge"))

        seed_id = ensure_string("seed.seed_id", payload["seed_id"])
        knowledge = ensure_string("seed.knowledge", payload["knowledge"])
        culture_point = knowledge
        title = _optional_string(payload.get("title"), seed_id)
        regions = _optional_region(payload.get("regions"), default="unspecified")
        countries = _optional_string_list(
            "seed.countries",
            payload.get("countries"),
            fallback=payload.get("countries_or_regions"),
            allow_empty=True,
        )
        countries_or_regions = _optional_string_list(
            "seed.countries_or_regions",
            payload.get("countries_or_regions"),
            fallback=countries or ([regions] if regions != "unspecified" else []),
            allow_empty=True,
        )
        major_topic = _optional_string(payload.get("major_topic"), _optional_string(payload.get("context"), "general"))
        subtopic = _optional_string(payload.get("subtopic"), major_topic)
        context = _optional_string(payload.get("context"), major_topic)
        common_misunderstanding = _optional_string(
            payload.get("common_misunderstanding"),
            "An outsider may overgeneralize from a generic global default instead of applying this seed-specific knowledge.",
        )
        typical_scenario = _optional_string(
            payload.get("typical_scenario"),
            f"A practical cross-cultural situation requires applying this knowledge: {knowledge}",
        )
        suitable_task_types = _optional_string_list(
            "seed.suitable_task_types",
            payload.get("suitable_task_types"),
            fallback=list(ALLOWED_TASK_TYPES),
            allowed=ALLOWED_TASK_TYPES,
        )
        cq_tags = _optional_string_list(
            "seed.cq_tags",
            payload.get("cq_tags"),
            fallback=list(ALLOWED_CQ_TAGS),
            allowed=ALLOWED_CQ_TAGS,
        )
        source = _normalize_sources(payload)

        recognized_fields = {
            "seed_id",
            "title",
            "regions",
            "countries",
            "major_topic",
            "subtopic",
            "countries_or_regions",
            "context",
            "culture_point",
            "knowledge",
            "common_misunderstanding",
            "typical_scenario",
            "suitable_task_types",
            "cq_tags",
            "difficulty",
            "source",
            "publisher",
            "url",
        }
        extras = {key: value for key, value in payload.items() if key not in recognized_fields}
        return cls(
            seed_id=seed_id,
            title=title,
            regions=regions,
            countries=countries,
            major_topic=major_topic,
            subtopic=subtopic,
            culture_point=culture_point,
            knowledge=knowledge,
            common_misunderstanding=common_misunderstanding,
            typical_scenario=typical_scenario,
            suitable_task_types=suitable_task_types,
            cq_tags=cq_tags,
            source=source,
            countries_or_regions=countries_or_regions,
            context=context,
            extras=extras,
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "regions": self.regions,
            "countries": self.countries,
            "major_topic": self.major_topic,
            "subtopic": self.subtopic,
            "countries_or_regions": self.countries_or_regions,
            "context": self.context,
            "knowledge": self.knowledge,
            "common_misunderstanding": self.common_misunderstanding,
            "typical_scenario": self.typical_scenario,
            "suitable_task_types": self.suitable_task_types,
            "cq_tags": self.cq_tags,
        }


def _optional_string(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _optional_region(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list) and value:
        return ensure_string("seed.regions[]", value[0])
    return default


def _optional_string_list(name: str, value: Any, fallback: Any, allowed=(), allow_empty: bool = False) -> List[str]:
    if isinstance(value, list) and value:
        return ensure_string_list(name, value, allowed=allowed)
    if isinstance(value, str) and value.strip():
        return ensure_string_list(name, [value], allowed=allowed)
    if isinstance(fallback, list) and fallback:
        return ensure_string_list(name, fallback, allowed=allowed)
    if isinstance(fallback, str) and fallback.strip():
        return ensure_string_list(name, [fallback], allowed=allowed)
    if allow_empty:
        return []
    raise SchemaValidationError(f"{name} must be a non-empty list or string.")


def _normalize_sources(payload: Dict[str, Any]) -> List[SourceReference]:
    raw_source = payload.get("source")
    if isinstance(raw_source, list) and raw_source:
        return [SourceReference.from_dict(item) for item in raw_source]

    urls = _raw_string_list(payload.get("url"))
    publishers = _raw_string_list(payload.get("publisher"))
    title = _optional_string(payload.get("title"), _optional_string(payload.get("seed_id"), "seed"))
    sources: List[SourceReference] = []
    for index, url in enumerate(urls):
        publisher = publishers[index] if index < len(publishers) else publishers[0] if publishers else "unknown"
        sources.append(
            SourceReference(
                title=f"{title} source {index + 1}",
                url=url,
                publisher=publisher,
            )
        )
    return sources


def _raw_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
