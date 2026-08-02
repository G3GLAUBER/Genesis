from dataclasses import dataclass

from Core.result import Result
from Engines.AI.models import AIRequest, AIResponse
from Engines.AI.provider import AIProvider


@dataclass(frozen=True)
class FakeProvider(AIProvider):
    should_fail: bool = False
    response_prefix: str = "Fake: "

    @property
    def provider_id(self) -> str:
        return "fake"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("text_generation",)

    def generate(self, request: AIRequest) -> Result:
        if self.should_fail:
            return Result.error(
                message="Falha controlada do FakeProvider",
            )

        if request.capability not in self.capabilities:
            return Result.error(
                message=(
                    "Capacidade não suportada pelo FakeProvider: "
                    f"{request.capability}"
                ),
            )

        response = AIResponse(
            provider_id=self.provider_id,
            content=f"{self.response_prefix}{request.prompt}",
            capability=request.capability,
        )

        return Result.success(
            message="Resposta gerada pelo FakeProvider",
            data=response,
        )
