from Core.event_bus import EventBus
from Core.events import Event, EventType


bus = EventBus()


def ideia_recebida(event):
    print("Nova ideia recebida!")
    print(event.data)


bus.subscribe(EventType.NEW_IDEA, ideia_recebida)

bus.publish(
    Event(
        event_type=EventType.NEW_IDEA,
        data={
            "titulo": "Construir o Gênesis"
        }
    )
)