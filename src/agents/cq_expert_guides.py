from typing import Dict


CQ_EXPERT_GUIDES: Dict[str, Dict[str, object]] = {
    "cognitive": {
        "core_target": "Apply cultural knowledge correctly in context; separate culture from process, personality, timing, and stereotype.",
        "quality_focus": [
            "Use concrete decisions or wording, not abstract framework ranking.",
            "Make seed-specific knowledge defeat a generic business heuristic.",
            "Include a true-but-misapplied norm, policy, theory, or practice from seed knowledge.",
            "For Task B, make the label turn on a culture-specific discriminator rather than on whether the newcomer asks, waits, or sounds respectful.",
            "For Task B, include mixed evidence and one opposite-surface cue so the answer cannot be read from compliance with local hints.",
        ],
        "distractor_traps": [
            "Generic business explanation misses culture.",
            "Cross-cultural decoy works elsewhere but not here.",
            "True cultural rule used at wrong scope or stage.",
            "Subtopic-label shortcut: a familiar topic like touch, vegetarian food, or titles predicts the answer without reading the dialogue.",
            "Solved-example shortcut: the final turn reveals the exact cultural rule or presents the clean repair.",
        ],
    },
    "metacognitive": {
        "core_target": "Calibrate under uncertainty: infer enough to act while keeping what remains unknown visible.",
        "quality_focus": [
            "Ask for concrete action, timing, evidence, or briefing under uncertainty.",
            "Make broad caution or private checking sometimes wrong.",
            "Use contextual noise and stakeholder variation.",
            "For Task B, make the update hinge on which uncertainty matters in this culture, not on generic humility or asking more questions.",
            "For Task B, include one cue that should be discounted; do not let every later cue point toward the same label.",
        ],
        "distractor_traps": [
            "Careful but inert.",
            "Decisive but overconfident.",
            "Checks only to confirm the original assumption.",
            "Stock calibration cue: the apparently cautious newcomer is automatically treated as correct.",
            "Cue-following shortcut: the newcomer simply obeys or ignores a local hint rather than calibrating competing signals.",
        ],
    },
    "motivational": {
        "core_target": "Sustain adaptive engagement when cross-cultural work costs time, status, comfort, or resources.",
        "quality_focus": [
            "Correct answer must pay a visible cost in effort, status, time, or resources.",
            "Make friendliness/inclusion insufficient without follow-through.",
            "Use slow progress, ambiguity, or relationship work as the cost.",
            "For Task B, make effort culturally targeted; warm persistence, withdrawal, patience, and speed can each be right or wrong depending on the seed.",
            "For Task B, put genuine effort on both sides of the label so the test is where effort is placed.",
        ],
        "distractor_traps": [
            "Energetic but intrusive.",
            "Respectful but withdrawn.",
            "Patient but shifts adaptation burden to locals.",
            "Friendly-tone shortcut: the warmer or more patient dialogue is assumed to be appropriate.",
            "Obvious persistence shortcut: the final line makes extra effort visibly successful or visibly misplaced.",
        ],
    },
    "behavioural": {
        "core_target": "Choose calibrated wording, timing, channel, audience, sequence, and follow-up.",
        "quality_focus": [
            "Use concrete action or sequence options.",
            "Correct answer should cost speed, clarity, ease, or comfort while fitting the context.",
            "Make softness/politeness insufficient when active timing matters.",
            "For Task B, make timing, channel, audience, or sequence depend on the target knowledge, not on a universal polite-script default.",
            "For Task B, mix one calibrated behavior with one questionable behavior so the decisive execution detail is small.",
        ],
        "distractor_traps": [
            "Right message, wrong channel.",
            "Right channel, wrong timing.",
            "Efficient but rhythm-breaking or over-accommodating.",
            "Template cue: appropriate equals 'follow your lead' or inappropriate equals 'No need / skip / reply-all'.",
            "Final-action shortcut: the last newcomer turn is a clean fix or a repeated wrong plan.",
        ],
    },
}


def build_cq_expert_guidance(cq_tag: str) -> Dict[str, object]:
    return CQ_EXPERT_GUIDES.get(
        cq_tag,
        {
            "core_target": "Test deeper cross-cultural judgment in context.",
            "quality_focus": ["Use concrete tradeoffs and plausible near-misses."],
            "distractor_traps": ["Wrong answers should be partly true but misapplied."],
        },
    )
