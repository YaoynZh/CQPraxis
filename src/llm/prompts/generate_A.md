Generate one Task A multiple-choice item for a cross-cultural benchmark. Return JSON only.

## 1. Goal

Task A should test whether the solver can apply one seed-specific cultural mechanism to a concrete situation through the selected CQ lens. The item should not reward the generic heuristic "choose the most careful, respectful, local, detailed, consultative, or risk-reducing option."

The selected CQ dimension has already been chosen. Use it to shape what must be reasoned about, but do not name the CQ dimension in the scenario or options.

Quality target: at least two distractors should remain defensible unless the solver notices the exact seed-specific discriminator.

Assign difficulty only after drafting, based on the reasoning the finished item actually requires. Do not target a preset difficulty or distribution.

## 2. Binding Inputs

Use the supplied seed, moderator_analysis, decision, selected_expert_score, item_id, and generation_hints.

Treat moderator_analysis.reason and moderator_analysis.task_fit as the moderator's original task-design rationale. Use that rationale together with the selected CQ expert's reason and skill when constructing the item, while keeping the already selected task and CQ labels fixed.

Treat these task_a_item_rules fields as binding:

- target_correct_option: put the correct answer at this letter.
- culture_anchor.knowledge: hidden answer key; do not repeat its distinctive wording.
- culture_anchor.common_misunderstanding: turn this into one polished near-miss distractor.
- culture_anchor.surface_terms_to_hide: do not use these terms in the scenario or correct option unless all options use comparable bait terms.
- format_hint: follow the named item format.
- option_dimension: all four options must compete on this one decision layer only.
- answer_posture: shape the correct answer's posture.
- action_magnitude_pattern: shape the relative size and attractiveness of correct/wrong actions.
- cq_hinge, if present: make the selected CQ dimension necessary to choose among culturally informed options.

If an item-rule field is provided only as a name, interpret it as follows.

### format_hint

- fact_or_mapping_discriminator: options are four claims or directions on one factual dimension; scenario gives only the trigger.
- counterbalanced_override: the correct answer may standardize, refuse, or narrow adaptation when extra localization would be false or risky.
- best_next_step: options are next steps at the same decision point; all protect a legitimate priority.
- concrete_revision_or_wording: options are alternative wordings or message frames only.
- diagnostic_evidence_selection: options are observations of the same kind; all are relevant, only one is most diagnostic.
- response_ordering: options reuse similar actions but differ by order, audience, channel, or timing.
- approval_or_briefing_decision: options are manager decisions or briefing lines, not mixed research/escalation/redesign moves.

### answer_posture

- active_push: correct answer moves work forward now; waiting broadly is tempting but wrong.
- bounded_directness: correct answer is explicit or direct for this seed; over-caution is tempting but wrong.
- conditional_commitment: correct answer makes a narrow concrete commitment or condition.
- specific_discriminator: correct answer turns on one local discriminator that defeats a generic heuristic.
- counterintuitive_local_fact: correct answer overrides a broad ethical, inclusive, consultative, or efficient default.
- targeted_check: correct answer checks one decisive point, not a broad "learn more first" agenda.

### action_magnitude_pattern

- smaller_precise_correct: correct answer is narrower than at least one more elaborate distractor.
- same_size_different_direction: all options require similar effort; only the local direction differs.
- wrong_overcorrection: one distractor looks more cautious or culturally elaborate than the correct answer.
- constraint_favored_trap: one distractor handles time/cost/approval pressure better on the surface.
- universal_best_practice_trap: one distractor embodies sound generic ethics, inclusion, autonomy, legal, or consultation logic.

### option_dimension

Use only the named layer: visual/material direction, wording/message frame, approval/documentation route, timing/sequence, stakeholder scope, evidence/observation, fact/mapping, or override scope. Do not mix layers.

## 3. Hidden Discriminator Protocol

Before writing the item, silently choose one narrow discriminator from the seed: actor, relationship, status, subgroup, setting, occasion, interaction stage, direction of behavior, timing, sequence, scope, degree, body area, object, food handling stage, address form, or evidence type.

The item is valid only if:

1. the scenario alone does not state the discriminator's cultural meaning;
2. the options alone do not reveal the answer by tone, caution, locality, detail, or professionalism;
3. at least two distractors contain the same seed-specific cultural knowledge as the correct option;
4. those culturally informed distractors fail only by applying that knowledge to the wrong actor, stage, scope, direction, degree, timing, or evidence weight;
5. at least two options share the same generic virtue as the correct option but differ in the concrete local direction;
6. the correct option is not the only option that solves the operational constraint in the scenario;
7. the wrong options would be defensible in a nearby market, adjacent subgroup, global SOP, legal/compliance habit, or mainstream professional frame.

Do not create a two-voice scenario where one person states the common misunderstanding and another person states the seed knowledge. Stakeholders may give factual constraints, but nobody should warn, flag, object, diagnose, or say that something feels culturally wrong.

## 4. CQ Hinge

The selected CQ must change the comparison among options. If removing the CQ tag and CQ guidance would leave the same answer obvious from cultural knowledge alone, rewrite the item.

- cognitive: do not merely ask for the known cultural rule. Make the answer depend on mapping the rule to the exact local category, boundary, exception, or mechanism while at least two distractors also state accurate parts of that rule.
- metacognitive: make the answer depend on monitoring or revising an interpretation under ambiguous cues. At least two options should interpret the same cultural evidence plausibly but weight it differently.
- motivational: make the answer depend on sustained willingness to adapt under inconvenience, uncertainty, relationship cost, or discomfort. At least two options should know the local norm but differ in commitment, patience, or effort.
- behavioural: make the answer depend on the concrete enactment of a known norm: wording, gesture, sequence, distance, channel, or timing. At least two options should know the norm but perform it at the wrong moment, intensity, direction, or audience.

## 5. Scenario Design

Use neutral observable facts: schedule, role, relationship, setting, prior behavior, object placement, message history, audience, workflow, or service arrangement.

Do not state:

- the decisive cultural rule;
- why the behavior is correct or incorrect;
- the full risk or violation;
- the exact body part, food stage, title form, ritual object, region mapping, or sequence if that is what the options are supposed to test;
- all steps that the correct option must contain.

Use deadlines, budgets, hierarchy, approvals, or logistics only if they make at least one distractor more attractive. They must not eliminate distractors by ordinary project logic.

Avoid direct wording overlap between scenario and correct option. A conspicuous scenario detail must not map uniquely to one option.

Use a neutral question stem. Avoid "most respectful", "safest", "most inclusive", "balanced", "calibrated", "most appropriate", and "most robust".

## 6. Option Design

Develop the four options together. Do not write an ideal answer first and then weaken the other three.

Required distractor set:

- one polished version of seed.common_misunderstanding;
- two culturally informed near-misses that use accurate seed knowledge but apply it to the wrong actor, stage, scope, direction, degree, timing, or evidence weight;
- one same-virtue near-miss that consults, localizes, verifies, preserves choice, standardizes, or reduces risk in the wrong scope, timing, or concrete direction;
- one imported-logic distractor that is reasonable in another culture, adjacent subgroup, legal/compliance system, or global SOP.

All four options must:

- answer the same question at the same decision layer;
- sound coherent, ethical, courteous, and professionally defensible;
- use similar length, grammar, confidence, and information density;
- contain comparable local or operational specificity;
- contain comparable cultural detail, stage coverage, and mechanism coverage;
- be candidate actions, observations, claims, sequences, or wording, not explanations of why they are good or flawed.

Do not make distractors visibly wrong by using "ignore", "bypass", "always", "never", "everyone", "only", "just", "simply", "merely", "as long as", "provided that", "that should be enough", "regardless of context", or self-discrediting "but/however/although this risks..." clauses.

Avoid rationale clauses such as "because", "since", and "so" unless all four options use the same syntax and none explains its own flaw.

Keep each option normally 22-32 English words. The longest-shortest gap should normally be 6 words or less. The correct option must not be the longest, most detailed, most nuanced, most locally named, most culturally complete, most stage-aware, most cautious, or the only two-part option.

If the correct option mentions a decisive object, stage, body area, address form, verification step, local behavior, subgroup, or sequence, at least two distractors must mention the same category with a wrong direction, stage, scope, or degree. Do not place the decisive category only in the correct option.

Do not make the correct option the only full-process answer. If the correct option covers preparation, service, follow-up, greeting sequence, verification chain, or evidence interpretation across stages, at least two distractors must cover comparable stages and differ only in where the mechanism is applied.

## 7. Final Self-Check

Silently reject and rewrite the draft if any of these are true:

- a solver can pick the answer by choosing the most cautious, local, respectful, detailed, consultative, flexible, complete, or culturally specific option;
- the scenario contains a local person pointing toward the intended answer;
- the correct option is the only one that handles the named constraint;
- the correct option is the only one with accurate local facts, full stage coverage, or fine-grained cultural distinction;
- fewer than two distractors contain accurate seed-specific cultural knowledge;
- wrong options are mostly generic global uniformity, individual freedom, large committee review, or obvious Western defaults;
- options differ mainly by management style rather than a seed-specific culture fact or execution mechanism;
- options differ mainly by how much cultural knowledge they contain rather than by application target, stage, direction, degree, or evidence weight;
- deleting cq_tags and CQ guidance would leave the same answer obvious from cultural knowledge alone;
- the correct option repeats distinctive seed wording while distractors stay generic;
- option lengths or clause counts make the answer stand out.

## 8. Output Schema

{
  "seed_id": "string",
  "item_id": "A_001",
  "task_type": "A",
  "countries_or_regions": ["string"],
  "scenario": "string",
  "question": "string",
  "options": {
    "A": "string",
    "B": "string",
    "C": "string",
    "D": "string"
  },
  "correct_option": "A|B|C|D",
  "cq_tags": ["selected_cq"],
  "difficulty": "easy|medium|hard"
}
