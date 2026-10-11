from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.errors import SchemaValidationError
from src.models.base import ALLOWED_CQ_TAGS, ALLOWED_TASK_TYPES, SchemaMixin, ensure_int, ensure_mapping, ensure_string


@dataclass(frozen=True)
class ExpertScore(SchemaMixin):
    expert: str
    score: int
    reason: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExpertScore":
        payload = ensure_mapping("expert_score", data)
        expert = ensure_string("expert_score.expert", payload.get("expert"))
        if expert not in ALLOWED_CQ_TAGS:
            raise SchemaValidationError(f"Unsupported expert name: {expert}")
        return cls(
            expert=expert,
            score=ensure_int("expert_score.score", payload.get("score"), min_value=1, max_value=5),
            reason=ensure_string("expert_score.reason", payload.get("reason")),
        )


@dataclass(frozen=True)
class TaskSelection(SchemaMixin):
    seed_id: str
    selected_task_type: str
    task_fit: Dict[str, int]
    reason: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskSelection":
        payload = ensure_mapping("task_selection", data)
        seed_id = ensure_string("task_selection.seed_id", payload.get("seed_id"))
        selected_task_type = ensure_string("task_selection.selected_task_type", payload.get("selected_task_type"))
        if selected_task_type not in ALLOWED_TASK_TYPES:
            raise SchemaValidationError(f"Unsupported task type: {selected_task_type}")
        task_fit_raw = ensure_mapping("task_selection.task_fit", payload.get("task_fit"))
        task_fit = {}
        for task_type in ALLOWED_TASK_TYPES:
            task_fit[task_type] = ensure_int(
                f"task_selection.task_fit.{task_type}",
                task_fit_raw.get(task_type),
                min_value=1,
                max_value=5,
            )
        return cls(
            seed_id=seed_id,
            selected_task_type=selected_task_type,
            task_fit=task_fit,
            reason=ensure_string("task_selection.reason", payload.get("reason")),
        )


@dataclass(frozen=True)
class DistributionSnapshot(SchemaMixin):
    total_items: int
    task_counts: Dict[str, int]
    cq_counts: Dict[str, int]
    task_cq_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    b_label_counts: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        total_items: int,
        task_counts: Dict[str, int],
        cq_counts: Dict[str, int],
        b_label_counts: Dict[str, int],
        task_cq_counts: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> "DistributionSnapshot":
        task_cq_counts = task_cq_counts or {}
        return cls(
            total_items=total_items,
            task_counts={task: int(task_counts.get(task, 0)) for task in ALLOWED_TASK_TYPES},
            cq_counts={cq: int(cq_counts.get(cq, 0)) for cq in ALLOWED_CQ_TAGS},
            task_cq_counts={
                task: {
                    cq: int(task_cq_counts.get(task, {}).get(cq, 0))
                    for cq in ALLOWED_CQ_TAGS
                }
                for task in ALLOWED_TASK_TYPES
            },
            b_label_counts={
                "appropriate": int(b_label_counts.get("appropriate", 0)),
                "inappropriate": int(b_label_counts.get("inappropriate", 0)),
            },
        )


@dataclass(frozen=True)
class ModeratorDecision(SchemaMixin):
    seed_id: str
    selected_task_type: str
    selected_cq: str
    decision_reason: str
    distribution_snapshot: DistributionSnapshot
    decision_scores: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        seed_id: str,
        selected_task_type: str,
        selected_cq: str,
        decision_reason: str,
        distribution_snapshot: DistributionSnapshot,
        decision_scores: Dict[str, Any],
    ) -> "ModeratorDecision":
        if selected_task_type not in ALLOWED_TASK_TYPES:
            raise SchemaValidationError(f"Unsupported task type: {selected_task_type}")
        if selected_cq not in ALLOWED_CQ_TAGS:
            raise SchemaValidationError(f"Unsupported CQ tag: {selected_cq}")
        return cls(
            seed_id=ensure_string("moderator_decision.seed_id", seed_id),
            selected_task_type=selected_task_type,
            selected_cq=selected_cq,
            decision_reason=ensure_string("moderator_decision.decision_reason", decision_reason),
            distribution_snapshot=distribution_snapshot,
            decision_scores=decision_scores,
        )


@dataclass(frozen=True)
class RejectedRecord(SchemaMixin):
    seed_id: str
    stage: str
    reason: str
    payload: Dict[str, Any]
    trace: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        seed_id: str,
        stage: str,
        reason: str,
        payload: Dict[str, Any],
        trace: Dict[str, Any],
    ) -> "RejectedRecord":
        return cls(
            seed_id=seed_id,
            stage=ensure_string("rejected.stage", stage),
            reason=ensure_string("rejected.reason", reason),
            payload=payload,
            trace=trace,
        )
