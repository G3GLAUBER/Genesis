from collections import defaultdict

from Core.dispatcher import Dispatcher


class EventBus:

    def __init__(self):

        self.listeners = defaultdict(list)

        self.dispatcher = Dispatcher()

    def subscribe(self, event_type, callback):

        self.listeners[event_type].append(callback)

    def publish(self, event):

        listeners = self.listeners.get(event.event_type, [])

        self.dispatcher.dispatch(listeners, event)