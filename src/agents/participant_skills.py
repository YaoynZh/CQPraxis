from functools import lru_cache
from pathlib import Path
from typing import Dict

from src.config import PROJECT_ROOT


PARTICIPANT_SKILLS_DIR = PROJECT_ROOT / "src" / "llm" / "participant_skills"

CQ_SKILL_DIRS = {
    "metacognitive": "metacognitive_cq_expert",
    "cognitive": "cognitive_cq_expert",
    "motivational": "motivational_cq_expert",
    "behavioural": "behavioural_cq_expert",
}

MODERATOR_SKILL_DIR = "multi_culture_moderator"


def _skill_path(skill_dir: str) -> Path:
    return PARTICIPANT_SKILLS_DIR / skill_dir / "skill.md"


@lru_cache(maxsize=None)
def _read_skill(skill_dir: str) -> str:
    path = _skill_path(skill_dir)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_moderator_skill() -> str:
    return _read_skill(MODERATOR_SKILL_DIR)


def load_cq_expert_skill(cq_tag: str) -> str:
    skill_dir = CQ_SKILL_DIRS.get(cq_tag)
    if skill_dir is None:
        return ""
    return _read_skill(skill_dir)


def load_cq_expert_skills() -> Dict[str, str]:
    return {cq_tag: load_cq_expert_skill(cq_tag) for cq_tag in CQ_SKILL_DIRS}
