from src.agents.base import BaseAgent
from src.agents.participant_skills import load_cq_expert_skill, load_cq_expert_skills
from src.models.decision_schema import DistributionSnapshot, ExpertScore, TaskSelection
from src.models.seed_schema import SeedRecord


class CQExpertAgent(BaseAgent):
    def __init__(self, expert_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expert_name = expert_name

    def score_seed(self, seed: SeedRecord, snapshot: DistributionSnapshot, task_selection: TaskSelection) -> ExpertScore:
        payload = {
            "seed": seed.summary(),
            "task_selection": task_selection.to_dict(),
            "expert": self.expert_name,
            "participant_skill": load_cq_expert_skill(self.expert_name),
            "panel_cq_skills": load_cq_expert_skills(),
            "panel_selection_goal": (
                "Score how strongly your CQ dimension can produce a valid, high-value item for this seed. "
                "Argue against the other CQ dimensions implicitly: use 5 only when your dimension creates the "
                "clearest CQ-dependent reasoning move, and use lower scores when another expert would make a better item."
            ),
        }
        response = self.invoke(payload)
        return ExpertScore.from_dict(response)
