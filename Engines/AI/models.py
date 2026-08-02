from dataclasses import dataclass


@dataclass(frozen=True)
class AIRequest:
    prompt: str
    capability: str = "text_generation"


@dataclass(frozen=True)
class AIResponse:
    provider_id: str
    content: str
    capability: str


@dataclass(frozen=True)
class AIProviderAttempt:
    provider_id: str
    outcome: str
    error_type: str | None = None


@dataclass(frozen=True)
class AIOrchestrationFailure:
    capability: str
    attempts: tuple[AIProviderAttempt, ...]
