import json
import os
import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.errors import ConfigError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "configs"
LOCAL_SETTINGS_PATH = PROJECT_ROOT / "src" / "local_settings.py"
RUNTIME_SETTING_NAMES = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "MCG_USE_MOCK_LLM",
)


def _strip_comment(line: str) -> str:
    if "#" not in line:
        return line
    inside_quote = False
    quote_char = ""
    output = []
    for char in line:
        if char in ("'", '"'):
            if inside_quote and char == quote_char:
                inside_quote = False
                quote_char = ""
            elif not inside_quote:
                inside_quote = True
                quote_char = char
        if char == "#" and not inside_quote:
            break
        output.append(char)
    return "".join(output)


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text == "":
        return ""
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if text[0] in ('"', "'", "[", "{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if text[0] == text[-1] and text[0] in ('"', "'"):
                return text[1:-1]
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _prepare_yaml_lines(text: str) -> List[Tuple[int, str]]:
    lines: List[Tuple[int, str]] = []
    for raw_line in text.splitlines():
        cleaned = _strip_comment(raw_line).rstrip()
        if not cleaned.strip():
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        lines.append((indent, cleaned.strip()))
    return lines


def _parse_yaml_block(lines: List[Tuple[int, str]], start: int, indent: int) -> Tuple[Any, int]:
    mapping: Dict[str, Any] = {}
    sequence: Optional[List[Any]] = None
    index = start

    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ConfigError(f"Unexpected indentation in config near: {content}")

        if content.startswith("- "):
            if mapping:
                raise ConfigError("Cannot mix list and mapping at the same indentation level.")
            if sequence is None:
                sequence = []
            value_text = content[2:].strip()
            if not value_text:
                value, index = _parse_yaml_block(lines, index + 1, indent + 2)
                sequence.append(value)
                continue
            sequence.append(_parse_scalar(value_text))
            index += 1
            continue

        if sequence is not None:
            raise ConfigError("Cannot mix list and mapping at the same indentation level.")

        key, sep, remainder = content.partition(":")
        if sep != ":":
            raise ConfigError(f"Invalid config line: {content}")
        key = key.strip()
        remainder = remainder.strip()
        if remainder:
            mapping[key] = _parse_scalar(remainder)
            index += 1
            continue

        value, index = _parse_yaml_block(lines, index + 1, indent + 2)
        mapping[key] = value

    return (sequence if sequence is not None else mapping), index


def parse_config_text(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {}
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        lines = _prepare_yaml_lines(stripped)
        parsed, _ = _parse_yaml_block(lines, 0, 0)
    if not isinstance(parsed, dict):
        raise ConfigError("Top-level config payload must be a mapping.")
    return parsed


def load_config_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    return parse_config_text(path.read_text(encoding="utf-8"))


def _stringify_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _load_python_settings(path: Path = LOCAL_SETTINGS_PATH) -> Dict[str, str]:
    if os.getenv("MCG_SKIP_LOCAL_SETTINGS", "false").lower() in ("1", "true", "yes", "on"):
        return {}
    if not path.exists():
        return {}

    payload = runpy.run_path(str(path))
    loaded: Dict[str, str] = {}

    runtime_settings = payload.get("RUNTIME_SETTINGS")
    if isinstance(runtime_settings, dict):
        for key, value in runtime_settings.items():
            if value is not None:
                loaded[str(key)] = _stringify_env_value(value)

    for key in RUNTIME_SETTING_NAMES:
        value = payload.get(key)
        if value is not None:
            loaded[key] = _stringify_env_value(value)

    return loaded


def load_env_file(path: Optional[Path] = None, override: bool = True) -> Dict[str, str]:
    """Load project runtime variables.

    src/local_settings.py is treated as the strongest project-local source by
    default, so a server-level OPENAI_API_KEY cannot silently override the key
    intended for this project. .env is still supported as a fallback. Pass
    override=False only when inherited shell variables should take precedence.
    """
    loaded: Dict[str, str] = {}

    if os.getenv("MCG_SKIP_DOTENV", "false").lower() not in ("1", "true", "yes", "on"):
        env_path = path or (PROJECT_ROOT / ".env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                loaded[key.strip()] = value.strip().strip('"').strip("'")

    loaded.update(_load_python_settings())

    if override:
        os.environ.update(loaded)
    else:
        os.environ.update({key: value for key, value in loaded.items() if key not in os.environ})
    return loaded


@dataclass(frozen=True)
class ModelSection:
    temperature: float
    max_tokens: int
    reasoning_effort: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelSection":
        return cls(
            temperature=float(data.get("temperature", 0.0)),
            max_tokens=int(data.get("max_tokens", 1024)),
            reasoning_effort=str(data["reasoning_effort"]) if data.get("reasoning_effort") is not None else None,
        )


@dataclass(frozen=True)
class ModelConfig:
    moderator: ModelSection
    cq_expert: ModelSection
    item_generator: ModelSection
    validator: ModelSection

    @classmethod
    def load(cls, config_dir: Path = DEFAULT_CONFIG_DIR) -> "ModelConfig":
        data = load_config_file(config_dir / "model.yaml")
        return cls(
            moderator=ModelSection.from_dict(data.get("moderator", {})),
            cq_expert=ModelSection.from_dict(data.get("cq_expert", {})),
            item_generator=ModelSection.from_dict(data.get("item_generator", {})),
            validator=ModelSection.from_dict(data.get("validator", data.get("moderator", {}))),
        )


@dataclass(frozen=True)
class GenerationConfig:
    target_total_items: int
    allow_task_types: List[str]
    allow_cq_tags: List[str]
    default_max_retries: int
    max_quality_attempts: int

    @classmethod
    def load(cls, config_dir: Path = DEFAULT_CONFIG_DIR) -> "GenerationConfig":
        data = load_config_file(config_dir / "generation.yaml")
        max_quality_attempts = int(data.get("max_quality_attempts", 8))
        if not 1 <= max_quality_attempts <= 8:
            raise ConfigError("max_quality_attempts must be between 1 and 8.")
        return cls(
            target_total_items=int(data.get("target_total_items", 0)),
            allow_task_types=list(data.get("allow_task_types", [])),
            allow_cq_tags=list(data.get("allow_cq_tags", [])),
            default_max_retries=int(data.get("default_max_retries", 3)),
            max_quality_attempts=max_quality_attempts,
        )


@dataclass(frozen=True)
class DistributionConfig:
    coverage_dimensions: List[str]

    @classmethod
    def load(cls, config_dir: Path = DEFAULT_CONFIG_DIR) -> "DistributionConfig":
        data = load_config_file(config_dir / "distribution.yaml")
        dimensions = [str(value) for value in data.get("coverage_dimensions", [])]
        allowed = {"task_cq", "major_topic", "regions"}
        invalid = [value for value in dimensions if value not in allowed]
        if invalid:
            raise ConfigError(f"Unsupported distribution coverage dimensions: {invalid}")
        if not dimensions:
            raise ConfigError("coverage_dimensions must contain at least one dimension.")
        return cls(coverage_dimensions=dimensions)
