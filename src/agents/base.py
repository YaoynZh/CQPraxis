from pathlib import Path
from typing import Any, Dict, Optional

from src.llm.client import LLMClient


class BaseAgent:
    def __init__(
        self,
        name: str,
        llm_client: LLMClient,
        prompt_path: Path,
        temperature: float,
        max_tokens: int,
        max_retries: int,
        reasoning_effort: Optional[str] = None,
    ):
        self.name = name
        self.llm_client = llm_client
        self.prompt_path = prompt_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.reasoning_effort = reasoning_effort

    def invoke(self, payload: Dict[str, Any], json_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.llm_client.generate_json(
            prompt_path=self.prompt_path,
            payload=payload,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
            json_schema=json_schema,
            reasoning_effort=self.reasoning_effort,
        )
