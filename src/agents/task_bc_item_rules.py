from typing import Any, Dict

from src.agents.cq_expert_guides import build_cq_expert_guidance
from src.agents.participant_skills import load_cq_expert_skill
from src.models.seed_schema import SeedRecord


TASK_B_ITEM_BLUEPRINT = {
    "must_include": [
        "label-first construction: use preferred_b_label as the target answer label before drafting; do not infer the label after writing the dialogue",
        "seed-truth anchoring: treat seed.knowledge as the culturally correct behavior; appropriate means the decisive newcomer behavior aligns with it, inappropriate means the decisive behavior deviates from it or enacts seed.common_misunderstanding",
        "culture necessity: the appropriate/inappropriate label must depend on seed.knowledge and seed.common_misunderstanding, not generic politeness or professionalism",
        "double closure: the scenario/dialogue must not explain the cultural rule, and the label must not be guessable from the newcomer's tone alone",
        "newcomer competence: the newcomer should make several reasonable moves; the decisive issue is a subtle execution mismatch or repair",
        "local cue discipline: local speakers give neutral task cues, hesitation, sequence pressure, or channel shifts, not cultural warnings or explanations",
        "appropriate-label misdirection: when the label is appropriate, the newcomer follows the seed-specific cultural mechanism but includes a surface feature that generic raters may dislike, such as directness, speed, publicity, brevity, or constraint preservation",
        "inappropriate-label camouflage: when the label is inappropriate, the newcomer violates or misapplies the seed-specific cultural mechanism while sounding polite, competent, good-faith, and partly adaptive",
        "common misunderstanding trap: for inappropriate labels, the decisive move should usually enact seed.common_misunderstanding in a polished, professional form; for appropriate labels, the dialogue may make that trap tempting without following it",
        "imported logic: an inappropriate move should be defensible in another market, adjacent subgroup, global SOP, or KPI-driven workflow, even though it is wrong for this seed",
        "CQ binding: the decisive turn must test the selected CQ expert skill through interpretation, updating, effort, or visible behavior",
        "culture discriminant: include a small target-culture-specific execution detail that separates the label from a plausible adjacent-culture or global-SOP reading",
        "minimal-opposite test: the opposite label should require changing a seed-specific timing, channel, audience, scope, sequence, or evidence-use choice, not merely changing tone",
        "template suppression: avoid recurring answer-key phrases that make appropriate items sound like patience/checking and inappropriate items sound like efficiency/refusal",
        "subtopic-label neutrality: do not let the seed subtopic imply the label; any subtopic should support either label when the execution detail changes",
        "surface-label reversal: appropriate items need at least one generic surface cue that looks questionable; inappropriate items need at least one generic surface cue that looks reasonable",
        "no final reveal: the final turn must not settle the hidden cultural fact, list the exact rule, or convert the item into a solved worked example",
        "keyword camouflage: do not foreground the most diagnostic taboo/ritual/title/gesture/food keyword without an ordinary operational decoy from the same setting",
        "opposite-surface cue: include a surface cue that would tempt a generic rater toward the wrong label while the seed-specific mechanism still decides",
    ],
    "label_test": (
        "If a rater can decide the label after removing the seed-specific cultural fact and keeping only generic empathy, "
        "teamwork, caution, or efficiency, the item is invalid."
    ),
    "dialogue_form": (
        "Use observable timing, channel, audience, sequence, wording, silence, delayed review, or follow-up cues. "
        "Do not put the answer key in a local speaker's mouth."
    ),
    "one_shot_recipe": [
        "lock preferred_b_label first and define the culturally aligned behavior versus the culturally misaligned behavior",
        "define the hidden seed-specific mechanism and one exact execution axis before drafting",
        "construct a near-opposite twin whose label changes by one culture-specific execution detail, not by tone",
        "include two competing frames: target-culture logic and plausible imported SOP/adjacent-culture logic",
        "for appropriate labels, add misleading surface evidence while keeping the decisive action culturally aligned",
        "for inappropriate labels, add polite or professional camouflage while keeping the decisive action culturally misaligned",
        "place the decisive detail before the last turn; make the last newcomer turn short, operational, and non-revealing",
        "camouflage diagnostic taboo/ritual/title/gesture/food terms with ordinary same-setting logistics and one decoy detail",
    ],
    "forbidden": [
        "local speaker states, paraphrases, warns about, or teaches the seed.knowledge",
        "label turns on obvious rudeness, perfect politeness, enthusiasm, or friendliness",
        "knowledge appears only in the scenario background while the dialogue tests generic project management",
        "newcomer line uses giveaway phrasing such as 'I will do it my way' or 'this works everywhere'",
        "brief_reason gives only generic etiquette, respect, inclusion, patience, or caution",
        "appropriate label is signaled mainly by stock phrases such as 'follow your lead', 'I'll hold', 'I'll wait', or 'check privately'",
        "inappropriate label is signaled mainly by stock phrases such as 'No need', 'I'll just', 'skip', 'reply-all', 'copy everyone', or 'keep the line moving'",
        "efficiency, directness, transparency, privacy, patience, or caution is treated as automatically right or wrong instead of culture-dependent",
        "local cues repeatedly point in one direction and the newcomer simply complies or simply ignores them",
        "final dialogue turn reveals the exact dietary list, ritual order, title order, gesture meaning, greeting rule, or other hidden answer key",
        "scenario foregrounds the diagnostic cultural keyword without a competing same-setting operational detail",
    ],
}


TASK_C_ITEM_BLUEPRINT = {
    "must_include": [
        "multicultural team frame: ask for a project-collaboration plan whose quality would be judged as work performance by teammates, a supervisor, client, or local stakeholders",
        "answer-first: define the high-scoring answer frame, one polished near-miss frame, and their exact execution-axis difference before drafting",
        "culture necessity: high credit must require seed.knowledge and must reject or bound seed.common_misunderstanding",
        "double closure: scenario gives practical facts and pressure, but not the decisive cultural rule",
        "execution-axis convergence: question, rubric, and reference outline should center on one primary axis such as timing, scope, evidence, wording, approval, placement, role, repair, or risk boundary",
        "auxiliary culture contrast: when useful, add two or three teammate countries/regions with modest task-local work-habit contrasts on the same execution axis; they add coordination pressure but do not replace the seed as answer key",
        "near-miss scoring: rubric should distinguish seed-specific execution from polite, efficient, inclusive, careful, or locally consultative wrong-scope answers",
        "CQ binding: at least one rubric point and one reference move must test the selected CQ expert skill",
        "constraint pressure: deadlines, hierarchy, budget, trust, legal, or stakeholder pressure should make the near-miss attractive without replacing cultural reasoning",
    ],
    "answer_test": (
        "If a generic cross-cultural project plan could score high without using the seed-specific cultural fact, "
        "the Task C item is invalid."
    ),
    "answer_first_recipe": [
        "define the high-scoring seed-specific plan before writing the case",
        "define one polished imported/common-misunderstanding plan that a competent respondent might propose",
        "choose one exact execution axis where the high-scoring and near-miss frames diverge",
        "make the scenario constraints increase the appeal of the near-miss frame",
        "write rubric points that reward the high-scoring frame and explicitly bound the near-miss frame",
    ],
    "execution_axes": [
        "timing_or_sequence",
        "stakeholder_scope",
        "evidence_weighting",
        "wording_or_message_frame",
        "approval_or_documentation_route",
        "visual_or_material_placement",
        "role_assignment",
        "repair_channel",
        "risk_control_boundary",
    ],
    "near_miss_answer_families": [
        "seed.common_misunderstanding rewritten as a courteous, careful, or brand-safe plan",
        "accurate seed-specific knowledge applied to the wrong actor, stage, scope, direction, timing, degree, or evidence type",
        "a sound generic ethics, inclusion, autonomy, legal, compliance, or consultation principle that loses because the target context has a narrower execution requirement",
        "a nearby-market, adjacent-subgroup, KPI, or global-SOP plan that handles pressure well but misreads the seed-specific mechanism",
    ],
    "rubric_form": (
        "Each score_rule should distinguish seed-specific execution from vague respect, broad checking, generic inclusion, "
        "or naming a doctrine/ritual without operational consequences."
    ),
    "reference_form": (
        "Every reference_outline point should be operational: diagnosis, execution-axis decision, coordination, "
        "near-miss handling, selected-CQ application, calibration or repair, and work-performance signals."
    ),
    "forbidden": [
        "extra countries or stakeholders that are present only to make the case look complex",
        "added countries used as absolute stereotypes rather than modest task-local collaboration contrasts",
        "scenario that is not clearly about completing work in a multicultural project team",
        "rubric points such as 'communicate respectfully' or 'be inclusive' without seed-specific scoring criteria",
        "reference_outline that could be reused for many unrelated cultures by changing country names",
        "scenario includes a local adviser who tells the reader the culturally correct direction",
        "full credit for asking locals generally, delaying everything, or using generic risk controls without applying the knowledge",
        "high score for the longest, safest, broadest, most consultative, or most elaborate plan unless the seed-specific mechanism requires that exact move",
        "near-miss frame that is obviously rude, careless, illegal, foolish, or self-discrediting",
        "rubric rewards repeating the seed wording more than translating it into execution consequences",
        "question asks for general attitudes instead of a concrete mechanism, coordination design, decision memo, repair plan, evidence-use plan, rollout plan, briefing approach, or stakeholder sequence",
    ],
}


def _culture_anchor(seed: SeedRecord) -> Dict[str, Any]:
    return {
        "knowledge": seed.knowledge,
        "common_misunderstanding": seed.common_misunderstanding,
        "anchor_rule": (
            "Use this as the hidden answer key. The item should show target country/region and triggering facts, "
            "but the scenario/dialogue must not state the decisive rule. The label, rubric, or reference outline "
            "must become weak or unscorable if this culture anchor is removed."
        ),
    }


def _selected_cq_payload(
    *,
    cq_tag: str,
    selected_expert_reason: str,
    selected_expert_score: int,
) -> Dict[str, Any]:
    return {
        "selected_expert_reason": selected_expert_reason,
        "selected_expert_score": selected_expert_score,
        "cq_expert_guidance": build_cq_expert_guidance(cq_tag),
        "cq_expert_skill": load_cq_expert_skill(cq_tag),
        "skill_rule": (
            "Use cq_expert_skill as an item-design standard, not metadata. The generated item must visibly test "
            "the selected CQ dimension in its decisive turn, rubric point, or reference-outline move."
        ),
    }


def build_task_b_item_rules(
    *,
    seed: SeedRecord,
    cq_tag: str,
    selected_expert_reason: str,
    selected_expert_score: int,
) -> Dict[str, Any]:
    return {
        "task_b_item_rules": {
            "culture_anchor": _culture_anchor(seed),
            **_selected_cq_payload(
                cq_tag=cq_tag,
                selected_expert_reason=selected_expert_reason,
                selected_expert_score=selected_expert_score,
            ),
            "item_blueprint": TASK_B_ITEM_BLUEPRINT,
            "generation_guardrails": {
                "label_first": "Use preferred_b_label as the target label before drafting. Appropriate means culture-aligned with seed.knowledge; inappropriate means culture-misaligned or enacting seed.common_misunderstanding.",
                "culture_necessity": TASK_B_ITEM_BLUEPRINT["label_test"],
                "directional_neutrality": "Use neutral cues and competing constraints; no local speaker should explain which behavior is culturally right.",
                "newcomer_camouflage": "The newcomer should sound good-faith, competent, and task-oriented even when the label is inappropriate.",
                "appropriate_misdirection": "For appropriate labels, add a surface cue that generic raters may dislike while keeping the decisive behavior culturally calibrated to the seed.",
                "inappropriate_camouflage": "For inappropriate labels, make the decisive behavior culturally wrong for the seed while preserving polite, competent, or locally plausible surface behavior.",
                "common_misunderstanding_trap": "Make seed.common_misunderstanding a tempting imported assumption. Use it as the decisive error for inappropriate labels when the seed supports that move.",
                "cq_skill_application": "Follow cq_expert_skill for the selected CQ; do not drift into a different CQ because it is easier to write.",
                "reason_specificity": "brief_reason must name the seed-specific mechanism and the exact execution axis, not generic respect or caution.",
                "culture_discriminant": "Include one target-culture-specific detail that would not be resolved by generic politeness, checking, or efficiency.",
                "minimal_opposite_test": "The imagined opposite-label twin should differ by one seed-specific execution detail, not by nicer tone or more caution.",
                "anti_template_signals": "Do not rely on stock answer cues such as follow-your-lead/check-privately for appropriate or no-need/skip/reply-all for inappropriate.",
                "subtopic_label_neutrality": "Use preferred_b_label to fight predictable label patterns within subtopics; the subtopic itself must not reveal the answer.",
                "surface_label_reversal": "Appropriate items need a generic surface cue that tempts raters toward inappropriate; inappropriate items need a generic surface cue that tempts raters toward appropriate.",
                "no_final_reveal": "The final turn cannot provide the exact missing cultural fact or a clean moral summary of the right/wrong move.",
                "keyword_camouflage": "Hide diagnostic cultural terms inside ordinary logistics and add one plausible decoy detail from the same setting.",
                "opposite_surface_cue": "Include a generic-politeness or generic-efficiency cue that points toward the wrong label unless the knowledge is applied.",
            },
        }
    }


def build_task_c_item_rules(
    *,
    seed: SeedRecord,
    cq_tag: str,
    selected_expert_reason: str,
    selected_expert_score: int,
) -> Dict[str, Any]:
    return {
        "task_c_item_rules": {
            "culture_anchor": _culture_anchor(seed),
            **_selected_cq_payload(
                cq_tag=cq_tag,
                selected_expert_reason=selected_expert_reason,
                selected_expert_score=selected_expert_score,
            ),
            "item_blueprint": TASK_C_ITEM_BLUEPRINT,
            "generation_guardrails": {
                "task_frame": "Frame Task C as a multicultural team project where the respondent's collaboration plan is evaluated as work performance.",
                "answer_first": "Before drafting, define the high-scoring seed-specific answer frame, a polished near-miss frame, and the one execution axis where they diverge.",
                "culture_necessity": TASK_C_ITEM_BLUEPRINT["answer_test"],
                "auxiliary_cultures": "If useful, add two or three teammate countries/regions with modest work-habit contrasts on the same execution axis; keep the seed country as the main hidden answer key.",
                "execution_axis": "Keep scenario, question, rubric, and reference outline centered on one primary execution axis.",
                "rubric_anchoring": "Most rubric points must use seed-specific execution criteria, not generic collaboration criteria.",
                "reference_anchoring": "Every reference-outline point should apply the knowledge to an operational consequence and work-performance signal.",
                "near_miss_scoring": "Rubric should penalize plausible polite, careful, efficient, inclusive, or locally consultative near-misses.",
                "common_misunderstanding_trap": "Include one attractive imported assumption that enacts seed.common_misunderstanding.",
                "cq_skill_application": "Follow cq_expert_skill; at least one rubric point should score that CQ dimension.",
                "generic_answer_penalty": "Generic politeness, generic inclusion, broad consultation, or delay-for-more-info cannot receive high credit.",
                "surface_reversal": "High credit need not be the largest, safest, or most consultative plan when the seed supports a narrower move.",
                "wrong_application_penalty": "Deny full credit for accurate cultural knowledge applied to the wrong actor, stage, scope, direction, timing, degree, or evidence type.",
                "directional_neutrality": "No local stakeholder should explain the correct cultural direction.",
            },
        }
    }
