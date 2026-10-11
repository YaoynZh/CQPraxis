import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import certifi
import requests

from src.config import load_env_file
from src.errors import ConfigError, JSONParseError, LLMClientError
from src.utils.json_utils import extract_json_payload
from src.utils.logger import build_logger


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str],
        base_url: str,
        model: str,
        timeout_seconds: int = 90,
        default_max_retries: int = 3,
        retry_sleep_seconds: float = 5.0,
        mock_mode: bool = False,
    ):
        self.api_key = api_key
        self.base_url = f"{base_url.rstrip('/')}/chat/completions"
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.default_max_retries = default_max_retries
        self.retry_sleep_seconds = retry_sleep_seconds
        self.mock_mode = mock_mode
        self.logger = build_logger("multiculture.llm")

    @classmethod
    def from_env(
        cls,
        timeout_seconds: int = 90,
        default_max_retries: int = 3,
        mock_mode: bool = False,
    ) -> "LLMClient":
        load_env_file()
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-5.4")
        retry_sleep_seconds = float(os.getenv("MCG_LLM_RETRY_SLEEP_SECONDS", "5"))
        env_mock_mode = os.getenv("MCG_USE_MOCK_LLM", "false").lower() == "true"
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
            default_max_retries=default_max_retries,
            retry_sleep_seconds=retry_sleep_seconds,
            mock_mode=mock_mode or env_mock_mode,
        )

    def generate_json(
        self,
        prompt_path: Path,
        payload: Dict[str, Any],
        temperature: float,
        max_tokens: int,
        max_retries: Optional[int] = None,
        json_schema: Optional[Dict[str, Any]] = None,
        reasoning_effort: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt_text = prompt_path.read_text(encoding="utf-8")
        retries = max_retries if max_retries is not None else self.default_max_retries

        if self.mock_mode:
            return self._mock_response(prompt_path.name, payload)

        if not self.api_key:
            raise ConfigError(
                "OPENAI_API_KEY is missing. Set it in the environment or in project-root .env. "
                ".env.example is only a template and is not auto-loaded. "
                "Alternatively enable MCG_USE_MOCK_LLM=true."
            )

        last_error: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                raw_text = self._request(
                    prompt_text=prompt_text,
                    payload=payload,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_schema=json_schema,
                    reasoning_effort=reasoning_effort,
                )
                parsed = extract_json_payload(raw_text)
                if not isinstance(parsed, dict):
                    raise JSONParseError("Model output must decode to a JSON object.")
                return parsed
            except (requests.exceptions.RequestException, TimeoutError, JSONParseError, LLMClientError) as exc:
                last_error = exc
                self.logger.warning("LLM call failed on attempt %s/%s: %s", attempt, retries, exc)
                if attempt == retries:
                    break
                time.sleep(self.retry_sleep_seconds)

        raise LLMClientError(f"LLM request failed after {retries} attempts: {last_error}")

    def _request(
        self,
        prompt_text: str,
        payload: Dict[str, Any],
        temperature: float,
        max_tokens: int,
        json_schema: Optional[Dict[str, Any]],
        reasoning_effort: Optional[str],
    ) -> str:
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt_text},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False, indent=2),
                },
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if reasoning_effort is not None:
            body["reasoning_effort"] = reasoning_effort
        if json_schema:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema,
            }
        else:
            body["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=body,
                timeout=self.timeout_seconds,
                verify=certifi.where(),
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            detail = self._describe_requests_exception(exc)
            raise LLMClientError(detail) from exc

        try:
            response_payload = response.json()
        except ValueError as exc:
            preview = response.text[:1000] if response.text else ""
            raise LLMClientError(
                "LLM endpoint returned non-JSON response "
                f"(status={response.status_code}, content_type={response.headers.get('Content-Type', '')}, "
                f"preview={preview!r})"
            ) from exc

        return self._extract_response_text(response_payload)

    def _describe_requests_exception(self, exc: requests.exceptions.RequestException) -> str:
        parts = [f"{type(exc).__name__}: {exc}"]
        if exc.__cause__:
            parts.append(f"cause={type(exc.__cause__).__name__}: {exc.__cause__}")
        response = getattr(exc, "response", None)
        if response is not None:
            preview = response.text[:500] if getattr(response, "text", None) else ""
            parts.append(f"status={response.status_code}")
            if preview:
                parts.append(f"preview={preview!r}")
        return " | ".join(parts)

    def _extract_response_text(self, payload: Dict[str, Any]) -> str:
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_chunks = []
                for item in content:
                    if item.get("type") == "text" and "text" in item:
                        text_chunks.append(item["text"])
                if text_chunks:
                    return "\n".join(text_chunks)

        output = payload.get("output")
        if isinstance(output, list):
            text_chunks = []
            for block in output:
                content = block.get("content", [])
                if not isinstance(content, list):
                    continue
                for item in content:
                    if item.get("type") == "output_text" and "text" in item:
                        text_chunks.append(item["text"])
            if text_chunks:
                return "\n".join(text_chunks)

        raise LLMClientError("Unsupported response payload shape from model endpoint.")

    def _mock_response(self, prompt_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        seed = payload.get("seed", {})
        task_type = payload.get("decision", {}).get("selected_task_type")
        if prompt_name == "moderator_task.md":
            return self._mock_task_selection(seed, payload)
        if prompt_name == "metacognitive.md":
            return self._mock_expert_score(seed, payload, "metacognitive")
        if prompt_name == "cognitive.md":
            return self._mock_expert_score(seed, payload, "cognitive")
        if prompt_name == "motivational.md":
            return self._mock_expert_score(seed, payload, "motivational")
        if prompt_name == "behavioural.md":
            return self._mock_expert_score(seed, payload, "behavioural")
        if prompt_name == "validate_item.md":
            return self._mock_item_validation()
        if prompt_name == "generate_A.md":
            return self._mock_item_a(seed, payload)
        if prompt_name == "generate_B.md":
            return self._mock_item_b(seed, payload)
        if prompt_name == "generate_C.md":
            return self._mock_item_c(seed, payload)
        raise LLMClientError(f"No mock response implemented for prompt: {prompt_name}")

    def _mock_item_validation(self) -> Dict[str, Any]:
        return {
            "seed_grounding": {
                "pass": True,
                "reason": "The item operationalizes the supplied seed knowledge without contradicting it.",
            },
            "cq_alignment": {
                "pass": True,
                "reason": "The decisive reasoning follows the selected CQ guidance.",
            },
            "task_format_validity": {
                "pass": True,
                "reason": "The item follows the selected task format and required response structure.",
            },
            "answer_coherence": {
                "pass": True,
                "reason": "The answer key and supporting rationale are internally coherent.",
            },
            "overall_pass": True,
            "feedback": "",
        }

    def _mock_task_selection(self, seed: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        suitable = set(seed.get("suitable_task_types", []))
        text_blob = " ".join(
            [
                str(seed.get("context", "")),
                str(seed.get("knowledge", "")),
                str(seed.get("common_misunderstanding", "")),
                str(seed.get("typical_scenario", "")),
            ]
        ).lower()
        task_fit = {"A": 2, "B": 2, "C": 2}
        for task in suitable:
            task_fit[task] = max(task_fit[task], 4)
        if any(token in text_blob for token in ("which", "judge", "decide", "misunderstanding")):
            task_fit["A"] = max(task_fit["A"], 4)
        if any(token in text_blob for token in ("meeting", "visit", "dialogue", "host", "client", "colleague")):
            task_fit["B"] = max(task_fit["B"], 4)
        if any(token in text_blob for token in ("team", "project", "feedback", "coordination", "decision")):
            task_fit["C"] = max(task_fit["C"], 4)

        allowed_task_types = payload.get("allowed_task_types", ["A", "B", "C"])
        selected_task_type = max(allowed_task_types, key=lambda item: (task_fit[item], -["A", "B", "C"].index(item)))
        return {
            "seed_id": seed.get("seed_id", ""),
            "selected_task_type": selected_task_type,
            "task_fit": task_fit,
            "reason": "Mock moderator selected the task type based on the scenario form and misunderstanding pattern.",
        }

    def _mock_expert_score(self, seed: Dict[str, Any], payload: Dict[str, Any], expert: str) -> Dict[str, Any]:
        payload_task_type = None
        task_selection = payload.get("task_selection")
        if isinstance(task_selection, dict):
            payload_task_type = task_selection.get("selected_task_type")
        score = 2
        if expert in seed.get("cq_tags", []):
            score = 4
        if expert == "metacognitive" and seed.get("common_misunderstanding"):
            score = max(score, 4)
        if expert == "cognitive" and seed.get("knowledge"):
            score = max(score, 4)
        if expert == "behavioural" and seed.get("typical_scenario"):
            score = max(score, 4)
        if expert == "motivational" and "adapt" in seed.get("common_misunderstanding", "").lower():
            score = max(score, 3)
        if expert == "motivational":
            motivational_blob = " ".join(
                [
                    seed.get("common_misunderstanding", ""),
                    seed.get("typical_scenario", ""),
                    seed.get("knowledge", ""),
                    seed.get("knowledge", ""),
                ]
            ).lower()
            if any(
                token in motivational_blob
                for token in (
                    "adapt",
                    "trust",
                    "relationship",
                    "uncertain",
                    "first time",
                    "initiative",
                    "hesitant",
                    "comfort",
                    "push",
                    "follow up",
                    "engage",
                    "participate",
                )
            ):
                score = max(score, 4)
            else:
                score = max(score, 3 if payload_task_type in ("B", "C") else 2)
        return {
            "expert": expert,
            "score": min(score, 5),
            "reason": f"Mock {expert} expert judged the seed based on its scenario, misunderstanding, and existing CQ hints.",
        }

    def _mock_item_a(self, seed: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        selected_cq = payload["decision"]["selected_cq"]
        difficulty = self._normalize_difficulty(seed.get("difficulty", "medium"))
        countries_or_regions = self._seed_countries_or_regions(seed)
        scenario = seed["typical_scenario"]
        if difficulty == "hard":
            scenario = (
                f"{seed['typical_scenario']} You need a decision before a client deadline, the senior stakeholder is in the room, "
                "and two mid-level colleagues give useful technical detail without clearly owning the final call. Afterward, "
                "a follow-up message sounds warm and cooperative but still uncertain about approval, so the team must decide "
                "whether the signal reflects commitment, hierarchy, or a need for more private alignment."
            )
        elif difficulty == "medium":
            scenario = f"{seed['typical_scenario']} You still need to keep the discussion moving without creating friction."
        return {
            "seed_id": seed["seed_id"],
            "item_id": payload["item_id"],
            "task_type": "A",
            "countries_or_regions": countries_or_regions,
            "scenario": scenario,
            "question": "Which response best handles the task and the cross-cultural situation?",
            "options": {
                "A": "Match the room's relaxed tone quickly, but keep directing your comments mainly through the senior person.",
                "B": f"Read the local interaction pattern, address people in the style used around you, and widen participation accordingly.",
                "C": "Stay formally deferential throughout, then wait for the senior person to invite broader discussion before speaking.",
                "D": "Keep the standard hierarchy and formality settings from the usual rollout, with only a small adjustment to the speaking order.",
            },
            "correct_option": "B",
            "cq_tags": [selected_cq],
            "difficulty": difficulty,
        }

    def _mock_item_b(self, seed: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        selected_cq = payload["decision"]["selected_cq"]
        hints = payload.get("generation_hints", {})
        difficulty = self._normalize_difficulty(seed.get("difficulty", "medium"))
        preferred_label = hints.get("preferred_b_label") or "inappropriate"
        countries_or_regions = self._seed_countries_or_regions(seed)
        local_role = f"{countries_or_regions[0]} local counterpart"
        newcomer_role = "foreign newcomer"
        if preferred_label == "appropriate":
            newcomer_last_line = (
                "I'll keep the public note neutral for now, make the narrower check through the right contact, and send the final version before the deadline."
            )
            reason = (
                "The newcomer uses the indirect cue to avoid the seed misunderstanding and adjusts the timing, channel, "
                "and public commitment around the seed-specific cultural mechanism."
            )
        else:
            newcomer_last_line = (
                "I'll use our standard version and post it in the group thread now; if anyone needs a different arrangement, they can reply before the deadline."
            )
            reason = (
                "The newcomer sounds efficient and polite, but enacts the seed misunderstanding by treating a local execution "
                "cue as optional unless someone objects directly."
            )
        dialogue = [
            {"speaker": "Local", "text": "The deadline is tight, but I would keep that part a little flexible until we hear from the person closest to the setting."},
            {"speaker": "Newcomer", "text": "I can do that, though the shared version is ready and would make the approvals cleaner."},
            {
                "speaker": "Local",
                "text": "Cleaner is helpful. Still, once it is in the group thread, some people may read it as the final arrangement."
            },
            {"speaker": "Newcomer", "text": "Right. I am trying to avoid slowing everyone down while the senior lead is waiting."},
            {
                "speaker": "Local",
                "text": "I can try one more narrow check. We do not need a long discussion, just enough to avoid reworking it publicly later."
            },
            {"speaker": "Newcomer", "text": newcomer_last_line},
        ]
        if difficulty == "hard":
            dialogue.extend(
                [
                    {
                        "speaker": "Local",
                        "text": "That should still leave time for the final approval, as long as the wording does not look settled too early."
                    },
                    {"speaker": "Newcomer", "text": "Understood. I will handle the timing so the update lands after that last check." if preferred_label == "appropriate" else "Understood. I will mark it as provisional, but I still want the full group to see the standard version now."},
                ]
            )
        return {
            "seed_id": seed["seed_id"],
            "item_id": payload["item_id"],
            "task_type": "B",
            "countries_or_regions": countries_or_regions,
            "scenario": (
                f"{seed['typical_scenario']} The team still needs alignment today, a senior stakeholder wants a smooth approval, "
                "and one local cue arrives indirectly rather than as a direct instruction."
            ),
            "roles": {
                "local": local_role,
                "newcomer": newcomer_role,
            },
            "dialogue_round": 4 if difficulty == "hard" else 3,
            "dialogue": dialogue,
            "label": preferred_label,
            "brief_reason": reason,
            "cq_tags": [selected_cq],
            "difficulty": difficulty,
        }

    def _mock_item_c(self, seed: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        selected_cq = payload["decision"]["selected_cq"]
        difficulty = self._normalize_difficulty(seed.get("difficulty", "medium"))
        countries_or_regions = self._seed_countries_or_regions(seed)
        knowledge = seed.get("knowledge", "the seed-specific knowledge")
        common_misunderstanding = seed.get(
            "common_misunderstanding",
            "a generic imported shortcut is treated as sufficient without applying the seed-specific knowledge",
        )
        rubric = [
            {
                "point": "Diagnose the seed-specific cultural mechanism.",
                "score_rule": f"Full credit identifies the execution consequences of this knowledge: {knowledge} Partial credit names culture generally; no credit gives generic collaboration advice.",
            },
            {
                "point": "Reject the polished imported assumption.",
                "score_rule": f"Full credit explains why this shortcut is unsafe here: {common_misunderstanding} Partial credit flags uncertainty vaguely; no credit follows the shortcut unchanged.",
            },
            {
                "point": "Design a concrete execution mechanism.",
                "score_rule": "Full credit translates the cultural mechanism into workflow, timing, wording, placement, routing, or approval steps; partial credit gives broad consultation; no credit stays at attitude level.",
            },
            {
                "point": f"Show selected {selected_cq} CQ in the plan.",
                "score_rule": "Full credit uses the selected CQ dimension in a visible decision or scoring move; partial credit mentions it abstractly; no credit drifts to another CQ dimension.",
            },
        ]
        if difficulty == "hard":
            rubric.append(
                {
                    "point": "Control residual risk under pressure.",
                    "score_rule": "Full credit sets a bounded launch or coordination rule, escalation path, and review trigger tied to the knowledge; partial credit monitors vaguely; no credit assumes the risk is solved.",
                }
            )
        return {
            "seed_id": seed["seed_id"],
            "item_id": payload["item_id"],
            "task_type": "C",
            "countries_or_regions": countries_or_regions,
            "scenario": (
                f"{seed['typical_scenario']} A headquarters team proposes a familiar standard approach because the deadline is close, "
                "the budget is capped, and a senior stakeholder wants visible progress by tomorrow. A local colleague gives an indirect "
                "caution about one implementation detail but does not spell out the rule. You can still change wording, routing, "
                "approval timing, placement, and follow-up checks, but you cannot restart the project."
            ),
            "question": "Propose a concrete plan that applies the local cultural mechanism while keeping the work moving under the deadline.",
            "rubric": rubric,
            "reference_outline": [
                f"Use the seed-specific knowledge as the diagnosis: {knowledge}",
                f"Name and reject the tempting imported shortcut: {common_misunderstanding}",
                "Turn the diagnosis into a concrete workflow, wording, timing, routing, placement, or approval change.",
                f"Make the selected {selected_cq} CQ dimension visible in who checks what, when action proceeds, and how uncertainty is handled.",
                "Set a bounded risk-control rule so deadline pressure does not erase the culture-specific execution requirement.",
            ],
            "cq_tags": [selected_cq],
            "difficulty": difficulty,
        }

    def _normalize_difficulty(self, difficulty: str) -> str:
        if difficulty not in ("easy", "medium", "hard"):
            return "medium"
        return difficulty

    def _seed_countries_or_regions(self, seed: Dict[str, Any]) -> list:
        value = seed.get("countries_or_regions") or seed.get("countries") or seed.get("regions") or ["unspecified"]
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()] or ["unspecified"]
        return [str(value)]
