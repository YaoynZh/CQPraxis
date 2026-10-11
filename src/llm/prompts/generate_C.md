Generate one Task C open-ended item for a cross-cultural benchmark. Return JSON only.

Task C is open-ended. Quality should come from a seed-specific cultural mechanism and a discriminating rubric, not from asking for a long generic plan.

Assign difficulty only after drafting, based on the reasoning the finished item actually requires. Do not target a preset difficulty or distribution.

## 1. Binding Inputs

Use the supplied seed, moderator_analysis, decision, selected_expert_score, item_id, and generation_hints.

Use moderator_analysis.reason and moderator_analysis.task_fit as the moderator's original task-design rationale. Combine it with the selected CQ expert's reason and skill when constructing the scenario, question, rubric, and reference outline; do not change the selected task or CQ labels.

Treat these fields as binding:

- selected_cq_expert_context
- task_c_item_rules.culture_anchor.knowledge as the hidden answer key
- task_c_item_rules.culture_anchor.common_misunderstanding as a polished near-miss trap
- task_c_item_rules.item_blueprint and generation_guardrails
- task_c_item_rules.cq_expert_skill and cq_expert_guidance

Use one main CQ tag only: the CQ already selected by the moderator.

## 2. Design Protocol

Before drafting, silently lock four things:

1. the high-scoring answer frame: what the respondent must diagnose, decide, sequence, communicate, and control using seed.knowledge;
2. the near-miss frame: what a competent generic respondent would do by following seed.common_misunderstanding, global SOP, KPI pressure, legal/process habits, or a nearby-market assumption;
3. one primary execution axis where the two frames diverge: timing, sequence, stakeholder scope, evidence weighting, wording, approval route, placement, role assignment, repair channel, or risk boundary;
4. the selected CQ hinge that makes high credit more than cultural fact recall.

The scenario, question, rubric, and reference_outline must all depend on this locked frame.

## 3. Scenario Rules

- Name the country/region and practical task facts, but do not state, paraphrase, or name the decisive cultural rule.
- Use neutral facts: schedule, roles, hierarchy, audience, workflow, message history, artifacts, approvals, or service setup.
- When the scenario supports them, include competing pressures such as deadline, client/sponsor pressure, budget, hierarchy, trust risk, public/private tension, legal/brand pressure, or ambiguous evidence.
- Make the near-miss plan attractive under those pressures.
- Do not include a local adviser who warns, flags, objects, diagnoses, or explains the correct cultural direction.
- Do not reveal the exact cue that the answer is supposed to infer, such as a decisive body part, food stage, title form, ritual object, region mapping, or sequence.

## 4. Question Rules

Ask for a concrete mechanism, plan, coordination design, decision memo, repair plan, evidence-use plan, rollout plan, briefing approach, or stakeholder sequence.

The question should force the respondent to:

- diagnose the hidden cultural mechanism from neutral evidence;
- identify the tempting imported assumption or common misunderstanding;
- make concrete execution choices on the primary axis;
- justify calibration, communication, or risk control through the selected CQ skill.

Avoid vague attitude questions that can be answered with generic respect, inclusion, caution, consultation, or delay.

## 5. Rubric Rules

Rubric must contain at least 3 substantive points.

Most rubric points must reward seed-specific execution. Include scoring for:

- diagnosing the seed-specific mechanism without merely naming a label;
- applying it to the exact actor, stage, scope, direction, timing, degree, or evidence weight;
- rejecting or bounding seed.common_misunderstanding as a tempting but miscalibrated plan;
- applying the selected CQ skill;
- designing concrete roles, workflow, channel, sequence, wording, placement, approval, repair, or risk control.

Penalize answers that:

- rely on generic politeness, broad checking, inclusion, caution, or delay;
- cite a cultural label, ritual, holiday, doctrine, or law without execution consequences;
- use accurate cultural knowledge at the wrong actor, stage, scope, direction, timing, degree, or evidence type;
- follow imported SOP, legal/process, KPI, brand, or adjacent-market logic that enacts the common misunderstanding;
- make the answer simply the safest, longest, broadest, or most consultative plan.

## 6. Reference Outline Rules

reference_outline must contain at least 3 substantive points.

Every point must be operational, not a generic principle. Cover:

- diagnosis and relevant scenario evidence;
- the primary execution-axis decision;
- role-specific communication or coordination;
- how to handle the near-miss/common misunderstanding;
- selected-CQ application;
- calibration, monitoring, or repair under constraints.

## 7. CQ Hinge

- cognitive: score exact mapping to local category, boundary, exception, or causal logic.
- metacognitive: score monitoring assumptions, weighing ambiguous evidence, and revising interpretations.
- motivational: score sustained adaptive effort under inconvenience, uncertainty, relationship cost, or discomfort.
- behavioural: score visible enactment through wording, sequence, channel, timing, audience, distance, intensity, or role.


## 8. Output Schema

{
  "seed_id": "string",
  "item_id": "C_001",
  "task_type": "C",
  "countries_or_regions": ["string"],
  "scenario": "string",
  "question": "string",
  "rubric": [
    {
      "point": "string",
      "score_rule": "string"
    }
  ],
  "reference_outline": ["string"],
  "cq_tags": ["metacognitive"],
  "difficulty": "easy|medium|hard"
}
