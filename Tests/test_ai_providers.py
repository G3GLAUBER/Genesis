from dataclasses import FrozenInstanceError
from inspect import isabstract

import pytest

from Core.registry import Registry
from Core.result import Result
from Engines.AI import AIProvider, AIRequest, AIResponse, FakeProvider


def test_ai_provider_defines_an_abstract_contract():
    assert isabstract(AIProvider)

    with pytest.raises(TypeError):
        AIProvider()


def test_provider_exposes_identity_and_capabilities():
    provider = FakeProvider()

    assert provider.provider_id == "fake"
    assert provider.capabilities == ("text_generation",)


def test_ai_request_is_immutable():
    request = AIRequest(prompt="Olá")

    with pytest.raises(FrozenInstanceError):
        request.prompt = "Outro prompt"


def test_ai_response_is_immutable():
    response = AIResponse(
        provider_id="fake",
        content="Resposta",
        capability="text_generation",
    )

    with pytest.raises(FrozenInstanceError):
        response.content = "Outro conteúdo"


def test_registry_registers_and_recovers_provider():
    registry = Registry()
    provider = FakeProvider()

    registry.register(provider.provider_id, provider)

    assert registry.get("fake") is provider
    assert registry.list() == ["fake"]


def test_registry_rejects_duplicate_provider():
    registry = Registry()
    provider = FakeProvider()
    registry.register(provider.provider_id, provider)

    with pytest.raises(ValueError, match="Módulo já registrado: fake"):
        registry.register(provider.provider_id, provider)


def test_registry_rejects_missing_provider():
    registry = Registry()

    with pytest.raises(ValueError, match="Módulo não encontrado: ausente"):
        registry.get("ausente")


def test_fake_provider_generates_success_result():
    provider = FakeProvider()
    request = AIRequest(prompt="Explique o Gênesis")

    result = provider.generate(request)

    assert isinstance(result, Result)
    assert result.is_success is True
    assert result.message == "Resposta gerada pelo FakeProvider"
    assert result.data == AIResponse(
        provider_id="fake",
        content="Fake: Explique o Gênesis",
        capability="text_generation",
    )


def test_fake_provider_returns_controlled_error():
    provider = FakeProvider(should_fail=True)

    result = provider.generate(AIRequest(prompt="Falhar"))

    assert isinstance(result, Result)
    assert result.is_success is False
    assert result.message == "Falha controlada do FakeProvider"
    assert result.data is None


def test_fake_provider_rejects_unsupported_capability():
    provider = FakeProvider()
    request = AIRequest(prompt="Imagem", capability="image_generation")

    result = provider.generate(request)

    assert result.is_success is False
    assert "Capacidade não suportada" in result.message
    assert result.data is None
