import pytest

from Core.Orchestrator.orchestrator import Orchestrator
from Core.registry import Registry


def test_register_and_dispatch_command():
    registry = Registry()
    orchestrator = Orchestrator(registry)

    def example_handler():
        return "executado"

    orchestrator.register("example", example_handler)

    result = orchestrator.dispatch("example")

    assert result == "executado"


def test_dispatch_unknown_command_raises_error():
    registry = Registry()
    orchestrator = Orchestrator(registry)

    with pytest.raises(ValueError, match="Comando desconhecido"):
        orchestrator.dispatch("inexistente")
