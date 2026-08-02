from dataclasses import dataclass
from enum import Enum


class LifecycleState(Enum):
    BOOT = "boot"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class Lifecycle:
    state: LifecycleState = LifecycleState.BOOT

    def initialize(self):
        self.state = LifecycleState.INITIALIZING

    def ready(self):
        self.state = LifecycleState.READY

    def start(self):
        self.state = LifecycleState.RUNNING

    def stop(self):
        self.state = LifecycleState.STOPPING

    def stopped(self):
        self.state = LifecycleState.STOPPED

    def fail(self):
        self.state = LifecycleState.ERROR
