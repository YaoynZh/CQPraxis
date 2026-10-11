import math
from typing import Any, Dict, Iterable, List, Sequence

from src.config import DistributionConfig
from src.models.base import ALLOWED_CQ_TAGS, ALLOWED_TASK_TYPES
from src.models.decision_schema import ExpertScore, ModeratorDecision, TaskSelection
from src.models.seed_schema import SeedRecord


TASK_ORDER = {task_type: index for index, task_type in enumerate(ALLOWED_TASK_TYPES)}
CQ_ORDER = {cq_tag: index for index, cq_tag in enumerate(ALLOWED_CQ_TAGS)}


class BalancingRules:
    """Fit-only label selection plus post-generation distribution stopping.

    Distribution counts never alter task or CQ labels. They are consulted only
    to decide whether the validated candidate pool is large and balanced enough
    to stop generation.
    """

    def __init__(self, config: DistributionConfig):
        self.config = config

    def build_decision(
        self,
        seed: SeedRecord,
        task_selection: TaskSelection,
        expert_scores: List[ExpertScore],
        snapshot,
        allowed_task_types: Iterable[str],
    ) -> ModeratorDecision:
        allowed = [task for task in allowed_task_types if task in ALLOWED_TASK_TYPES]
        if not allowed:
            raise ValueError("At least one allowed task type is required.")

        best_task_fit = max(task_selection.task_fit[task] for task in allowed)
        best_tasks = [task for task in allowed if task_selection.task_fit[task] == best_task_fit]
        if task_selection.selected_task_type in best_tasks:
            selected_task = task_selection.selected_task_type
        else:
            selected_task = min(best_tasks, key=lambda task: TASK_ORDER[task])

        score_lookup = {entry.expert: entry for entry in expert_scores}
        missing_experts = [cq for cq in ALLOWED_CQ_TAGS if cq not in score_lookup]
        if missing_experts:
            raise ValueError(f"Missing CQ expert scores: {missing_experts}")
        best_cq_fit = max(score_lookup[cq].score for cq in ALLOWED_CQ_TAGS)
        best_cqs = [cq for cq in ALLOWED_CQ_TAGS if score_lookup[cq].score == best_cq_fit]
        selected_cq = min(best_cqs, key=lambda cq: CQ_ORDER[cq])

        decision_scores = {
            "selection_policy": "fit_only",
            "task_fit": {task: task_selection.task_fit[task] for task in ALLOWED_TASK_TYPES},
            "cq_fit": {cq: score_lookup[cq].score for cq in ALLOWED_CQ_TAGS},
            "task_tie_candidates": best_tasks,
            "cq_tie_candidates": best_cqs,
            "distribution_used_for_label_selection": False,
        }
        reason = (
            f"Task {selected_task} was selected from the highest moderator task-fit score "
            f"({best_task_fit}). CQ {selected_cq} was selected from the highest expert "
            f"self-assessment score ({best_cq_fit}). Distribution counts did not alter either label."
        )
        return ModeratorDecision.create(
            seed_id=seed.seed_id,
            selected_task_type=selected_task,
            selected_cq=selected_cq,
            decision_reason=reason,
            distribution_snapshot=snapshot,
            decision_scores=decision_scores,
        )

    def coverage_status(
        self,
        *,
        tracker,
        target_total_items: int,
        allowed_task_types: Sequence[str],
        cultural_domains: Sequence[str],
        regions: Sequence[str],
    ) -> Dict[str, Any]:
        if target_total_items < 1:
            raise ValueError("target_total_items must be at least 1.")

        dimension_status: Dict[str, Dict[str, Any]] = {}
        if "task_cq" in self.config.coverage_dimensions:
            categories = [
                f"{task}|{cq}"
                for task in allowed_task_types
                for cq in ALLOWED_CQ_TAGS
            ]
            counts = {
                f"{task}|{cq}": tracker.task_cq_counts.get(task, {}).get(cq, 0)
                for task in allowed_task_types
                for cq in ALLOWED_CQ_TAGS
            }
            dimension_status["task_cq"] = self._dimension_status(
                categories, counts, target_total_items
            )

        if "major_topic" in self.config.coverage_dimensions:
            categories = sorted(set(cultural_domains))
            counts = {category: tracker.domain_counts.get(category, 0) for category in categories}
            dimension_status["major_topic"] = self._dimension_status(
                categories, counts, target_total_items
            )

        if "regions" in self.config.coverage_dimensions:
            categories = sorted(set(regions))
            counts = {category: tracker.region_counts.get(category, 0) for category in categories}
            dimension_status["regions"] = self._dimension_status(
                categories, counts, target_total_items
            )

        return {
            "satisfied": bool(dimension_status)
            and all(status["satisfied"] for status in dimension_status.values()),
            "target_total_items": target_total_items,
            "candidate_items": tracker.total_items,
            "extra_candidates": max(0, tracker.total_items - target_total_items),
            "dimensions": dimension_status,
        }

    @staticmethod
    def _dimension_status(
        categories: Sequence[str],
        counts: Dict[str, int],
        target_total_items: int,
    ) -> Dict[str, Any]:
        if not categories:
            return {
                "satisfied": False,
                "category_count": 0,
                "quota_per_category": 0,
                "minimum_count": 0,
                "counts": {},
                "deficits": {},
            }
        quota = math.ceil(target_total_items / len(categories))
        normalized_counts = {category: int(counts.get(category, 0)) for category in categories}
        deficits = {
            category: quota - count
            for category, count in normalized_counts.items()
            if count < quota
        }
        return {
            "satisfied": not deficits,
            "category_count": len(categories),
            "quota_per_category": quota,
            "minimum_count": min(normalized_counts.values()),
            "counts": normalized_counts,
            "deficits": deficits,
        }
