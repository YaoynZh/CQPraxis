Generate one Task B dialogue item for a cross-cultural benchmark. Return JSON only.

Your job is to write a dialogue where the assigned label depends on whether the newcomer's concrete behavior matches the seed-specific cultural mechanism.

## Label-First Rule
- Treat preferred_b_label as the target answer label when it is present. Do not choose the label after drafting the dialogue.
- First derive the culturally calibrated behavior from seed.knowledge. Treat the seed as true; never invert, weaken, or rewrite the cultural mechanism.
- If the target label is appropriate, the newcomer's decisive behavior must align with the seed-specific cultural mechanism. Add misleading surface evidence that could make a generic rater think the behavior is questionable, such as being direct, fast, public, brief, constraint-preserving, or not maximally warm and so on, as long as that surface evidence is not culturally wrong for this seed.
- If the target label is inappropriate, the newcomer's decisive behavior must deviate from the seed-specific cultural mechanism or enact the seed.common_misunderstanding. The newcomer should still sound polite, competent, good-faith, and partly adaptive, so a generic rater could be tempted to call it appropriate.
- The label is decided by culture fit, not by tone. Both labels may contain courtesy, effort, efficiency, caution, directness, or consultation; those surface qualities are only misdirection unless they change the seed-specific execution detail.

## Fixed Requirements
- Two roles: local and newcomer.
- dialogue_round must be 2, 3, or 4; dialogue length must equal dialogue_round * 2.
- label must be appropriate or inappropriate.
- Assign difficulty after drafting from the reasoning required by the finished item; do not target a preset difficulty or distribution.
- One main CQ tag only. Use the CQ already selected by the moderator; do not rebalance or reinterpret CQ here.
- Use moderator_analysis.reason and moderator_analysis.task_fit as the moderator's original task-design rationale, together with the selected CQ expert's reason and skill. Do not change the selected task or CQ labels.
- The label must depend on seed.knowledge and seed.common_misunderstanding as the hidden answer key.
- Use task_b_item_rules.culture_anchor, task_b_item_rules.item_blueprint, task_b_item_rules.generation_guardrails, task_b_item_rules.cq_expert_skill, and selected_cq_expert_context as binding item-design instructions.

## Use generation_hints
- Follow the selected CQ expert context when it is present.
- If preferred_b_label is present, satisfy it when the seed can support that label. For appropriate, make the decisive action culturally calibrated; for inappropriate, make the decisive action culturally miscalibrated while keeping the interaction superficially reasonable.
- If b_label_balance_context is present, use it as label-control context; do not let the subtopic itself reveal the label.
- If previous_task_b_record is present, preserve only seed_id, item_id, task_type, selected CQ, and the broad cultural assignment. Do not paraphrase its scenario, dialogue, or easy answer pattern.
- If validation_feedback is present, fix that exact issue.

## Anti-Shortcut Detail Rule

Do not directly foreground the decisive cultural keyword in the dialogue, such as exact taboo gestures, body parts, greeting actions, address-form errors, or restricted food ingredients. Prefer describing surrounding execution details such as task flow, service setup, audience, channel, timing, or role assignment, so the answerer must infer the answer through the seed-specific cultural mechanism rather than keyword matching.

The local speaker must not become an answer-giver. The local may provide time pressure, logistics, or ambiguous cues, but must not offer the more correct or safer alternative, or make the label depend on whether the newcomer follows or ignores the local. The decisive behavior must come from the newcomer’s own execution of the cultural mechanism.

## One-Shot Design Process Suggestion
Silently complete these design steps before writing the JSON:

1. Lock the target label:
   - Use preferred_b_label if present; otherwise choose one label internally and commit to it before drafting.

2. Choose two competing frames:
   - A target-culture frame that only someone with the seed knowledge would prioritize.
   - A plausible imported frame from a global SOP, adjacent market, nearby subgroup, legal/process norm, or KPI workflow and so on.
   - Both frames must have some evidence in the dialogue.

3. Add label-specific misdirection:
   - For an appropriate label, include one surface move that looks risky, abrupt, too public, too direct, too efficient, or insufficiently deferential under a generic cross-cultural heuristic, while the decisive action still follows the seed.
   - For an inappropriate label, include one surface move that looks respectful, careful, locally consultative, warm, patient, or professionally reasonable, while the decisive action still departs from the seed.
   - The final judgment should require knowing which detail matters in this culture.

4. Hide the answer key:
   - Do not state, paraphrase, teach, or list the cultural rule in the scenario or dialogue.
   - Do not put all local cues on one side. Include at least one cue that a generic rater could over-weight in the wrong direction.
   - Do not let the last turn reveal the rule, list the missing facts, or summarize the moral of the item.

## Scenario Design Suggestion
- May include a concrete objective, such as decision, approval, repair, briefing, negotiation, classroom/work task, event logistics, meal service, media asset, greeting sequence, or relationship-sensitive coordination and so on.
- May include one real non-cultural constraint: deadline, hierarchy, stakeholder pressure, budget, recording/printing, public/private risk, staffing, logistics, donor/client pressure, or relationship maintenance.
- Keep the diagnostic cultural term low-salience. If a specific word is unavoidable, mention it once as ordinary logistics and surround it with a same-setting decoy detail.
- Do not write scenarios that directly announce the answer key, such as exact restriction lists, explicit title order, ritual order, taboo meaning, or "the local team is worried this is culturally wrong."

## Dialogue Architecture
Prefer 4 rounds. 


## Label-Specific Standards
For appropriate:
- The newcomer's decisive behavior must match the cultural behavior implied by seed.knowledge.
- The newcomer may be fast, direct, public, brief, or constraint-preserving if that is culturally calibrated.
- Do not make appropriate equal to "ask privately," "wait," "follow your lead," or "be extra careful."
- Include at least one action that would look questionable without the seed-specific cultural mechanism.

For inappropriate:
- The newcomer must sound good-faith, competent, and partly adaptive.
- The decisive behavior must conflict with the cultural behavior implied by seed.knowledge, usually by enacting seed.common_misunderstanding or making a narrow miscalibration: wrong scope, wrong actor, wrong stage, wrong channel, wrong intensity, wrong evidence, or wrong sequence.
- Do not make inappropriate equal to obvious rudeness, repeated refusal, reckless efficiency, or ignoring a clear warning.

## Brief Reason
- brief_reason may be explicit because it is the answer key, but it must name the seed-specific mechanism and exact execution axis.
- Avoid generic explanations like "respect local culture," "be polite," "communicate clearly," or "show sensitivity."

Output schema:
{
  "seed_id": "string",
  "item_id": "B_001",
  "task_type": "B",
  "countries_or_regions": ["string"],
  "scenario": "string",
  "roles": {
    "local": "string",
    "newcomer": "string"
  },
  "dialogue_round": 4,
  "dialogue": [
    {"speaker": "Local", "text": "string"},
    {"speaker": "Newcomer", "text": "string"},
    {"speaker": "Local", "text": "string"},
    {"speaker": "Newcomer", "text": "string"},
    {"speaker": "Local", "text": "string"},
    {"speaker": "Newcomer", "text": "string"},
    {"speaker": "Local", "text": "string"},
    {"speaker": "Newcomer", "text": "string"}
  ],
  "label": "appropriate|inappropriate",
  "brief_reason": "string",
  "cq_tags": ["behavioural"],
  "difficulty": "easy|medium|hard"
}
