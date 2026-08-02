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
