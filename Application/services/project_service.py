from __future__ import annotations

from Core.result import Result
from Engines.Projects import ProjectEngine
from Application.services.workspace_service import WorkspaceApplicationService


class ProjectService:
    def __init__(
        self,
        engine: ProjectEngine,
        *,
        workspace_service: WorkspaceApplicationService | None = None,
    ) -> None:
        self._engine = engine
        self._workspace_service = workspace_service

    def create(
        self,
        *,
        workspace_id: str | None,
        title: str | None,
        client: str | None,
        address: str | None,
        description: str | None = "",
    ) -> Result:
        if self._workspace_service is not None:
            workspace = self._workspace_service.get(workspace_id)
            if not workspace.is_success:
                return workspace
        return self._engine.create(
            workspace_id=workspace_id,
            title=title,
            client=client,
            address=address,
            description=description,
        )

    def list(
        self,
        *,
        workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> Result:
        return self._engine.list(
            workspace_id=workspace_id,
            include_archived=include_archived,
        )

    def get(self, project_id: str | None) -> Result:
        return self._engine.get(project_id)

    def archive(self, project_id: str | None) -> Result:
        return self._engine.archive(project_id)

    def restore(self, project_id: str | None) -> Result:
        return self._engine.restore(project_id)

    def attach_mission(
        self,
        project_id: str | None,
        *,
        mission_id: str | None,
    ) -> Result:
        return self._engine.attach_mission(
            project_id,
            mission_id=mission_id,
        )
