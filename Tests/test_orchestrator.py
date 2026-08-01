import pytest

from Core.context import Context
from Core.Orchestrator.orchestrator import Orchestrator
from Core.registry import Registry


def test_register_and_dispatch_command():
    registry = Registry()
    orchestrator = Orchestrator(registry)

    def example_handler():
        return "executado"

    orchestrator.register("example", example_handler)

    context = Context.create(
        session_id="session-001",
        command="example",
        source="TEST",
    )

    result = orchestrator.dispatch(context)

    assert result == "executado"


def test_dispatch_unknown_command_raises_error():
    registry = Registry()
    orchestrator = Orchestrator(registry)

    context = Context.create(
        session_id="session-002",
        command="inexistente",
        source="TEST",
    )

    with pytest.raises(ValueError, match="Comando desconhecido"):
        orchestrator.dispatch(context)
