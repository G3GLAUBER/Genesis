from __future__ import annotations

from Core.result import Result
from Engines.Workspace import WorkspaceManager, WorkspaceStatus


class WorkspaceApplicationService:
    def __init__(
        self,
        manager: WorkspaceManager,
        *,
        active_workspace_id: str | None = None,
    ) -> None:
        self._manager = manager
        self._active_workspace_id = active_workspace_id

    @property
    def active_workspace_id(self) -> str | None:
        return self._active_workspace_id

    def create(
        self,
        *,
        name: str | None,
        description: str | None = "",
    ) -> Result:
        result = self._manager.create(name=name, description=description)
        if result.is_success:
            self._active_workspace_id = result.data.id
        return result

    def list(self, *, include_archived: bool = False) -> Result:
        return self._manager.list(include_archived=include_archived)

    def get(self, workspace_id: str | None) -> Result:
        return self._manager.get(workspace_id)

    def archive(self, workspace_id: str | None) -> Result:
        result = self._manager.delete(workspace_id)
        if result.is_success and result.data.id == self._active_workspace_id:
            self._active_workspace_id = None
        return result

    def restore(self, workspace_id: str | None) -> Result:
        return self._manager.restore(workspace_id)

    def set_active(self, workspace_id: str | None) -> Result:
        result = self._manager.get(workspace_id)
        if not result.is_success:
            return result
        if result.data.status is not WorkspaceStatus.ACTIVE:
            return Result.error(message="Workspace arquivado não pode ser ativo")
        self._active_workspace_id = result.data.id
        return Result.success(message="Workspace ativo definido", data=result.data)

    def get_active(self) -> Result:
        return self._manager.get(self._active_workspace_id)

    def associate_mission(
        self,
        workspace_id: str | None,
        *,
        mission_id: str | None,
    ) -> Result:
        return self._manager.add_mission(
            workspace_id,
            mission_id=mission_id,
        )
