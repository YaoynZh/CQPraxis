import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from src.agents.cq_expert_guides import build_cq_expert_guidance
from src.agents.participant_skills import load_cq_expert_skill
from src.models.seed_schema import SeedRecord


@dataclass(frozen=True)
class AFormatHint:
    name: str
    structure: str
    question_goal: str
    option_design: List[str]
    design_checks: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


FORMAT_CATALOG = [
    AFormatHint(
        name="fact_or_mapping_discriminator",
        structure=(
            "Present a short practical context, then ask which concrete claim or direction should guide the work. "
            "The scenario gives the trigger, not the decisive cultural fact."
        ),
        question_goal="Test a seed-specific fact, mapping, direction, sequence, body area, status cue, occasion, region, or degree.",
        option_design=[
            "All four options sound professional, culturally attentive, and similarly localized.",
            "All options compete on one factual dimension, not on four management styles.",
            "Distractors are correct-looking transplants from a nearby market, global default, or same culture at the wrong scope.",
            "One distractor should be common_misunderstanding written as a polished near-miss.",
            "The correct option must not be the only local, balanced, optional, or cautious wording.",
        ],
        design_checks=[
            "Scenario alone does not reveal the answer.",
            "Options alone do not reveal the answer by tone.",
            "At least one distractor is half-right but mapped to the wrong cue.",
        ],
    ),
    AFormatHint(
        name="counterbalanced_override",
        structure=(
            "Present a local-sounding request or adaptation pressure, then ask which bounded decision should be made. "
            "The correct answer may be standardization, refusal, or a narrow exception."
        ),
        question_goal="Break the shortcut that local adaptation is always correct when health, compliance, ethics, or false representation is at stake.",
        option_design=[
            "At least two options sound locally respectful.",
            "At least one wrong option localizes more than the correct option.",
            "The correct option should not advertise moral superiority.",
            "Wrong options fail through the seed fact, not through rude or careless language.",
        ],
        design_checks=[
            "A local-looking option is tempting but wrong.",
            "A standardized option can be correct.",
            "Surface respectfulness is not a reliable answer cue.",
        ],
    ),
    AFormatHint(
        name="best_next_step",
        structure=(
            "Present a concrete decision moment with local cues, imported assumptions, deadline or stakeholder pressure, "
            "and one detail that complicates standard caution."
        ),
        question_goal="Ask which next step should be taken now; the best step may be active, direct, or conditional rather than wait-and-see.",
        option_design=[
            "Scenario cues must be neutral facts, not a local stakeholder warning that points toward the answer.",
            "All options must compete on the same decision layer and deliverable.",
            "All options are trade-offs, not good/bad contrasts.",
            "At least two options should protect the same generic virtue but in different concrete directions.",
            "All distractors should be good moves in another mainstream culture, nearby market, legal system, or professional frame.",
            "One distractor should be the seed common_misunderstanding rewritten as a polished professional rationale.",
            "Wrong answers should look faster, cheaper, more scalable, or easier to report than the correct answer.",
            "At least one wrong answer should look more careful or more interventionist than the correct answer.",
            "Write options as proposed actions, not as action-plus-warning commentary.",
        ],
        design_checks=[
            "Correct answer is not always the largest action.",
            "Use three bound trap origins: nearby-market practice, KPI efficiency logic, and a valid outside norm used at the wrong scope.",
            "Make every scenario constraint improve or weaken at least two options.",
        ],
    ),
    AFormatHint(
        name="concrete_revision_or_wording",
        structure="Present a draft message, script, policy line, agenda move, or briefing sentence with cross-cultural risk and a non-obvious local constraint.",
        question_goal="Ask which revision, wording, or briefing line should be approved; avoid making the broadest or safest wording automatically best.",
        option_design=[
            "Do not include a local reviewer saying the draft is wrong, off, hard to sell, or culturally sensitive.",
            "All options must be alternative wordings or message frames, not mixed copy/channel/research/governance moves.",
            "All options sound professionally defensible and each loses something.",
            "Do not make the correct wording the only nuanced, lawful, or inclusive one.",
            "If the correct wording gives choice, local sign-off, or cultural caution, a distractor should do the same at the wrong scope or direction.",
            "Make one wrong wording embody the seed common_misunderstanding in benevolent or brand-safe language.",
            "Do not signal which option is local by making it the only one that names the country or culture.",
            "Avoid self-discrediting clauses such as 'but this risks' or 'although it may'.",
            "Avoid naming the seed's cultural label; use behavioral, visual, timing, or workflow cues instead.",
        ],
        design_checks=[
            "Compete execution cost, localization accuracy, stakeholder comfort, KPI reporting, and operational deadline.",
            "Let the correct wording be less efficient or less polished than attractive distractors.",
        ],
    ),
    AFormatHint(
        name="diagnostic_evidence_selection",
        structure="Present a tentative action or interpretation, then ask which concrete observation would justify acting, revising, or rejecting generic caution.",
        question_goal="Test diagnostic value, not general relevance; the best evidence may support moving forward rather than delaying.",
        option_design=[
            "Observations must be neutral data points; none should explicitly say a choice is wrong or acceptable.",
            "All observations are relevant and tempting.",
            "All options must be observations of the same kind, not mixed evidence, action, and authority checks.",
            "Only one changes the decision priority because of seed-specific culture knowledge.",
            "At least one wrong observation should support the common_misunderstanding in a way that sounds professionally plausible.",
            "One distractor should be vivid but less diagnostic.",
            "One distractor should support a broadly sensible but wrong imported cultural or professional heuristic.",
            "The decisive clue should be about execution behavior, not naming the cultural term.",
        ],
        design_checks=[
            "Separate cultural signal from generic business noise.",
            "Use intra-group or stakeholder variation to make the obvious clue insufficient or misleading.",
        ],
    ),
    AFormatHint(
        name="response_ordering",
        structure="Present four candidate sequences using similar action building blocks in different order or channel, with one active move required somewhere.",
        question_goal="Ask which sequence best handles timing, audience, task movement, and cultural risk without defaulting to broad consultation.",
        option_design=[
            "Use factual constraints rather than a local person explaining which sequence is culturally expected.",
            "Reuse overlapping actions across options to reduce keyword elimination.",
            "Wrong answers fail through order, channel, audience, or priority rather than rude content.",
            "Each wrong sequence should be defensible under a different imported culture, law, or institutional rhythm.",
            "One wrong sequence should express common_misunderstanding as an efficient, inclusive, deferential, or legally tidy process.",
            "Make the wrong sequences smoother or more KPI-friendly than the correct local sequence.",
            "At least one wrong sequence should include more review or consultation than the correct sequence.",
        ],
        design_checks=[
            "One sequence is clearer but premature.",
            "One sequence is respectful but too passive or too late.",
            "One sequence follows a true rule at the wrong stage.",
        ],
    ),
    AFormatHint(
        name="approval_or_briefing_decision",
        structure="Present a manager who must approve, reject, narrow, accelerate, or brief a cross-cultural action under pressure.",
        question_goal="Ask what decision or briefing line is most defensible; it may require accepting visible risk rather than avoiding action.",
        option_design=[
            "Bystander input should be balanced constraints, not evaluative hints such as warnings, flags, objections, or claims that something feels off.",
            "All options must be approval/briefing decisions, not a mix of creative edits, research, escalation, and delay.",
            "Each option protects one real priority and exposes another.",
            "Avoid abstract speaker-ranking language.",
            "Make the correct answer neither the broadest nor the safest-sounding.",
            "Make every wrong option plausible under another authority, law, relationship, or communication logic.",
            "Make common_misunderstanding one of those plausible authorities, laws, relationship logics, or governance routines.",
            "Phrase each option as the decision a manager would actually approve, not a critique of that decision.",
            "Do not name the local rule; make the decision turn on local execution consequences.",
            "Do not make the correct decision the only local-signoff, participant-choice, consultation, or middle-path option.",
        ],
        design_checks=[
            "Use legal/compliance process vs relationship trust vs cultural representation vs KPI deadline.",
            "Include a true-but-misapplied outside policy, practice, or theory as a distractor.",
        ],
    ),
]


FORMAT_GROUPS = {
    "knowledge": {
        "fact_or_mapping_discriminator",
        "concrete_revision_or_wording",
        "counterbalanced_override",
    },
    "calibration": {
        "diagnostic_evidence_selection",
        "best_next_step",
        "fact_or_mapping_discriminator",
    },
    "commitment": {
        "best_next_step",
        "approval_or_briefing_decision",
        "counterbalanced_override",
    },
    "non_action": {"diagnostic_evidence_selection", "fact_or_mapping_discriminator"},
    "action": {"response_ordering", "concrete_revision_or_wording", "best_next_step"},
}

ANSWER_POSTURES = [
    {
        "name": "active_push",
        "rule": (
            "The correct answer should actively move the work forward now. "
            "A generic wait-for-more-information option should be an attractive but wrong distractor."
        ),
        "cost": "Higher visibility, less time for consensus, or relationship discomfort.",
    },
    {
        "name": "bounded_directness",
        "rule": (
            "The correct answer should use a direct or explicit move because the seed-specific context supports it. "
            "Over-cautious indirectness should be plausible but wrong."
        ),
        "cost": "It may feel less diplomatic or less inclusive in the short term.",
    },
    {
        "name": "conditional_commitment",
        "rule": (
            "The correct answer should make a narrow conditional commitment, decision, or briefing instead of waiting. "
            "The condition must be concrete and culturally meaningful."
        ),
        "cost": "The actor owns a visible risk if the condition is misunderstood or later changes.",
    },
    {
        "name": "specific_discriminator",
        "rule": (
            "The correct answer should turn on one seed-specific discriminator that defeats a generic business heuristic. "
            "The generic heuristic must lead to a plausible wrong option."
        ),
        "cost": "The actor must ignore a broadly sensible rule because this local case is different.",
    },
    {
        "name": "counterintuitive_local_fact",
        "rule": (
            "The correct answer should override a broadly ethical, inclusive, consultative, or efficient default "
            "because the seed-specific local fact points in a narrower concrete direction. "
            "One distractor should be that universal default, written as a generous professional choice."
        ),
        "cost": "The actor may look less universally cautious or less procedurally tidy in the short term.",
    },
    {
        "name": "targeted_check",
        "rule": (
            "The correct answer may check something, but only one decisive point. "
            "Broad delay, broad consultation, or 'learn more first' should be too diffuse to be correct."
        ),
        "cost": "The actor risks acting with incomplete background beyond that decisive point.",
    },
]

ACTION_MAGNITUDE_PATTERNS = [
    {
        "name": "smaller_precise_correct",
        "rule": "The correct answer should be a narrow local adjustment. At least one distractor must propose broader review, larger redesign, or heavier approval.",
    },
    {
        "name": "same_size_different_direction",
        "rule": "All options should require similar effort; the difference is the local direction, not how much work is done.",
    },
    {
        "name": "wrong_overcorrection",
        "rule": "One distractor should look more cautious, more culturally elaborate, or more rework-heavy than the correct answer, but apply the wrong imported logic.",
    },
    {
        "name": "constraint_favored_trap",
        "rule": "At least one wrong option should handle the strongest time/cost/approval constraint better than the correct answer on the surface.",
    },
    {
        "name": "universal_best_practice_trap",
        "rule": "One distractor should embody a sound generic ethics, inclusion, autonomy, legal, or consultation principle that loses only because this target context has a more specific direction.",
    },
]

OPTION_DIMENSIONS = [
    {
        "name": "visual_or_material_direction",
        "rule": "All options compete on the same visual/material choice; do not mix visual changes with approval-routing or research choices.",
    },
    {
        "name": "wording_or_message_frame",
        "rule": "All options compete on the same wording/message frame; do not mix copy edits with channel, research, or governance moves.",
    },
    {
        "name": "approval_or_documentation_route",
        "rule": "All options compete on the same approval/documentation route; do not mix it with changing the product, visual, or message direction.",
    },
    {
        "name": "timing_or_sequence",
        "rule": "All options compete on timing/sequence; do not mix sequencing with unrelated visual or stakeholder-scope decisions.",
    },
    {
        "name": "stakeholder_scope",
        "rule": "All options compete on who is included, bound, briefed, or insulated; do not mix stakeholder scope with unrelated content changes.",
    },
    {
        "name": "evidence_or_observation",
        "rule": "All options compete on the same kind of evidence or observation; do not mix evidence selection with action, approval, or redesign choices.",
    },
    {
        "name": "fact_or_mapping",
        "rule": "All options compete on one cultural fact dimension: region, subgroup, body part, occasion, age/status, sequence, visual direction, or degree.",
    },
    {
        "name": "override_scope",
        "rule": "All options compete on the same localization versus standardization scope; do not mix scope with unrelated process moves.",
    },
]

FORMAT_OPTION_DIMENSIONS = {
    "concrete_revision_or_wording": "wording_or_message_frame",
    "diagnostic_evidence_selection": "evidence_or_observation",
    "fact_or_mapping_discriminator": "fact_or_mapping",
    "counterbalanced_override": "override_scope",
    "response_ordering": "timing_or_sequence",
    "approval_or_briefing_decision": "approval_or_documentation_route",
}

SURFACE_TERM_STOPWORDS = {
    "The",
    "This",
    "These",
    "Those",
    "In",
    "At",
    "For",
    "Among",
    "Sources",
    "Search",
    "A",
    "An",
    "Historic",
}

SOURCE_TERM_WORDS = {
    "ABC",
    "Böll",
    "Frontiers",
    "Heinrich",
    "International",
    "News",
    "NOW",
    "PubMed",
    "RCDF",
    "ReVista",
    "Smithsonian",
    "Stiftung",
}

BROKEN_TERM_WORDS = {
    "are",
    "as",
    "has",
    "have",
    "is",
    "may",
    "might",
    "not",
    "notes",
    "reported",
    "reports",
    "says",
    "states",
    "was",
    "were",
    "would",
}

ITEM_BLUEPRINT = {
    "must_include": [
        "double closure: scenario alone does not reveal the answer, and options alone do not reveal it by tone",
        "all four options compete on one decision dimension only",
        "three transplanted decoys that would be defensible in another mainstream culture, nearby market, legal system, professional practice, or adjacent subgroup",
        "scenario gives trigger context only, not the decisive culture fact",
        "constraints create a culture tradeoff but do not eliminate distractors through ordinary deadline or budget logic",
        "one distractor turns common_misunderstanding into a polished, benevolent, professional, or compliance-friendly near-miss",
        "at least two options share the same universal good-practice appeal but diverge in concrete local direction",
        "at least two distractors contain accurate seed-specific cultural knowledge and fail only by wrong actor, stage, scope, direction, degree, timing, or evidence weight",
        "the correct answer is not the only option with full stage coverage, local detail, or fine-grained cultural distinction",
        "the selected CQ changes the comparison among options; without it, the answer should not be obvious from cultural knowledge alone",
        "the correct answer paraphrases the seed-specific fact instead of repeating the seed's distinctive wording",
        "the correct answer is not the only option with choice, local sign-off, consultation, or balanced middle-path wording",
    ],
    "question_form": "concrete action, wording, sequence, channel, approval, briefing, or diagnostic observation",
    "scenario_form": "name the target country/region and practical facts only; express culture through behavior, timing, place, industry, or role cues",
    "option_form": "parallel candidate actions; each distractor is efficient and plausible under a different imported logic but fails in local execution",
    "dimension_convergence": "same action type, same decision layer, same deliverable; vary only the culturally decisive direction",
    "cultural_detail_parity": "all options should contain comparable cultural detail and mechanism coverage; vary target, stage, scope, direction, degree, timing, or evidence weight",
    "stage_coverage_parity": "if the correct option covers multiple stages, at least two distractors should cover comparable stages and differ in application fit",
    "constraint_penetration": "time, cost, approval, and stakeholder constraints must make at least one wrong option genuinely attractive",
    "transplant_decoys": [
        "nearby-market or regional practice that would normally be accepted",
        "dominant international or Western legal/commercial logic",
        "efficiency, KPI, governance, rights, or inclusion logic that is sound elsewhere",
    ],
    "directional_neutrality": [
        "No local expert, liaison, reviewer, producer, consultant, or manager should warn, flag, object, or say something feels wrong.",
        "Stakeholder comments must be factual constraints, not cultural diagnoses or recommendations.",
        "If one fact supports the correct option, include similarly credible facts supporting distractors.",
        "Avoid evaluative labels in options; all four options should read like reasonable proposals.",
    ],
    "forbidden": [
        "perfect correct option",
        "correct option as the only option that changes the artifact substantially",
        "correct option as the only option that contains accurate local facts or covers the full process",
        "wrong options scattered across unrelated dimensions",
        "distractor with no real trap origin",
        "named cultural or legal knowledge such as holidays, rituals, doctrines, or principles",
        "scenario that states the seed knowledge or common_misunderstanding",
        "directional third-party feedback such as 'warns', 'flags', 'off', 'will be ignored', or 'issue is bigger'",
        "abstract speaker ranking",
        "obvious rude/illegal filler distractor",
        "distractor that admits its own risk or uses obviously bad behavior",
        "correct answer as generic delay plus more information",
        "common_misunderstanding written as a foolish or obviously insensitive option",
        "correct answer as the only option that offers participant choice, local consultation, local signature, or a balanced middle path",
        "correct option repeating the seed's key phrase while distractors use generic language",
        "scenario stating the decisive body part, mapping, sequence, contrast, or local meaning that the options are supposed to test",
        "deadline, budget, or committee size making a distractor wrong without culture knowledge",
        "options that differ mainly by style: localize vs globalize vs escalate vs leave to individuals",
        "options that differ mainly by amount of cultural knowledge rather than application target, stage, scope, direction, degree, timing, or evidence weight",
        "pure cultural-knowledge item where deleting the selected CQ leaves the same answer obvious",
    ],
}

CQ_HINGES = {
    "cognitive": {
        "rule": (
            "Do not merely ask for recall of the local rule. The answer should depend on mapping the rule to the exact "
            "category, boundary, exception, or mechanism in this scenario."
        ),
        "distractor_requirement": (
            "At least two distractors must state accurate parts of the same cultural rule but apply them to the wrong "
            "actor, subgroup, stage, scope, direction, degree, or occasion."
        ),
    },
    "metacognitive": {
        "rule": (
            "The answer should depend on monitoring or revising an interpretation under ambiguous cultural cues, "
            "not on directly recognizing the rule."
        ),
        "distractor_requirement": (
            "At least two distractors must interpret the same cultural evidence plausibly but weight, update, or bound "
            "that evidence incorrectly."
        ),
    },
    "motivational": {
        "rule": (
            "The answer should depend on willingness to keep adapting under inconvenience, uncertainty, relationship cost, "
            "or discomfort, not just knowing what the norm is."
        ),
        "distractor_requirement": (
            "At least two distractors must know the local norm but differ in commitment, patience, effort, or tolerance "
            "in a way that misfits this scenario."
        ),
    },
    "behavioural": {
        "rule": (
            "The answer should depend on the concrete enactment of a known norm: wording, gesture, sequence, distance, "
            "channel, timing, intensity, or audience."
        ),
        "distractor_requirement": (
            "At least two distractors must know the norm but perform it at the wrong moment, intensity, direction, "
            "channel, or audience."
        ),
    },
}


def preferred_task_a_format_group(cq_tag: str) -> str:
    # Task A item rules only shape the multiple-choice item after the selected
    # CQ has already been chosen by the caller.
    return "mixed"


def _select_by_hash(items, key: str):
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def select_target_correct_option(seed_id: str, item_index: int) -> str:
    return _select_by_hash(("A", "B", "C", "D"), f"{seed_id}:{item_index}:task-a-correct")


def select_format_hint(seed_id: str, item_index: int, preferred_group: Optional[str] = None) -> AFormatHint:
    if preferred_group and preferred_group in FORMAT_GROUPS:
        catalog = [item for item in FORMAT_CATALOG if item.name in FORMAT_GROUPS[preferred_group]]
    else:
        catalog = FORMAT_CATALOG
    return _select_by_hash(catalog, f"{seed_id}:{item_index}")


def select_answer_posture(seed_id: str, item_index: int) -> Dict[str, str]:
    return _select_by_hash(ANSWER_POSTURES, f"{seed_id}:{item_index}:answer-posture")


def select_action_magnitude_pattern(seed_id: str, item_index: int) -> Dict[str, str]:
    return _select_by_hash(ACTION_MAGNITUDE_PATTERNS, f"{seed_id}:{item_index}:action-magnitude")


def select_option_dimension(seed: SeedRecord, item_index: int, format_name: str) -> Dict[str, str]:
    by_name = {item["name"]: item for item in OPTION_DIMENSIONS}
    if format_name in FORMAT_OPTION_DIMENSIONS:
        return by_name[FORMAT_OPTION_DIMENSIONS[format_name]]

    text_blob = " ".join(
        [seed.context, seed.knowledge, seed.common_misunderstanding, seed.typical_scenario]
    ).lower()
    if any(
        token in text_blob
        for token in ("beauty", "cosmetic", "costume", "dress", "visual", "campaign", "fashion", "styling", "image")
    ):
        candidates = ("visual_or_material_direction", "wording_or_message_frame")
    elif any(token in text_blob for token in ("contract", "legal", "arbitration", "sign", "approval", "procurement")):
        candidates = ("approval_or_documentation_route", "stakeholder_scope", "timing_or_sequence")
    else:
        candidates = ("timing_or_sequence", "stakeholder_scope", "wording_or_message_frame")
    return by_name[_select_by_hash(candidates, f"{seed.seed_id}:{item_index}:option-dimension")]


def _surface_terms_to_hide(seed: SeedRecord) -> list[str]:
    text = " ".join([seed.knowledge, seed.common_misunderstanding])
    country_words = {
        part.lower()
        for region in seed.countries_or_regions
        for part in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'’\-]+", region)
    }
    candidates: list[str] = []

    def add(term: str) -> None:
        cleaned = re.sub(r"\s+", " ", term.strip(" .,:;()[]{}\"'“”‘’"))
        if len(cleaned) < 3:
            return
        words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'’\-]+", cleaned)
        if not words:
            return
        if all(word.lower() in country_words for word in words):
            return
        if words[0] in SURFACE_TERM_STOPWORDS:
            return
        if any(word in SOURCE_TERM_WORDS for word in words):
            return
        if any(word.lower() in BROKEN_TERM_WORDS for word in words[1:]):
            return
        lowered = cleaned.lower()
        if lowered not in {item.lower() for item in candidates}:
            candidates.append(cleaned)

    for quoted in re.findall(r"['“”\"]([^'“”\"]{2,60})['“”\"]", text):
        add(quoted)
    for slash_term in re.findall(r"\b[A-Za-zÀ-ÖØ-öø-ÿ'’\-]+/[A-Za-zÀ-ÖØ-öø-ÿ'’\-]+\b", text):
        add(slash_term)
        for part in slash_term.split("/"):
            add(part)
    for phrase in re.findall(r"\b[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’\-]+(?:\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’\-]+){0,3}\b", text):
        if len(phrase.split()) > 1:
            add(phrase)
    label_patterns = (
        r"\bcalled\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-/]+)",
        r"\bknown as\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-/]+)",
        r"\bconcept of\s+([A-Za-zÀ-ÖØ-öø-ÿ'’\-/]+)",
    )
    for pattern in label_patterns:
        for term in re.findall(pattern, text, flags=re.IGNORECASE):
            add(term)
    for legal_label in re.findall(
        r"\b([a-z][a-z\-]+(?:\s+(?:of|and|or|the|[a-z][a-z\-]+)){0,5}\s+(?:principle|doctrine|theory|rule))\b",
        text,
    ):
        add(legal_label)
    return candidates[:12]


def build_task_a_item_rules(
    *,
    seed: SeedRecord,
    item_index: int,
    cq_tag: str,
    selected_expert_reason: str,
    selected_expert_score: int,
    target_correct_option: str = "",
) -> Dict[str, Any]:
    preferred_group = preferred_task_a_format_group(cq_tag)
    format_hint = select_format_hint(
        seed.seed_id,
        item_index,
        preferred_group=None if preferred_group == "mixed" else preferred_group,
    )
    answer_posture = select_answer_posture(seed.seed_id, item_index)
    action_magnitude_pattern = select_action_magnitude_pattern(seed.seed_id, item_index)
    option_dimension = select_option_dimension(seed, item_index, format_hint.name)
    target_correct_option = target_correct_option or select_target_correct_option(seed.seed_id, item_index)
    return {
        "task_a_item_rules": {
            "culture_anchor": {
                "knowledge": seed.knowledge,
                "common_misunderstanding": seed.common_misunderstanding,
                "surface_terms_to_hide": _surface_terms_to_hide(seed),
                "anchor_rule": (
                    "Use this as the hidden answer key. The item should show country and triggering facts, "
                    "then test execution judgment without naming or paraphrasing the rule."
                ),
            },
            "selected_expert_reason": selected_expert_reason,
            "selected_expert_score": selected_expert_score,
            "cq_expert_guidance": build_cq_expert_guidance(cq_tag),
            "cq_expert_skill": load_cq_expert_skill(cq_tag),
            "cq_hinge": CQ_HINGES.get(cq_tag, {}),
            "format_hint": format_hint.to_dict(),
            "answer_posture": answer_posture,
            "action_magnitude_pattern": action_magnitude_pattern,
            "option_dimension": option_dimension,
            "target_correct_option": target_correct_option,
            "item_blueprint": ITEM_BLUEPRINT,
            "generation_guardrails": {
                "design_quality": "Follow answer_posture and item_blueprint exactly.",
                "action_magnitude": "Follow action_magnitude_pattern; at least one wrong option must do more or look more careful than the correct option.",
                "dimension_convergence": "Follow option_dimension; all options must compete on one decision layer only.",
                "trap_origin_binding": "Silently bind every wrong option to a real external market, legal, SOP, or professional logic; do not output the labels.",
                "constraint_penetration": "Every scenario constraint must affect at least two options, and at least one wrong option should benefit from the strongest constraint.",
                "cultural_detail_parity": "The correct option must not be the only one with accurate culture detail, full-process coverage, local facts, or fine-grained stage distinctions.",
                "culturally_informed_distractors": "At least two distractors must use accurate seed-specific knowledge and fail only by wrong actor, stage, scope, direction, degree, timing, or evidence weight.",
                "cq_hinge": "Follow cq_hinge: the selected CQ must be necessary to choose among culturally informed options, not merely a metadata tag.",
                "implicit_signals": "Replace named culture/legal terms with behavior, timing, geography, industry, role, or workflow cues.",
                "execution_bias": "Ask about local execution drift caused by imported assumptions, not recall of legal text or cultural labels.",
                "directional_neutrality": "Use neutral facts and competing constraints only; no stakeholder should tell the reader which direction is culturally right.",
                "option_camouflage": "Do not append 'but/risk/however/although' flaw explanations to options; keep all options self-advocating.",
                "option_payoff": "Wrong options should look cheaper, faster, KPI-friendly, or administratively cleaner than the correct option.",
                "option_balance": "22-32 words each; parallel grammar; all distractors plausible in other contexts; no filler distractors.",
                "double_closure": "The scenario should not reveal the answer; the options should not reveal it by tone. Only seed-specific culture knowledge plus scenario trigger should decide.",
                "universal_heuristic_split": "At least two options must satisfy the same generic professional virtue; the correct answer wins only because of the seed-specific local fact.",
                "common_misunderstanding_trap": "Make one distractor embody common_misunderstanding as a polished, benevolent, modern, or compliance-friendly proposal.",
                "lexical_anti_cueing": "Correct option should paraphrase the target rule; do not let it be the option with the strongest wording overlap with the seed or scenario.",
                "anti_template_answer": "The correct option must not be the only one with choice, local sign-off, consultation, broad review, or middle-path wording.",
                "anti_full_process_answer": "The correct option must not be the only option that handles all stages; if it covers multiple stages, two distractors must cover comparable stages differently.",
                "same_lane_options": "All options should be professional and similarly local-aware; vary one concrete fact dimension, not respectfulness.",
                "constraint_use": "Use deadlines and budgets only if they pressure all plausible options; do not let them eliminate distractors by common sense.",
                "counterbalance": "Some items should let standardization, refusal, or a narrow override be correct when cultural adaptation would be harmful or false.",
            },
            "allowed_question_styles": [
                "best_next_step_under_competing_constraints",
                "best_concrete_revision_or_wording",
                "plausible_explanation_for_mismatch",
                "diagnostic_evidence_selection",
                "response_or_priority_ordering",
                "approval_or_briefing_decision",
            ],
        },
    }
