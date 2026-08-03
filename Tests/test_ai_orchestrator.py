from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from Core.registry import Registry
from Core.result import Result
from Engines.AI import (
    AIOrchestrationFailure,
    AIOrchestrator,
    AIProvider,
    AIProviderAttempt,
    AIRequest,
    AIResponse,
    FakeProvider,
)


class StubProvider(AIProvider):
    def __init__(
        self,
        provider_id: str,
        *,
        capabilities: tuple[str, ...] = ("text_generation",),
        outcome: object | None = None,
    ) -> None:
        self._provider_id = provider_id
        self._capabilities = capabilities
        self._outcome = outcome or success_result(provider_id)
        self.generate_calls = 0

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    def generate(self, request: AIRequest) -> Result:
        self.generate_calls += 1

        if isinstance(self._outcome, Exception):
            raise self._outcome

        return cast(Result, self._outcome)


def success_result(
    provider_id: str,
    *,
    capability: str = "text_generation",
) -> Result:
    return Result.success(
        message=f"Sucesso de {provider_id}",
        data=AIResponse(
            provider_id=provider_id,
            content=f"Resposta de {provider_id}",
            capability=capability,
        ),
    )


def register(registry: Registry, *providers: AIProvider) -> None:
    for provider in providers:
        registry.register(provider.provider_id, provider)


def test_v1_single_provider_api_remains_compatible():
    registry = Registry()
    provider = FakeProvider()
    register(registry, provider)
    orchestrator = AIOrchestrator(registry, provider_id="fake")

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert orchestrator.provider_ids == ("fake",)
    assert result.is_success is True
    assert result.data == AIResponse(
        provider_id="fake",
        content="Fake: Olá",
        capability="text_generation",
    )


def test_selects_provider_compatible_with_requested_capability():
    registry = Registry()
    text_provider = StubProvider("text")
    image_provider = StubProvider(
        "image",
        capabilities=("image_generation",),
        outcome=success_result(
            "image",
            capability="image_generation",
        ),
    )
    register(registry, text_provider, image_provider)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("text", "image"),
    )

    result = orchestrator.generate(
        AIRequest(prompt="Imagem", capability="image_generation")
    )

    assert result.is_success is True
    assert result.data.provider_id == "image"


def test_incompatible_provider_is_not_executed():
    registry = Registry()
    incompatible = StubProvider(
        "image",
        capabilities=("image_generation",),
    )
    compatible = StubProvider("text")
    register(registry, incompatible, compatible)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("image", "text"),
    )

    result = orchestrator.generate(AIRequest(prompt="Texto"))

    assert result.is_success is True
    assert incompatible.generate_calls == 0
    assert compatible.generate_calls == 1


def test_provider_priority_order_is_respected():
    registry = Registry()
    primary = StubProvider("primary")
    secondary = StubProvider("secondary")
    register(registry, primary, secondary)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("secondary", "primary"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert orchestrator.provider_ids == ("secondary", "primary")
    assert result.data.provider_id == "secondary"


def test_explicit_intelligence_order_reuses_orchestrator_pipeline():
    registry = Registry()
    configured_first = StubProvider("configured-first")
    routed_first = StubProvider("routed-first")
    register(registry, configured_first, routed_first)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("configured-first", "routed-first"),
    )

    result = orchestrator.generate_with_order(
        AIRequest(prompt="Olá"),
        ("routed-first", "configured-first"),
    )

    assert result.data.provider_id == "routed-first"
    assert routed_first.generate_calls == 1
    assert configured_first.generate_calls == 0


def test_first_provider_success_is_returned():
    registry = Registry()
    first = StubProvider("first")
    second = StubProvider("second")
    register(registry, first, second)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("first", "second"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is True
    assert result.data.provider_id == "first"


def test_fallback_after_result_error_returns_second_success():
    registry = Registry()
    first = StubProvider(
        "first",
        outcome=Result.error("Falha controlada"),
    )
    second = StubProvider("second")
    register(registry, first, second)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("first", "second"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is True
    assert result.data.provider_id == "second"
    assert first.generate_calls == 1
    assert second.generate_calls == 1


def test_fallback_after_exception_returns_second_success():
    registry = Registry()
    first = StubProvider(
        "first",
        outcome=RuntimeError("segredo que não deve vazar"),
    )
    second = StubProvider("second")
    register(registry, first, second)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("first", "second"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is True
    assert result.data.provider_id == "second"


def test_all_result_errors_return_total_failure():
    registry = Registry()
    first = StubProvider("first", outcome=Result.error("Falha 1"))
    second = StubProvider("second", outcome=Result.error("Falha 2"))
    register(registry, first, second)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("first", "second"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.message == (
        "Todos os provedores compatíveis falharam para: text_generation"
    )
    assert result.data.attempts == (
        AIProviderAttempt("first", "error"),
        AIProviderAttempt("second", "error"),
    )


def test_all_exceptions_return_safe_total_failure():
    registry = Registry()
    first = StubProvider("first", outcome=RuntimeError("token=secret"))
    second = StubProvider("second", outcome=ValueError("key=secret"))
    register(registry, first, second)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("first", "second"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.data.attempts == (
        AIProviderAttempt("first", "exception", "RuntimeError"),
        AIProviderAttempt("second", "exception", "ValueError"),
    )
    assert "secret" not in repr(result.data)


def test_no_provider_supports_requested_capability():
    registry = Registry()
    provider = StubProvider("text")
    register(registry, provider)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("text",),
    )

    result = orchestrator.generate(
        AIRequest(prompt="Imagem", capability="image_generation")
    )

    assert result.is_success is False
    assert result.message == (
        "Nenhum provedor compatível disponível para: image_generation"
    )
    assert result.data == AIOrchestrationFailure(
        capability="image_generation",
        attempts=(),
    )
    assert provider.generate_calls == 0


def test_empty_registry_returns_controlled_failure():
    orchestrator = AIOrchestrator(
        Registry(),
        provider_ids=("missing",),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.data.attempts == (
        AIProviderAttempt("missing", "missing"),
    )


def test_invalid_registered_type_returns_controlled_failure():
    registry = Registry()
    registry.register("invalid", object())
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("invalid",),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.data.attempts == (
        AIProviderAttempt("invalid", "invalid_provider"),
    )


def test_provider_registered_with_wrong_identity_is_not_executed():
    registry = Registry()
    provider = StubProvider("actual")
    registry.register("alias", provider)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("alias",),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.data.attempts == (
        AIProviderAttempt("alias", "identity_mismatch"),
    )
    assert provider.generate_calls == 0


@pytest.mark.parametrize(
    ("outcome", "expected_status"),
    [
        ("fora do contrato", "invalid_result"),
        (
            Result.success("Sem AIResponse"),
            "invalid_response",
        ),
        (
            success_result("outro"),
            "invalid_response_provider",
        ),
    ],
)
def test_invalid_provider_success_contract_is_recorded(
    outcome,
    expected_status,
):
    registry = Registry()
    invalid = StubProvider("invalid", outcome=outcome)
    register(registry, invalid)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("invalid",),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is False
    assert result.data.attempts == (
        AIProviderAttempt("invalid", expected_status),
    )
    assert invalid.generate_calls == 1


def test_success_response_identifies_winning_provider():
    registry = Registry()
    first = StubProvider("first", outcome=Result.error("Falha"))
    winner = StubProvider("winner")
    register(registry, first, winner)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("first", "winner"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert isinstance(result.data, AIResponse)
    assert result.data.provider_id == "winner"


def test_total_failure_contains_ordered_structured_attempt_history():
    registry = Registry()
    failed = StubProvider("failed", outcome=Result.error("Falha"))
    crashed = StubProvider("crashed", outcome=RuntimeError("segredo"))
    register(registry, failed, crashed)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("missing", "failed", "crashed"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert isinstance(result.data, AIOrchestrationFailure)
    assert result.data.capability == "text_generation"
    assert result.data.attempts == (
        AIProviderAttempt("missing", "missing"),
        AIProviderAttempt("failed", "error"),
        AIProviderAttempt("crashed", "exception", "RuntimeError"),
    )

    with pytest.raises(FrozenInstanceError):
        result.data.capability = "outra"


def test_no_provider_runs_after_first_success():
    registry = Registry()
    winner = StubProvider("winner")
    second = StubProvider("second")
    third = StubProvider("third")
    register(registry, winner, second, third)
    orchestrator = AIOrchestrator(
        registry,
        provider_ids=("winner", "second", "third"),
    )

    result = orchestrator.generate(AIRequest(prompt="Olá"))

    assert result.is_success is True
    assert winner.generate_calls == 1
    assert second.generate_calls == 0
    assert third.generate_calls == 0


def test_v1_and_v2_provider_configuration_are_mutually_exclusive():
    with pytest.raises(ValueError, match="não ambos"):
        AIOrchestrator(
            Registry(),
            provider_id="legacy",
            provider_ids=("primary",),
        )
