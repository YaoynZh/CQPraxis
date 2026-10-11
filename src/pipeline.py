import random
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.agents.factory import build_agents
from src.agents.participant_skills import load_cq_expert_skill
from src.agents.cq_expert_guides import build_cq_expert_guidance
from src.agents.task_a_item_rules import build_task_a_item_rules
from src.agents.task_bc_item_rules import build_task_b_item_rules, build_task_c_item_rules
from src.config import DEFAULT_CONFIG_DIR, DistributionConfig, GenerationConfig, ModelConfig, PROJECT_ROOT
from src.errors import RejectionError, SchemaValidationError
from src.loaders.seed_loader import SeedLoader
from src.models.base import ALLOWED_TASK_TYPES
from src.models.decision_schema import ExpertScore, ModeratorDecision, RejectedRecord, TaskSelection
from src.models.item_schema import BaseItem, TaskAItem
from src.models.seed_schema import SeedRecord
from src.stats.balancing import BalancingRules
from src.stats.distribution_tracker import DistributionTracker
from src.utils.ids import build_item_id
from src.utils.io import append_jsonl, ensure_dir
from src.utils.logger import build_logger
from src.validators.item_quality import ItemQualityValidator
from src.llm.client import LLMClient


@dataclass(frozen=True)
class PipelinePaths:
    input_path: Path
    outputs_dir: Path
    rejected_dir: Path
    logs_dir: Path
    items_a_path: Path
    items_b_path: Path
    items_c_path: Path
    all_items_path: Path
    rejected_path: Path
    decisions_path: Path
    expert_scores_path: Path
    generation_trace_path: Path
    run_log_path: Path

    @classmethod
    def create(cls, input_path: Path, output_root: Optional[Path] = None) -> "PipelinePaths":
        if output_root is None:
            data_dir = PROJECT_ROOT / "data"
        else:
            data_dir = output_root if output_root.is_absolute() else PROJECT_ROOT / output_root
        data_dir = ensure_dir(data_dir)
        outputs_dir = ensure_dir(data_dir / "outputs")
        rejected_dir = ensure_dir(data_dir / "rejected")
        logs_dir = ensure_dir(data_dir / "logs")
        return cls(
            input_path=input_path,
            outputs_dir=outputs_dir,
            rejected_dir=rejected_dir,
            logs_dir=logs_dir,
            items_a_path=outputs_dir / "items_A.jsonl",
            items_b_path=outputs_dir / "items_B.jsonl",
            items_c_path=outputs_dir / "items_C.jsonl",
            all_items_path=outputs_dir / "all_items.jsonl",
            rejected_path=rejected_dir / "rejected_items.jsonl",
            decisions_path=logs_dir / "decisions.jsonl",
            expert_scores_path=logs_dir / "expert_scores.jsonl",
            generation_trace_path=logs_dir / "generation_trace.jsonl",
            run_log_path=logs_dir / "run.log",
        )


class GenerationPipeline:
    def __init__(
        self,
        input_path: Optional[Path] = None,
        output_root: Optional[Path] = None,
        config_dir: Path = DEFAULT_CONFIG_DIR,
        prompt_dir: Optional[Path] = None,
        mock_llm: bool = False,
    ):
        input_file = input_path or (PROJECT_ROOT / "data" / "seed_ex.jsonl")
        self.paths = PipelinePaths.create(input_file, output_root=output_root)
        self.logger = build_logger("multiculture.pipeline", self.paths.run_log_path)
        self.model_config = ModelConfig.load(config_dir)
        self.generation_config = GenerationConfig.load(config_dir)
        self.distribution_config = DistributionConfig.load(config_dir)
        self.seed_loader = SeedLoader(self.paths.input_path)
        self.llm_client = LLMClient.from_env(
            default_max_retries=self.generation_config.default_max_retries,
            mock_mode=mock_llm,
        )
        if self.llm_client.mock_mode:
            self.logger.warning(
                "LLM client is running in mock mode. No external API calls will be made. "
                "This is usually caused by --mock-llm or MCG_USE_MOCK_LLM=true."
            )
        else:
            self.logger.info("LLM client is running in live mode against %s", self.llm_client.base_url)
        self.prompt_dir = prompt_dir or (PROJECT_ROOT / "src" / "llm" / "prompts")
        self.agents = build_agents(
            llm_client=self.llm_client,
            prompt_dir=self.prompt_dir,
            model_config=self.model_config,
            generation_config=self.generation_config,
        )
        self.tracker = DistributionTracker.from_output_file(self.paths.all_items_path)
        self.balancing = BalancingRules(self.distribution_config)
        self.item_quality_validator = ItemQualityValidator(
            llm_client=self.llm_client,
            semantic_prompt_path=self.prompt_dir / "validate_item.md",
            temperature=self.model_config.validator.temperature,
            max_tokens=self.model_config.validator.max_tokens,
            max_retries=self.generation_config.default_max_retries,
            reasoning_effort=self.model_config.validator.reasoning_effort,
        )

    def run_one(
        self,
        seed_id: str,
        allowed_task_types: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        raw_seed = self.seed_loader.get_raw_by_id(seed_id)
        if raw_seed is None:
            raise ValueError(f"Seed not found: {seed_id}")
        return self._process_seed(
            raw_seed=raw_seed,
            allowed_task_types=self._normalize_task_types(allowed_task_types),
        )

    def run_batch(
        self,
        target_total_items: Optional[int] = None,
        allowed_task_types: Optional[Iterable[str]] = None,
        coverage_input_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        allowed = self._normalize_task_types(allowed_task_types)
        accepted = 0
        rejected = 0
        processed = 0
        target = target_total_items or self.generation_config.target_total_items
        if target < 1:
            raise ValueError("target_total_items must be at least 1.")

        raw_seeds = list(self.seed_loader.iter_raw())
        coverage_seeds = (
            list(SeedLoader(coverage_input_path).iter_raw())
            if coverage_input_path is not None
            else raw_seeds
        )
        cultural_domains, regions = self._coverage_categories(coverage_seeds)
        coverage = self.balancing.coverage_status(
            tracker=self.tracker,
            target_total_items=target,
            allowed_task_types=allowed,
            cultural_domains=cultural_domains,
            regions=regions,
        )

        for raw_seed in raw_seeds:
            if coverage["satisfied"]:
                break
            result = self._process_seed(
                raw_seed=raw_seed,
                allowed_task_types=allowed,
            )
            processed += 1
            if result["status"] == "accepted":
                accepted += 1
                coverage = self.balancing.coverage_status(
                    tracker=self.tracker,
                    target_total_items=target,
                    allowed_task_types=allowed,
                    cultural_domains=cultural_domains,
                    regions=regions,
                )
            else:
                rejected += 1

        if coverage["satisfied"]:
            self.logger.info(
                "Distribution coverage satisfied with %s candidates for target N=%s (%s extras).",
                coverage["candidate_items"],
                target,
                coverage["extra_candidates"],
            )
        else:
            self.logger.warning(
                "Input seeds were exhausted before distribution coverage was satisfied for target N=%s.",
                target,
            )

        return {
            "mode": "run-batch",
            "processed": processed,
            "accepted": accepted,
            "rejected": rejected,
            "target_total_items": target,
            "distribution_satisfied": coverage["satisfied"],
            "candidate_items": coverage["candidate_items"],
            "extra_candidates": coverage["extra_candidates"],
            "coverage": coverage["dimensions"],
            "all_items_path": str(self.paths.all_items_path),
            "rejected_path": str(self.paths.rejected_path),
            "llm_mode": "mock" if self.llm_client.mock_mode else "live",
        }

    def _process_seed(
        self,
        raw_seed: Dict[str, Any],
        allowed_task_types: List[str],
    ) -> Dict[str, Any]:
        seed_id = str(raw_seed.get("seed_id", "UNKNOWN"))
        trace: Dict[str, Any] = {
            "seed_id": seed_id,
            "raw_seed": raw_seed,
        }
        try:
            seed = SeedRecord.from_dict(raw_seed)
            trace["seed"] = seed.to_dict()

            snapshot = self.tracker.snapshot()
            task_selection = self._select_task(seed, snapshot, allowed_task_types)
            trace["task_selection"] = task_selection.to_dict()

            expert_scores = self._score_experts(seed, snapshot, task_selection)
            trace["expert_scores"] = [entry.to_dict() for entry in expert_scores]

            decision = self.balancing.build_decision(
                seed=seed,
                task_selection=task_selection,
                expert_scores=expert_scores,
                snapshot=snapshot,
                allowed_task_types=allowed_task_types,
            )
            trace["decision"] = decision.to_dict()
            self._write_decision(seed, task_selection, decision)

            item = self._generate_item(seed, task_selection, decision, expert_scores)
            trace["generated_item"] = item.to_dict()
            self._write_item(item)
            self.tracker.register_item(item)

            append_jsonl(
                self.paths.generation_trace_path,
                {
                    "seed_id": seed.seed_id,
                    "status": "accepted",
                    "trace": trace,
                },
            )
            return {
                "status": "accepted",
                "seed_id": seed.seed_id,
                "item_id": item.item_id,
                "task_type": item.task_type,
                "cq_tag": item.cq_tags[0],
                "llm_mode": "mock" if self.llm_client.mock_mode else "live",
            }

        except Exception as exc:
            self.logger.warning("Rejected seed %s: %s", seed_id, exc)
            rejection = self._build_rejection(seed_id=seed_id, raw_seed=raw_seed, trace=trace, error=exc)
            self._write_rejection(rejection)
            append_jsonl(
                self.paths.generation_trace_path,
                {
                    "seed_id": seed_id,
                    "status": "rejected",
                    "trace": trace,
                    "rejection": rejection.to_dict(),
                },
            )
            return {
                "status": "rejected",
                "seed_id": seed_id,
                "stage": rejection.stage,
                "reason": rejection.reason,
                "llm_mode": "mock" if self.llm_client.mock_mode else "live",
            }

    def _coverage_categories(self, raw_seeds: Iterable[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        cultural_domains = set()
        regions = set()
        for raw_seed in raw_seeds:
            try:
                seed = SeedRecord.from_dict(raw_seed)
            except SchemaValidationError:
                continue
            cultural_domains.add(seed.major_topic)
            regions.add(seed.regions)
        if not cultural_domains or not regions:
            raise ValueError("Coverage input must contain at least one valid cultural domain and region.")
        return sorted(cultural_domains), sorted(regions)

    def _select_task(
        self,
        seed: SeedRecord,
        snapshot,
        allowed_task_types: List[str],
    ) -> TaskSelection:
        moderator = self.agents["moderator"]
        return moderator.select_task(seed=seed, snapshot=snapshot, allowed_task_types=allowed_task_types)

    def _score_experts(self, seed: SeedRecord, snapshot, task_selection: TaskSelection) -> List[ExpertScore]:
        scores: List[ExpertScore] = []
        for expert in self.agents["experts"]:
            score = expert.score_seed(seed, snapshot, task_selection)
            scores.append(score)
            append_jsonl(
                self.paths.expert_scores_path,
                {
                    "seed_id": seed.seed_id,
                    **score.to_dict(),
                },
            )
        return scores

    def _generate_item(
        self,
        seed: SeedRecord,
        task_selection: TaskSelection,
        decision: ModeratorDecision,
        expert_scores: List[ExpertScore],
    ) -> BaseItem:
        selected_expert_score = next(score for score in expert_scores if score.expert == decision.selected_cq)
        validation_feedback: Optional[str] = None
        attempts = self.generation_config.max_quality_attempts
        item_generator = self.agents["item_generator"]
        for attempt_number in range(1, attempts + 1):
            target_a_correct_option: Optional[str] = None
            item_index = self.tracker.next_item_index(decision.selected_task_type)
            item_id = build_item_id(decision.selected_task_type, item_index)
            generation_hints: Dict[str, Any] = {}
            generation_hints["selected_cq_reason"] = selected_expert_score.reason
            generation_hints["selected_cq_score"] = selected_expert_score.score
            if decision.selected_task_type == "A":
                target_a_correct_option, target_random_value = self._random_task_a_correct_option()
                generation_hints["target_a_correct_option_random"] = target_random_value
                generation_hints.update(
                    build_task_a_item_rules(
                        seed=seed,
                        item_index=item_index,
                        cq_tag=decision.selected_cq,
                        selected_expert_reason=selected_expert_score.reason,
                        selected_expert_score=selected_expert_score.score,
                        target_correct_option=target_a_correct_option,
                    )
                )
            if decision.selected_task_type in {"B", "C"}:
                generation_hints["selected_cq_expert_context"] = self._selected_cq_expert_context(
                    cq_tag=decision.selected_cq,
                    selected_expert_score=selected_expert_score,
                )
                if decision.selected_task_type == "B":
                    generation_hints.update(
                        build_task_b_item_rules(
                            seed=seed,
                            cq_tag=decision.selected_cq,
                            selected_expert_reason=selected_expert_score.reason,
                            selected_expert_score=selected_expert_score.score,
                        )
                    )
                else:
                    generation_hints.update(
                        build_task_c_item_rules(
                            seed=seed,
                            cq_tag=decision.selected_cq,
                            selected_expert_reason=selected_expert_score.reason,
                            selected_expert_score=selected_expert_score.score,
                        )
                    )
            if decision.selected_task_type == "B":
                preferred_label, label_random_value = self._random_task_b_label()
                generation_hints["b_label_balance_context"] = {
                    "scope": "random",
                    "subtopic": seed.subtopic,
                    "random_value": label_random_value,
                    "purpose": "Task B label is fixed by random draw before generation.",
                }
                generation_hints["preferred_b_label"] = preferred_label
            try:
                item = item_generator.generate_item(
                    seed=seed,
                    decision=decision,
                    moderator_analysis=task_selection,
                    selected_expert_score=selected_expert_score,
                    item_id=item_id,
                    generation_hints=generation_hints,
                    validation_feedback=validation_feedback,
                )
            except SchemaValidationError as exc:
                validation_feedback = str(exc)
                self.logger.warning(
                    "Generated item for seed %s failed schema validation on attempt %s/%s: %s",
                    seed.seed_id,
                    attempt_number,
                    attempts,
                    exc,
                )
                continue
            item = self._attach_seed_metadata(item, seed)
            item = self._assign_system_item_id(item, item_id)
            if target_a_correct_option:
                item = self._place_task_a_correct_option(item, target_a_correct_option)

            try:
                self._validate_generated_item(seed, task_selection, decision, item)
            except SchemaValidationError as exc:
                validation_feedback = str(exc)
                self.logger.warning(
                    "Generated item %s for seed %s failed quality validation on attempt %s/%s: %s",
                    item.item_id,
                    seed.seed_id,
                    attempt_number,
                    attempts,
                    exc,
                )
                continue

            if self.tracker.is_duplicate(item.to_dict()):
                raise RejectionError("dedupe", "Generated item duplicates an existing accepted item.")
            self.logger.info(
                "Generated item %s for seed %s passed quality validation on attempt %s/%s.",
                item.item_id,
                seed.seed_id,
                attempt_number,
                attempts,
            )
            return item
        raise RejectionError(
            "item_generation",
            f"Item failed schema or quality validation after {attempts} attempts: "
            f"{validation_feedback or 'no validation detail was returned.'}",
        )

    def _selected_cq_expert_context(
        self,
        *,
        cq_tag: str,
        selected_expert_score: ExpertScore,
    ) -> Dict[str, Any]:
        return {
            "cq": cq_tag,
            "score_reason": selected_expert_score.reason,
            "compact_guidance": build_cq_expert_guidance(cq_tag),
            "skill": load_cq_expert_skill(cq_tag),
            "token_policy": "Generation receives only the selected CQ expert skill, not the full expert panel.",
        }

    def _random_task_a_correct_option(self) -> tuple[str, float]:
        value = random.random()
        if value < 0.25:
            return "A", value
        if value < 0.5:
            return "B", value
        if value < 0.75:
            return "C", value
        return "D", value

    def _random_task_b_label(self) -> tuple[str, float]:
        value = random.random()
        return ("appropriate" if value < 0.5 else "inappropriate"), value

    def _place_task_a_correct_option(self, item: BaseItem, target_correct_option: str) -> BaseItem:
        if not isinstance(item, TaskAItem) or item.correct_option == target_correct_option:
            return item
        options = dict(item.options)
        current = item.correct_option
        options[current], options[target_correct_option] = options[target_correct_option], options[current]
        return replace(item, options=options, correct_option=target_correct_option)

    def _assign_system_item_id(self, item: BaseItem, item_id: str) -> BaseItem:
        if item.item_id == item_id:
            return item
        return replace(item, item_id=item_id)

    def _attach_seed_metadata(self, item: BaseItem, seed: SeedRecord) -> BaseItem:
        return replace(
            item,
            seed_id=seed.seed_id,
            regions=seed.regions,
            countries=seed.countries,
            major_topic=seed.major_topic,
            subtopic=seed.subtopic,
            countries_or_regions=seed.countries_or_regions,
        )

    def _validate_generated_item(
        self,
        seed: SeedRecord,
        task_selection: TaskSelection,
        decision: ModeratorDecision,
        item: BaseItem,
    ) -> None:
        if item.seed_id != seed.seed_id:
            raise SchemaValidationError("Generated item seed_id does not match the source seed.")
        if item.task_type != decision.selected_task_type:
            raise SchemaValidationError("Generated item task_type does not match the selected task type.")
        if item.cq_tags[0] != decision.selected_cq:
            raise SchemaValidationError("Generated item CQ tag does not match the selected CQ.")
        missing_countries = [country for country in seed.countries_or_regions if country not in item.countries_or_regions]
        if missing_countries:
            raise SchemaValidationError("Generated item dropped the seed's core country or region context.")
        self.item_quality_validator.validate(
            item,
            seed=seed,
            task_selection=task_selection,
            decision=decision,
        )

    def _write_item(self, item: BaseItem) -> None:
        payload = item.to_dict()
        append_jsonl(self.paths.all_items_path, payload)
        if item.task_type == "A":
            append_jsonl(self.paths.items_a_path, payload)
        elif item.task_type == "B":
            append_jsonl(self.paths.items_b_path, payload)
        else:
            append_jsonl(self.paths.items_c_path, payload)

    def _write_decision(self, seed: SeedRecord, task_selection: TaskSelection, decision: ModeratorDecision) -> None:
        append_jsonl(
            self.paths.decisions_path,
            {
                "seed_id": seed.seed_id,
                "task_selection": task_selection.to_dict(),
                "decision": decision.to_dict(),
            },
        )

    def _build_rejection(
        self,
        seed_id: str,
        raw_seed: Dict[str, Any],
        trace: Dict[str, Any],
        error: Exception,
    ) -> RejectedRecord:
        if isinstance(error, RejectionError):
            stage = error.stage
            reason = error.reason
        elif isinstance(error, SchemaValidationError):
            stage = "schema_validation"
            reason = str(error)
        else:
            stage = "runtime"
            reason = str(error)
        return RejectedRecord.create(
            seed_id=seed_id,
            stage=stage,
            reason=reason,
            payload=raw_seed,
            trace=trace,
        )

    def _write_rejection(self, rejection: RejectedRecord) -> None:
        append_jsonl(self.paths.rejected_path, rejection.to_dict())

    def _normalize_task_types(self, allowed_task_types: Optional[Iterable[str]]) -> List[str]:
        task_types = list(allowed_task_types or self.generation_config.allow_task_types)
        invalid = [task_type for task_type in task_types if task_type not in ALLOWED_TASK_TYPES]
        if invalid:
            raise ValueError(f"Unsupported task types: {invalid}")
        return task_types
