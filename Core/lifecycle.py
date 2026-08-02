from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


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

    _VALID_TRANSITIONS: ClassVar[dict[LifecycleState, LifecycleState]] = {
        LifecycleState.BOOT: LifecycleState.INITIALIZING,
        LifecycleState.INITIALIZING: LifecycleState.READY,
        LifecycleState.READY: LifecycleState.RUNNING,
        LifecycleState.RUNNING: LifecycleState.STOPPING,
        LifecycleState.STOPPING: LifecycleState.STOPPED,
    }

    def __post_init__(self) -> None:
        if not isinstance(self.state, LifecycleState):
            raise ValueError(f"Estado inicial inválido: {self.state!r}")

        object.__setattr__(self, "_state_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if name == "state" and getattr(self, "_state_locked", False):
            raise AttributeError(
                "Lifecycle.state é somente leitura; "
                "use os métodos de transição"
            )

        object.__setattr__(self, name, value)

    def _transition(self, target: LifecycleState) -> None:
        if target is LifecycleState.ERROR:
            object.__setattr__(self, "state", target)
            return

        expected_target = self._VALID_TRANSITIONS.get(self.state)

        if target is not expected_target:
            raise ValueError(
                "Transição inválida do Lifecycle: "
                f"{self.state.name} -> {target.name}"
            )

        object.__setattr__(self, "state", target)

    def initialize(self) -> None:
        self._transition(LifecycleState.INITIALIZING)

    def ready(self) -> None:
        self._transition(LifecycleState.READY)

    def start(self) -> None:
        self._transition(LifecycleState.RUNNING)

    def stop(self) -> None:
        self._transition(LifecycleState.STOPPING)

    def stopped(self) -> None:
        self._transition(LifecycleState.STOPPED)

    def fail(self) -> None:
        self._transition(LifecycleState.ERROR)
