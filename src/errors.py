class MultiCultureError(Exception):
    """Base project error."""


class SchemaValidationError(MultiCultureError):
    """Raised when a schema payload fails validation."""


class ConfigError(MultiCultureError):
    """Raised when configuration is missing or malformed."""


class JSONParseError(MultiCultureError):
    """Raised when model output cannot be parsed as JSON."""


class LLMClientError(MultiCultureError):
    """Raised for upstream LLM client failures."""


class RejectionError(MultiCultureError):
    """Raised when a seed or item should be rejected."""

    def __init__(self, stage: str, reason: str):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
