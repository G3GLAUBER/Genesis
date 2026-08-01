import pytest

from Core.Orchestrator.orchestrator import Orchestrator


def test_register_and_dispatch_command():
    orchestrator = Orchestrator()

    def example_handler():
        return "executado"

    orchestrator.register("example", example_handler)

    result = orchestrator.dispatch("example")

    assert result == "executado"


def test_dispatch_unknown_command_raises_error():
    orchestrator = Orchestrator()

    with pytest.raises(ValueError, match="Comando desconhecido"):
        orchestrator.dispatch("inexistente")
