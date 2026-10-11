from pathlib import Path
from typing import Dict, Iterable, Optional, Set

from src.models.base import ALLOWED_CQ_TAGS, ALLOWED_TASK_TYPES
from src.models.decision_schema import DistributionSnapshot
from src.models.item_schema import BaseItem
from src.utils.hashing import stable_hash
from src.utils.io import read_jsonl


class DistributionTracker:
    def __init__(self) -> None:
        self.task_counts: Dict[str, int] = {task: 0 for task in ALLOWED_TASK_TYPES}
        self.cq_counts: Dict[str, int] = {cq: 0 for cq in ALLOWED_CQ_TAGS}
        self.task_cq_counts: Dict[str, Dict[str, int]] = {
            task: {cq: 0 for cq in ALLOWED_CQ_TAGS}
            for task in ALLOWED_TASK_TYPES
        }
        self.domain_counts: Dict[str, int] = {}
        self.region_counts: Dict[str, int] = {}
        self.b_label_counts: Dict[str, int] = {"appropriate": 0, "inappropriate": 0}
        self.b_subtopic_label_counts: Dict[str, Dict[str, int]] = {}
        self.a_correct_counts: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        self.seen_hashes: Set[str] = set()
        self.total_items = 0

    @classmethod
    def from_output_file(cls, all_items_path: Path) -> "DistributionTracker":
        tracker = cls()
        if not all_items_path.exists():
            return tracker
        for record in read_jsonl(all_items_path):
            task_type = record.get("task_type")
            if task_type in tracker.task_counts:
                tracker.task_counts[task_type] += 1
            cq_tags = record.get("cq_tags", [])
            if isinstance(cq_tags, list) and cq_tags:
                cq = cq_tags[0]
                if cq in tracker.cq_counts:
                    tracker.cq_counts[cq] += 1
                    if task_type in tracker.task_cq_counts:
                        tracker.task_cq_counts[task_type][cq] += 1
            domain = record.get("major_topic")
            if isinstance(domain, str) and domain:
                tracker.domain_counts[domain] = tracker.domain_counts.get(domain, 0) + 1
            region = record.get("regions")
            if isinstance(region, str) and region:
                tracker.region_counts[region] = tracker.region_counts.get(region, 0) + 1
            if task_type == "B":
                label = record.get("label")
                if label in tracker.b_label_counts:
                    tracker.b_label_counts[label] += 1
                    tracker._register_b_subtopic_label(record.get("subtopic"), label)
            if task_type == "A":
                correct_option = record.get("correct_option")
                if correct_option in tracker.a_correct_counts:
                    tracker.a_correct_counts[correct_option] += 1
            tracker.total_items += 1
            tracker.seen_hashes.add(tracker.item_identity_hash(record))
        return tracker

    def snapshot(self) -> DistributionSnapshot:
        return DistributionSnapshot.create(
            total_items=self.total_items,
            task_counts=self.task_counts,
            cq_counts=self.cq_counts,
            b_label_counts=self.b_label_counts,
            task_cq_counts=self.task_cq_counts,
        )

    def next_item_index(self, task_type: str) -> int:
        return self.task_counts[task_type] + 1

    def preferred_a_correct_option(self) -> str:
        min_count = min(self.a_correct_counts.values())
        candidates = [option for option, count in self.a_correct_counts.items() if count == min_count]
        if len(candidates) == 1:
            return candidates[0]
        digest = stable_hash(
            {
                "task": "A",
                "task_count": self.task_counts["A"],
                "total_items": self.total_items,
                "a_correct_counts": self.a_correct_counts,
            }
        )
        return candidates[int(digest[:8], 16) % len(candidates)]

    def preferred_b_label_for_subtopic(self, subtopic: str) -> Optional[str]:
        counts = self.b_subtopic_label_counts.get(subtopic)
        if not counts:
            return None
        appropriate = counts.get("appropriate", 0)
        inappropriate = counts.get("inappropriate", 0)
        if appropriate >= inappropriate + 1:
            return "inappropriate"
        if inappropriate >= appropriate + 1:
            return "appropriate"
        return None

    def b_subtopic_label_context(self, subtopic: str) -> Dict[str, int]:
        counts = self.b_subtopic_label_counts.get(subtopic, {})
        return {
            "appropriate": counts.get("appropriate", 0),
            "inappropriate": counts.get("inappropriate", 0),
        }

    def register_item(self, item: BaseItem) -> None:
        payload = item.to_dict()
        self.task_counts[item.task_type] += 1
        self.cq_counts[item.cq_tags[0]] += 1
        self.task_cq_counts[item.task_type][item.cq_tags[0]] += 1
        if item.major_topic:
            self.domain_counts[item.major_topic] = self.domain_counts.get(item.major_topic, 0) + 1
        if item.regions:
            self.region_counts[item.regions] = self.region_counts.get(item.regions, 0) + 1
        if item.task_type == "B":
            label = payload.get("label")
            if label in self.b_label_counts:
                self.b_label_counts[label] += 1
                self._register_b_subtopic_label(payload.get("subtopic"), label)
        if item.task_type == "A":
            correct_option = payload.get("correct_option")
            if correct_option in self.a_correct_counts:
                self.a_correct_counts[correct_option] += 1
        self.total_items += 1
        self.seen_hashes.add(self.item_identity_hash(payload))

    def is_duplicate(self, payload: Dict[str, object]) -> bool:
        return self.item_identity_hash(payload) in self.seen_hashes

    @staticmethod
    def item_identity_hash(payload: Dict[str, object]) -> str:
        keys = (
            "task_type",
            "scenario",
            "question",
            "options",
            "dialogue",
            "label",
            "rubric",
            "reference_outline",
            "cq_tags",
        )
        return stable_hash(payload, keys=keys)

    def _register_b_subtopic_label(self, subtopic: object, label: str) -> None:
        if not isinstance(subtopic, str) or label not in self.b_label_counts:
            return
        counts = self.b_subtopic_label_counts.setdefault(
            subtopic,
            {"appropriate": 0, "inappropriate": 0},
        )
        counts[label] += 1
