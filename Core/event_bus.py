from collections import defaultdict
from collections.abc import Callable

from Core.dispatcher import Dispatcher
from Core.events import Event, EventType


class EventBus:
    """
    Responsável por registrar listeners e publicar eventos.
    """

    def __init__(self, dispatcher: Dispatcher | None = None):
        self._listeners: dict[EventType, list[Callable[[Event], None]]] = (
            defaultdict(list)
        )
        self._dispatcher = dispatcher or Dispatcher()

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None],
    ) -> None:
        self._listeners[event_type].append(callback)

    def publish(self, event: Event) -> None:
        listeners = list(self._listeners.get(event.event_type, []))
        self._dispatcher.dispatch(listeners, event)
