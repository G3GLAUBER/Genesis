from Core.event_bus import EventBus
from Core.events import Event, EventType


def test_event_bus_publishes_event_to_listener():
    event_bus = EventBus()
    received_events = []

    def listener(event):
        received_events.append(event)

    event_bus.subscribe(EventType.SYSTEM_START, listener)

    event = Event(
        event_type=EventType.SYSTEM_START,
        data={"status": "started"},
    )

    event_bus.publish(event)

    assert received_events == [event]


def test_event_bus_notifies_multiple_listeners():
    event_bus = EventBus()
    calls = []

    def first_listener(event):
        calls.append(("first", event))

    def second_listener(event):
        calls.append(("second", event))

    event_bus.subscribe(EventType.NEW_TASK, first_listener)
    event_bus.subscribe(EventType.NEW_TASK, second_listener)

    event = Event(
        event_type=EventType.NEW_TASK,
        data={"task": "testar EventBus"},
    )

    event_bus.publish(event)

    assert calls == [
        ("first", event),
        ("second", event),
    ]


def test_listener_failure_does_not_stop_other_listeners(capsys):
    event_bus = EventBus()
    successful_calls = []

    def failing_listener(event):
        raise RuntimeError("falha simulada")

    def successful_listener(event):
        successful_calls.append(event)

    event_bus.subscribe(EventType.NEW_MESSAGE, failing_listener)
    event_bus.subscribe(EventType.NEW_MESSAGE, successful_listener)

    event = Event(
        event_type=EventType.NEW_MESSAGE,
        data={"message": "Olá"},
    )

    event_bus.publish(event)

    output = capsys.readouterr().out

    assert successful_calls == [event]
    assert "[ERROR]" in output
    assert "falha simulada" in output
