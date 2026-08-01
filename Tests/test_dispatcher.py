from Core.event_bus import EventBus
from Core.events import Event, EventType


bus = EventBus()


def agente_a(event):
    print("Agente A recebeu:", event.data)


def agente_b(event):
    print("Agente B recebeu:", event.data)


bus.subscribe(EventType.NEW_IDEA, agente_a)
bus.subscribe(EventType.NEW_IDEA, agente_b)

bus.publish(
    Event(
        event_type=EventType.NEW_IDEA,
        data={
            "titulo": "Projeto Gênesis"
        }
    )
)