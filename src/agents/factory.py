from pathlib import Path
from typing import Dict, List

from src.agents.behavioural_expert import BehaviouralExpert
from src.agents.cognitive_expert import CognitiveExpert
from src.agents.item_generator import ItemGeneratorAgent
from src.agents.metacognitive_expert import MetacognitiveExpert
from src.agents.moderator import MultiCultureModerator
from src.agents.motivational_expert import MotivationalExpert
from src.config import GenerationConfig, ModelConfig
from src.llm.client import LLMClient


def build_agents(
    llm_client: LLMClient,
    prompt_dir: Path,
    model_config: ModelConfig,
    generation_config: GenerationConfig,
) -> Dict[str, object]:
    return {
        "moderator": MultiCultureModerator(
            name="moderator",
            llm_client=llm_client,
            prompt_path=prompt_dir / "moderator_task.md",
            temperature=model_config.moderator.temperature,
            max_tokens=model_config.moderator.max_tokens,
            max_retries=generation_config.default_max_retries,
            reasoning_effort=model_config.moderator.reasoning_effort,
        ),
        "experts": [
            MetacognitiveExpert(
                name="metacognitive_expert",
                llm_client=llm_client,
                prompt_path=prompt_dir / "metacognitive.md",
                temperature=model_config.cq_expert.temperature,
                max_tokens=model_config.cq_expert.max_tokens,
                max_retries=generation_config.default_max_retries,
                reasoning_effort=model_config.cq_expert.reasoning_effort,
            ),
            CognitiveExpert(
                name="cognitive_expert",
                llm_client=llm_client,
                prompt_path=prompt_dir / "cognitive.md",
                temperature=model_config.cq_expert.temperature,
                max_tokens=model_config.cq_expert.max_tokens,
                max_retries=generation_config.default_max_retries,
                reasoning_effort=model_config.cq_expert.reasoning_effort,
            ),
            MotivationalExpert(
                name="motivational_expert",
                llm_client=llm_client,
                prompt_path=prompt_dir / "motivational.md",
                temperature=model_config.cq_expert.temperature,
                max_tokens=model_config.cq_expert.max_tokens,
                max_retries=generation_config.default_max_retries,
                reasoning_effort=model_config.cq_expert.reasoning_effort,
            ),
            BehaviouralExpert(
                name="behavioural_expert",
                llm_client=llm_client,
                prompt_path=prompt_dir / "behavioural.md",
                temperature=model_config.cq_expert.temperature,
                max_tokens=model_config.cq_expert.max_tokens,
                max_retries=generation_config.default_max_retries,
                reasoning_effort=model_config.cq_expert.reasoning_effort,
            ),
        ],
        "item_generator": ItemGeneratorAgent(
            llm_client=llm_client,
            prompt_dir=prompt_dir,
            temperature=model_config.item_generator.temperature,
            max_tokens=model_config.item_generator.max_tokens,
            max_retries=generation_config.default_max_retries,
            reasoning_effort=model_config.item_generator.reasoning_effort,
        ),
    }
