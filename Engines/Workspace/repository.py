from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from Engines.Workspace.models import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    def store(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    def get(self, workspace_id: str) -> Workspace | None: ...

    @abstractmethod
    def list(self) -> tuple[Workspace, ...]: ...


class InMemoryWorkspaceRepository(WorkspaceRepository):
    def __init__(self) -> None:
        self._items: dict[str, Workspace] = {}
        self._lock = RLock()

    def store(self, workspace: Workspace) -> Workspace:
        with self._lock:
            self._items[workspace.id] = workspace
        return workspace

    def get(self, workspace_id: str) -> Workspace | None:
        with self._lock:
            return self._items.get(workspace_id)

    def list(self) -> tuple[Workspace, ...]:
        with self._lock:
            return tuple(self._items.values())

