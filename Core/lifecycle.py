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

    def initialize(self) -> None:
        self.state = LifecycleState.INITIALIZING

    def ready(self) -> None:
        self.state = LifecycleState.READY

    def start(self) -> None:
        self.state = LifecycleState.RUNNING

    def stop(self) -> None:
        self.state = LifecycleState.STOPPING

    def stopped(self) -> None:
        self.state = LifecycleState.STOPPED

    def fail(self) -> None:
        self.state = LifecycleState.ERROR
