from Core.dispatcher import Dispatcher
from Core.events import Event, EventType


def test_dispatcher_executes_all_callbacks():
    dispatcher = Dispatcher()
    calls = []
    event = Event(
        event_type=EventType.NEW_IDEA,
        data={"titulo": "Projeto Gênesis"},
    )

    def agente_a(received_event):
        calls.append(("a", received_event))

    def agente_b(received_event):
        calls.append(("b", received_event))

    dispatcher.dispatch([agente_a, agente_b], event)

    assert calls == [("a", event), ("b", event)]


def test_callable_without_name_does_not_interrupt_dispatch(capsys):
    dispatcher = Dispatcher()
    calls = []
    event = Event(
        event_type=EventType.NEW_IDEA,
        data={"titulo": "Projeto Gênesis"},
    )

    class FailingListener:
        def __call__(self, received_event):
            raise RuntimeError("falha simulada")

    def successful_listener(received_event):
        calls.append(received_event)

    dispatcher.dispatch(
        [FailingListener(), successful_listener],
        event,
    )

    output = capsys.readouterr().out

    assert calls == [event]
    assert "FailingListener" in output
    assert "falha simulada" in output
