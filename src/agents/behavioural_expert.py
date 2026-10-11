from src.agents.cq_expert import CQExpertAgent


class BehaviouralExpert(CQExpertAgent):
    def __init__(self, *args, **kwargs):
        super().__init__("behavioural", *args, **kwargs)
