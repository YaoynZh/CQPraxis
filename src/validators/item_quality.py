import re
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Optional

from src.agents.cq_expert_guides import build_cq_expert_guidance
from src.agents.participant_skills import load_cq_expert_skill
from src.errors import SchemaValidationError
from src.llm.client import LLMClient
from src.models.decision_schema import ModeratorDecision, TaskSelection
from src.models.item_schema import TaskAItem, TaskBItem, TaskCItem
from src.models.seed_schema import SeedRecord


OVERLY_OBVIOUS_A_MARKERS = (
    "ignore the local",
    "rely only on stereotypes",
    "do whatever feels right",
    "it does not matter here",
    "any behavior is fine",
    "because politeness matters more than local expectations",
    "all three are equally valid",
    "all are equally valid",
    "any of the revisions would work",
    "any option would work",
    "treat silence as acceptance",
    "naturally cover",
    "naturally covers",
    "override procurement",
    "bypass the",
    "non-negotiable",
)

SELF_DISCREDITING_A_PATTERNS = (
    r"\bbut\s+(?:risk|risks|risking|may|might|could|would|leaves|creates|bypasses|weakens|exposes)\b",
    r"\balthough\s+(?:this|it|that)\b",
    r"\bthough\s+(?:this|it|that)\b",
    r"\bhowever\b",
    r"\beven if\s+(?:this|that|it)\b",
    r"\bwhile\s+(?:risking|leaving|creating|bypassing|weakening|exposing)\b",
    r"\bprotects?\s+.+\s+but\s+",
)

DIRECTIONAL_SCENARIO_A_PATTERNS = (
    r"\b(?:local|museum|municipal|phnom penh|outreach|producer|reviewer|consultant|liaison|distributor|manager|officer|fixer)\b.{0,90}\b(?:warns?|warned|flags?|flagged|pushes back|objects?|concerns?|says? .{0,35}hard to sell|will likely be ignored|feels? off|issue is bigger|missing the point)\b",
    r"\b(?:warns?|warned|flags?|flagged|pushes back|objects?|concerns?)\b.{0,90}\b(?:local|culture|cultural|audience|community|neighborhood|translation|styling|wording)\b",
    r"\b(?:local|audience|reviewer|producer|distributor|officer|manager|panel|contestants|community|neighborhood)\b.{0,100}\b(?:should be changed|should change|asks? for|requested|reacted most strongly|says? .{0,40}(?:change|avoid|use|keep))\b",
)

DIRECTIONAL_OPTION_A_PATTERNS = (
    r"\b(?:wrong|missing the point|tone-deaf|culturally sensitive|culturally safer|culturally accurate|respectful|authentic|appropriate|inappropriate)\b",
    r"\b(?:feels?|looks?|seems?|reads?)\s+off\b",
)

OVERLY_BLUNT_B_MARKERS = (
    "i don't care",
    "whatever",
    "that's stupid",
    "your way is weird",
    "no need to adapt",
    "i will do it my way",
    "it should be fine anywhere",
    "everyone does this",
)

APPROPRIATE_B_STOCK_SIGNALS = (
    "follow your lead",
    "i'll follow your",
    "i'll hold",
    "i will hold",
    "i'll pause",
    "i will pause",
    "i'll wait for your",
    "i will wait for your",
    "check privately",
    "confirm privately",
    "exact ingredients",
    "exact restrictions",
    "exact names",
    "exact titles",
    "mark that seat",
    "mark it as pending",
    "final wording as pending",
    "after the liaison confirms",
    "after they confirm",
    "once they confirm",
)

INAPPROPRIATE_B_STOCK_SIGNALS = (
    "no need to",
    "i'll just",
    "i will just",
    "skip the",
    "reply-all",
    "copy everyone",
    "keep the line moving",
    "keep it efficient",
    "to save back-and-forth",
    "standard version",
    "standard vegetarian",
    "full group",
    "group thread now",
    "reply before the deadline",
)

LOCAL_DIRECTIONAL_B_PATTERNS = (
    r"\b(?:would rather|rather not|make sure|be careful|before it goes out|before i send|give me a moment|holding the export|not yet|not ready)\b",
    r"\b(?:may not|might not|usually|should not|shouldn't|can't|cannot)\b",
    r"\b(?:once|before|after|as long as)\b.{0,70}\b(?:final|send|print|release|lock|confirm|approve)\b",
    r"\b(?:wait|hold|pause|pending|check|confirm)\b.{0,70}\b(?:first|before|until)\b",
)

FINAL_REVEAL_B_PATTERNS = (
    r"\b(?:just replied|just confirmed|confirmed that|the liaison replied|the liaison just replied)\b",
    r"\b(?:no meat|no fish|no eggs|no alcohol|garlic|onions|halal|kosher)\b",
    r"\b(?:then i'll|i will now|i'll update|i'll send only|i'll keep .* unchanged|done\. i stayed)\b",
    r"\b(?:that way|this way)\b.{0,80}\b(?:protect|avoid|respect|fit|capture|preserve)\b",
    r"\b(?:instead of|rather than|unless|if they|if anyone|only shift|only return|one clear default|most efficient|same file|same visit|standardizing)\b",
    r"\b(?:i'll keep|i will keep|i'll start|i'll lead|i'll let|we'll treat|i built|i marked|i posted|i kept)\b.{0,90}\b(?:before|after|until|instead|rather|unless|if|default|same|separate|formal|handshake|first names|fish|meal|greeting|distance|hosts)\b",
)

DIAGNOSTIC_KEYWORD_B_MARKERS = (
    "left hand",
    "right hand",
    "ok hand",
    "ok emoji",
    "first-name",
    "first name",
    "cheek",
    "kiss",
    "halal",
    "kosher",
    "vegetarian",
    "no meat",
    "no fish",
    "no eggs",
    "alcohol",
    "garlic",
    "onions",
)

FINAL_DECISION_B_CONNECTORS = (
    "instead",
    "rather",
    "still",
    "after",
    "before",
    "until",
    "unless",
    "if ",
    "so ",
    "because",
    "default",
    "standard",
    "first",
    "same",
    "separate",
    "formal",
    "moving",
    "schedule",
    "deadline",
)

SUBTOPIC_FINAL_DIAGNOSTIC_MARKERS = {
    "vegetarian_dietary_norm": ("vegetarian", "no meat", "no fish", "no eggs", "default tray", "special-label"),
    "religious_food_taboo": ("halal", "kosher", "fish option", "left hand", "right hand", "religious setting"),
    "gesture_taboo": ("gesture", "ok hand", "ok emoji", "left hand", "that sign"),
    "respect_address_system": ("first name", "first names", "title", "speaker card", "moderator line"),
    "cheek_kiss_greeting": ("cheek", "kiss"),
    "handshake_greeting": ("handshake",),
    "no_touch_greeting": ("handshake", "warmer greeting"),
    "touch_boundary": ("distance", "handshake", "close"),
    "festival_food_ritual": ("yam", "meal has started", "first usable food", "wrong point"),
    "food_as_gift": ("guest rsvp", "extra item"),
    "shared_dining_etiquette": ("divide it up", "separate", "boxed", "cloth"),
    "food_as_hospitality": ("thank them before", "coffee", "toast"),
    "fasting_feasting_schedule": ("lunch block", "threshold", "religious setting", "yam course"),
    "deference_greeting": ("hosts open", "personal greetings"),
}

COMPLEXITY_CUE_MARKERS = (
    "deadline",
    "timeline",
    "follow-up",
    "stakeholder",
    "manager",
    "client",
    "team",
    "project",
    "decision",
    "approval",
    "relationship",
    "trust",
    "pressure",
    "risk",
    "third party",
    "budget",
    "deadline",
)

AMBIGUITY_CUE_MARKERS = (
    "pause",
    "silent",
    "hesitate",
    "unclear",
    "indirect",
    "vague",
    "follow-up",
    "later",
    "not explicitly",
    "seems",
    "appears",
)

def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _marker_hit_count(text: str, markers) -> int:
    return sum(1 for marker in markers if marker in text)


def _regex_hit_count(text: str, patterns) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text))


class ItemQualityValidator:
    """Validate deterministic item quality and model-judged semantic quality."""

    SEMANTIC_DIMENSIONS = (
        "seed_grounding",
        "cq_alignment",
        "task_format_validity",
        "answer_coherence",
    )

    def __init__(
        self,
        *,
        llm_client: Optional[LLMClient] = None,
        semantic_prompt_path: Optional[Path] = None,
        temperature: float = 0.0,
        max_tokens: int = 1200,
        max_retries: int = 3,
        reasoning_effort: Optional[str] = None,
    ) -> None:
        self.llm_client = llm_client
        self.semantic_prompt_path = semantic_prompt_path
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.reasoning_effort = reasoning_effort

    def validate(
        self,
        item,
        *,
        seed: Optional[SeedRecord] = None,
        task_selection: Optional[TaskSelection] = None,
        decision: Optional[ModeratorDecision] = None,
    ) -> None:
        if isinstance(item, TaskAItem):
            self._validate_task_a(item)
        elif isinstance(item, TaskBItem):
            self._validate_task_b(item)
        elif isinstance(item, TaskCItem):
            self._validate_task_c(item)
        else:
            raise SchemaValidationError("Unsupported item type for quality validation.")

        if self.llm_client is not None:
            if self.semantic_prompt_path is None or seed is None or task_selection is None or decision is None:
                raise SchemaValidationError("Semantic validation requires the seed, moderator analysis, and CQ decision.")
            self._validate_semantics(
                item=item,
                seed=seed,
                task_selection=task_selection,
                decision=decision,
            )

    def _validate_semantics(
        self,
        *,
        item,
        seed: SeedRecord,
        task_selection: TaskSelection,
        decision: ModeratorDecision,
    ) -> None:
        response = self.llm_client.generate_json(
            prompt_path=self.semantic_prompt_path,
            payload={
                "seed": seed.summary(),
                "moderator_analysis": task_selection.to_dict(),
                "selected_task_type": decision.selected_task_type,
                "selected_cq": decision.selected_cq,
                "selected_cq_guidance": build_cq_expert_guidance(decision.selected_cq),
                "selected_cq_skill": load_cq_expert_skill(decision.selected_cq),
                "item": item.to_dict(),
            },
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
            reasoning_effort=self.reasoning_effort,
        )

        failures = []
        for dimension in self.SEMANTIC_DIMENSIONS:
            result = response.get(dimension)
            if not isinstance(result, dict):
                raise SchemaValidationError(f"Semantic validator omitted object field: {dimension}.")
            passed = result.get("pass")
            reason = result.get("reason")
            if not isinstance(passed, bool) or not isinstance(reason, str) or not reason.strip():
                raise SchemaValidationError(
                    f"Semantic validator returned an invalid result for {dimension}."
                )
            if not passed:
                failures.append(f"{dimension}: {reason.strip()}")

        overall_pass = response.get("overall_pass")
        if not isinstance(overall_pass, bool):
            raise SchemaValidationError("Semantic validator omitted boolean field: overall_pass.")
        computed_pass = not failures
        if overall_pass != computed_pass:
            raise SchemaValidationError("Semantic validator returned inconsistent dimension and overall results.")
        if failures:
            feedback = response.get("feedback")
            if isinstance(feedback, str) and feedback.strip():
                failures.append(f"revision: {feedback.strip()}")
            raise SchemaValidationError("Semantic quality validation failed: " + " | ".join(failures))

    def _validate_task_a(self, item: TaskAItem) -> None:
        option_lengths = {key: _word_count(text) for key, text in item.options.items()}
        shortest = min(option_lengths.values())
        longest = max(option_lengths.values())
        if shortest < 8:
            raise SchemaValidationError("Task A options are too short; make all four options substantive and plausible.")
        if shortest == 0 or longest / shortest > 1.3:
            raise SchemaValidationError(
                "Task A option lengths are too uneven; keep the four options closer in length and information density."
            )

        correct_length = option_lengths[item.correct_option]
        distractor_lengths = [length for key, length in option_lengths.items() if key != item.correct_option]
        if correct_length > mean(distractor_lengths) * 1.15:
            raise SchemaValidationError(
                "Task A correct option is noticeably longer than the distractors; reduce that giveaway cue."
            )

        for option_key, text in item.options.items():
            normalized = _normalize_text(text)
            if any(marker in normalized for marker in OVERLY_OBVIOUS_A_MARKERS):
                raise SchemaValidationError(
                    f"Task A option {option_key} is too obviously wrong; rewrite it as a plausible near-miss."
                )
            if any(re.search(pattern, normalized) for pattern in SELF_DISCREDITING_A_PATTERNS):
                raise SchemaValidationError(
                    f"Task A option {option_key} explains its own flaw; write it as a self-advocating candidate action."
                )
            if any(re.search(pattern, normalized) for pattern in DIRECTIONAL_OPTION_A_PATTERNS):
                raise SchemaValidationError(
                    f"Task A option {option_key} contains evaluative direction cues; make all options surface-plausible."
                )

        scenario_text = _normalize_text(item.scenario)
        if any(re.search(pattern, scenario_text) for pattern in DIRECTIONAL_SCENARIO_A_PATTERNS):
            raise SchemaValidationError(
                "Task A scenario contains directional stakeholder feedback; use neutral facts and competing constraints instead."
            )
        if item.difficulty in ("medium", "hard") and _word_count(item.scenario) < 35:
            raise SchemaValidationError("Task A items labeled medium or hard need sufficient scenario context.")
        if item.difficulty == "hard":
            if not any(marker in scenario_text for marker in COMPLEXITY_CUE_MARKERS):
                raise SchemaValidationError(
                    "Task A items labeled hard need a concrete non-cultural constraint such as task pressure, hierarchy, stakeholder risk, or relationship maintenance."
                )
            close_distractors = sum(
                1 for key, length in option_lengths.items() if key != item.correct_option and abs(length - correct_length) <= 3
            )
            if close_distractors < 2:
                raise SchemaValidationError("Task A items labeled hard need at least two strong distractors close in length to the correct option.")

    def _validate_task_b(self, item: TaskBItem) -> None:
        newcomer_texts = [
            turn["text"]
            for turn in item.dialogue
            if _normalize_text(turn["speaker"]).startswith("newcomer")
        ]
        if not newcomer_texts:
            raise SchemaValidationError("Task B dialogue must include newcomer turns.")

        joined = " ".join(_normalize_text(text) for text in newcomer_texts)
        self._validate_task_b_surface_signals(item, joined)

        if item.label != "inappropriate":
            self._validate_task_b_difficulty(item)
            return

        if any(marker in joined for marker in OVERLY_BLUNT_B_MARKERS):
            raise SchemaValidationError(
                "Task B inappropriate dialogue is too blunt; make the mismatch subtler and more realistically plausible."
            )

        last_turn = _normalize_text(newcomer_texts[-1])
        if "!" in newcomer_texts[-1] or newcomer_texts[-1].isupper():
            raise SchemaValidationError(
                "Task B inappropriate dialogue is too overtly emphatic; keep the mismatch understated."
            )
        if "sorry" not in joined and any(token in last_turn for token in ("fine here too", "i'll just", "i always")):
            raise SchemaValidationError(
                "Task B inappropriate dialogue reads too directly as a wrong answer; make it a subtler miscalibration."
            )
        self._validate_task_b_difficulty(item)

    def _validate_task_b_surface_signals(self, item: TaskBItem, newcomer_text: str) -> None:
        if item.difficulty != "hard":
            return
        if item.label == "appropriate" and _marker_hit_count(newcomer_text, APPROPRIATE_B_STOCK_SIGNALS) >= 1:
            raise SchemaValidationError(
                "Task B dialogue labeled hard uses stock patience/checking cues; make the label depend on a culture-specific execution detail instead."
            )
        if item.label == "inappropriate" and _marker_hit_count(newcomer_text, INAPPROPRIATE_B_STOCK_SIGNALS) >= 1:
            raise SchemaValidationError(
                "Task B dialogue labeled hard uses stock efficiency/refusal cues; make the mismatch subtler and culture-specific."
            )
        local_text = " ".join(
            _normalize_text(turn["text"])
            for turn in item.dialogue
            if _normalize_text(turn["speaker"]).startswith("local")
        )
        final_turn = _normalize_text(item.dialogue[-1]["text"]) if item.dialogue else ""
        scenario_text = _normalize_text(item.scenario)
        full_text = " ".join((scenario_text, local_text, newcomer_text))

        if _regex_hit_count(local_text, LOCAL_DIRECTIONAL_B_PATTERNS) >= 3:
            raise SchemaValidationError(
                "Task B dialogue labeled hard has too many directional local cues; reduce answer-key choreography and add mixed evidence."
            )
        if _regex_hit_count(final_turn, FINAL_REVEAL_B_PATTERNS) >= 1:
            raise SchemaValidationError(
                "Task B item labeled hard has a final turn that reveals or summarizes the answer; keep the decisive cultural fact implicit."
            )
        if _word_count(final_turn) >= 16 and any(marker in final_turn for marker in FINAL_DECISION_B_CONNECTORS):
            raise SchemaValidationError(
                "Task B item labeled hard has a long final decision summary; keep the ending shorter and less label-revealing."
            )
        subtopic_markers = SUBTOPIC_FINAL_DIAGNOSTIC_MARKERS.get(item.subtopic, ())
        if subtopic_markers and any(marker in final_turn for marker in subtopic_markers):
            raise SchemaValidationError(
                "Task B item labeled hard names the subtopic's diagnostic cue in the final turn; move the cue earlier and make it less explicit."
            )
        if subtopic_markers and any(marker in newcomer_text for marker in subtopic_markers):
            raise SchemaValidationError(
                "Task B item labeled hard names the subtopic's diagnostic cue in the newcomer action; encode the mechanism through less obvious operational detail."
            )
        if _marker_hit_count(full_text, DIAGNOSTIC_KEYWORD_B_MARKERS) >= 2:
            raise SchemaValidationError(
                "Task B item labeled hard foregrounds too many diagnostic cultural keywords; camouflage the knowledge with ordinary operational details."
            )

    def _validate_task_b_difficulty(self, item: TaskBItem) -> None:
        dialogue_text = " ".join(turn["text"] for turn in item.dialogue)
        normalized_dialogue = _normalize_text(dialogue_text)
        if item.difficulty == "hard" and item.dialogue_round < 3:
            raise SchemaValidationError("Task B items labeled hard should use at least 3 dialogue rounds.")
        if item.difficulty in ("medium", "hard") and not any(marker in normalized_dialogue for marker in AMBIGUITY_CUE_MARKERS):
            raise SchemaValidationError(
                "Task B items labeled medium or hard should contain some ambiguity, indirectness, or incomplete signal in the dialogue."
            )
        if item.difficulty == "hard" and _word_count(item.scenario) < 30:
            raise SchemaValidationError("Task B items labeled hard need a richer scenario with a concrete interaction objective.")

    def _validate_task_c(self, item: TaskCItem) -> None:
        if item.difficulty in ("medium", "hard") and len(item.reference_outline) < 4:
            raise SchemaValidationError("Task C items labeled medium or hard need a fuller reference outline.")
        if item.difficulty == "hard":
            if len(item.rubric) < 5:
                raise SchemaValidationError("Task C items labeled hard need at least 5 rubric points.")
            if _word_count(item.scenario) < 45:
                raise SchemaValidationError("Task C items labeled hard need a richer scenario with real execution constraints.")
            scenario_text = _normalize_text(item.scenario)
            if not any(marker in scenario_text for marker in COMPLEXITY_CUE_MARKERS):
                raise SchemaValidationError(
                    "Task C items labeled hard need concrete execution constraints such as deadline, stakeholder pressure, hierarchy, trust risk, budget, or approval."
                )
