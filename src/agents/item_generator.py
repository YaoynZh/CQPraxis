from pathlib import Path
from typing import Any, Dict, Optional

from src.agents.base import BaseAgent
from src.models.decision_schema import ExpertScore, ModeratorDecision, TaskSelection
from src.models.item_schema import parse_item_payload
from src.models.seed_schema import SeedRecord


class ItemGeneratorAgent:
    def __init__(
        self,
        llm_client,
        prompt_dir: Path,
        temperature: float,
        max_tokens: int,
        max_retries: int,
        reasoning_effort: Optional[str] = None,
    ):
        self.prompt_dir = prompt_dir
        self.generators = {
            "A": BaseAgent(
                name="item_generator_A",
                llm_client=llm_client,
                prompt_path=prompt_dir / "generate_A.md",
                temperature=temperature,
                max_tokens=max_tokens,
                max_retries=max_retries,
                reasoning_effort=reasoning_effort,
            ),
            "B": BaseAgent(
                name="item_generator_B",
                llm_client=llm_client,
                prompt_path=prompt_dir / "generate_B.md",
                temperature=temperature,
                max_tokens=max_tokens,
                max_retries=max_retries,
                reasoning_effort=reasoning_effort,
            ),
            "C": BaseAgent(
                name="item_generator_C",
                llm_client=llm_client,
                prompt_path=prompt_dir / "generate_C.md",
                temperature=temperature,
                max_tokens=max_tokens,
                max_retries=max_retries,
                reasoning_effort=reasoning_effort,
            ),
        }

    def generate_item(
        self,
        seed: SeedRecord,
        decision: ModeratorDecision,
        moderator_analysis: TaskSelection,
        selected_expert_score: ExpertScore,
        item_id: str,
        generation_hints: Optional[Dict[str, Any]] = None,
        validation_feedback: Optional[str] = None,
    ):
        decision_payload = decision.to_dict()
        decision_payload.pop("distribution_snapshot", None)
        payload = {
            "seed": seed.summary(),
            "moderator_analysis": moderator_analysis.to_dict(),
            "decision": decision_payload,
            "selected_expert_score": selected_expert_score.to_dict(),
            "item_id": item_id,
            "generation_hints": generation_hints or {},
        }
        if validation_feedback:
            payload["validation_feedback"] = validation_feedback
        response = self.generators[decision.selected_task_type].invoke(payload)
        return parse_item_payload(response)
