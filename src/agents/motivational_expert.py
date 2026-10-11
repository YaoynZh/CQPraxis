from src.agents.cq_expert import CQExpertAgent


class MotivationalExpert(CQExpertAgent):
    def __init__(self, *args, **kwargs):
        super().__init__("motivational", *args, **kwargs)
