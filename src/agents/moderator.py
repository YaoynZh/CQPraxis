from typing import Iterable

from src.agents.base import BaseAgent
from src.agents.participant_skills import load_cq_expert_skills, load_moderator_skill
from src.models.decision_schema import DistributionSnapshot, TaskSelection
from src.models.seed_schema import SeedRecord


class MultiCultureModerator(BaseAgent):
    def select_task(
        self,
        seed: SeedRecord,
        snapshot: DistributionSnapshot,
        allowed_task_types: Iterable[str],
    ) -> TaskSelection:
        payload = {
            "seed": seed.summary(),
            "allowed_task_types": list(allowed_task_types),
            "participant_skill": load_moderator_skill(),
            "cq_expert_skills": load_cq_expert_skills(),
        }
        response = self.invoke(payload)
        return TaskSelection.from_dict(response)
