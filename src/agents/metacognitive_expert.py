from src.agents.cq_expert import CQExpertAgent


class MetacognitiveExpert(CQExpertAgent):
    def __init__(self, *args, **kwargs):
        super().__init__("metacognitive", *args, **kwargs)
