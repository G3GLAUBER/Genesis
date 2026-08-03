from __future__ import annotations

from threading import RLock

from Core.result import Result
from Engines.Workspace.engine import WorkspaceEngine
from Engines.Workspace.models import Workspace, WorkspaceStatus


class WorkspaceManager:
    def __init__(self, engine: WorkspaceEngine | None = None) -> None:
        self._engine = engine or WorkspaceEngine()
        self._workspaces: dict[str, Workspace] = {}
        self._lock = RLock()

    def create(
        self,
        *,
        name: str | None = None,
        description: str | None = "",
    ) -> Result:
        with self._lock:
            result = self._engine.create(
                name=name,
                description=description,
            )
            if not result.is_success:
                return result
            if self._name_exists(result.data.name):
                return Result.error(message="Workspace com este nome já existe")
            self._workspaces[result.data.id] = result.data
            return result

    def get(self, workspace_id: str | None) -> Result:
        with self._lock:
            workspace = self._workspaces.get(workspace_id or "")
            if workspace is None:
                return Result.error(message="Workspace não encontrado")
            return Result.success(message="Workspace encontrado", data=workspace)

    def list(self, *, include_archived: bool = False) -> Result:
        with self._lock:
            workspaces = tuple(
                workspace
                for workspace in self._workspaces.values()
                if include_archived
                or workspace.status is WorkspaceStatus.ACTIVE
            )
            return Result.success(
                message="Workspaces listados",
                data=workspaces,
            )

    def delete(self, workspace_id: str | None) -> Result:
        return self._update(workspace_id, self._engine.archive)

    def restore(self, workspace_id: str | None) -> Result:
        return self._update(workspace_id, self._engine.restore)

    def rename(self, workspace_id: str | None, *, name: str | None) -> Result:
        with self._lock:
            current = self.get(workspace_id)
            if not current.is_success:
                return current
            normalized_name = name.strip() if isinstance(name, str) else name
            if self._name_exists(normalized_name, exclude_id=current.data.id):
                return Result.error(message="Workspace com este nome já existe")
            result = self._engine.rename(workspace=current.data, name=name)
            return self._store_result(result)

    def add_mission(
        self,
        workspace_id: str | None,
        *,
        mission_id: str | None,
    ) -> Result:
        return self._update(
            workspace_id,
            self._engine.add_mission,
            mission_id=mission_id,
        )

    def remove_mission(
        self,
        workspace_id: str | None,
        *,
        mission_id: str | None,
    ) -> Result:
        return self._update(
            workspace_id,
            self._engine.remove_mission,
            mission_id=mission_id,
        )

    def search(
        self,
        name: str | None,
        *,
        include_archived: bool = False,
    ) -> Result:
        if not isinstance(name, str) or not name.strip():
            return Result.error(message="Busca deve ser um texto não vazio")
        query = name.strip().casefold()
        listed = self.list(include_archived=include_archived)
        matches = tuple(
            workspace
            for workspace in listed.data
            if query in workspace.name.casefold()
        )
        return Result.success(message="Busca concluída", data=matches)

    def _update(self, workspace_id, operation, **kwargs) -> Result:
        with self._lock:
            current = self.get(workspace_id)
            if not current.is_success:
                return current
            result = operation(workspace=current.data, **kwargs)
            return self._store_result(result)

    def _store_result(self, result: Result) -> Result:
        if result.is_success:
            self._workspaces[result.data.id] = result.data
        return result

    def _name_exists(
        self,
        name: object,
        *,
        exclude_id: str | None = None,
    ) -> bool:
        if not isinstance(name, str):
            return False
        normalized = name.casefold()
        return any(
            workspace.id != exclude_id
            and workspace.name.casefold() == normalized
            for workspace in self._workspaces.values()
        )
