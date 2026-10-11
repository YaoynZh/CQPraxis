from src.agents.cq_expert import CQExpertAgent


class CognitiveExpert(CQExpertAgent):
    def __init__(self, *args, **kwargs):
        super().__init__("cognitive", *args, **kwargs)
