from Core.registry import Registry
from Core.result import Result
from Engines.AI import (
    AIOrchestrator,
    AIProvider,
    AIRequest,
    AIResponse,
    FakeProvider,
)


class RecordingProvider(AIProvider):
    def __init__(self) -> None:
        self.generate_calls = 0

    @property
    def provider_id(self) -> str:
        return "recording"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("text_generation",)

    def generate(self, request: AIRequest) -> Result:
        self.generate_calls += 1
        return Result.success(
            message="Resposta gravada",
            data=AIResponse(
                provider_id=self.provider_id,
                content=request.prompt,
                capability=request.capability,
            ),
        )


def test_orchestrator_generates_response_through_configured_provider():
    registry = Registry()
    provider = FakeProvider()
    registry.register(provider.provider_id, provider)
    orchestrator = AIOrchestrator(registry, provider_id="fake")

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is True
    assert result.data == AIResponse(
        provider_id="fake",
        content="Fake: Olá",
        capability="text_generation",
    )


def test_orchestrator_returns_error_when_provider_is_missing():
    orchestrator = AIOrchestrator(Registry(), provider_id="ausente")

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.message == "Provedor de IA não encontrado: ausente"
    assert result.data is None


def test_orchestrator_rejects_item_that_is_not_a_provider():
    registry = Registry()
    registry.register("invalido", object())
    orchestrator = AIOrchestrator(registry, provider_id="invalido")

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.message == (
        "Item registrado não implementa AIProvider: invalido"
    )
    assert result.data is None


def test_orchestrator_rejects_provider_registered_with_wrong_identity():
    registry = Registry()
    provider = RecordingProvider()
    registry.register("alias", provider)
    orchestrator = AIOrchestrator(registry, provider_id="alias")

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.message == (
        "Identificador do provedor não corresponde ao registro: "
        "esperado 'alias', recebido 'recording'"
    )
    assert result.data is None
    assert provider.generate_calls == 0


def test_orchestrator_validates_capability_before_generation():
    registry = Registry()
    provider = RecordingProvider()
    registry.register(provider.provider_id, provider)
    orchestrator = AIOrchestrator(registry, provider_id="recording")
    request = AIRequest(
        prompt="Crie uma imagem",
        capability="image_generation",
    )

    result = orchestrator.generate(request)

    assert result.is_success is False
    assert result.message == (
        "Capacidade não suportada pelo provedor "
        "'recording': image_generation"
    )
    assert result.data is None
    assert provider.generate_calls == 0


def test_orchestrator_propagates_controlled_provider_error():
    registry = Registry()
    provider = FakeProvider(should_fail=True)
    registry.register(provider.provider_id, provider)
    orchestrator = AIOrchestrator(registry, provider_id="fake")

    result = orchestrator.generate(AIRequest(prompt="Falhar"))

    assert result.is_success is False
    assert result.message == "Falha controlada do FakeProvider"
    assert result.data is None
