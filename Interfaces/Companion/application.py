from __future__ import annotations

from dataclasses import dataclass

from Application.bootstrap import bootstrap_application
from Application.models import MissionApplicationExecution
from Application.services import (
    MissionApplicationService,
    WorkspaceApplicationService,
)
from Core.result import Result
from Engines.Execution import MissionExecutionEngine
from Engines.Mission import MissionEngine
from Engines.Planning import Planner
from Engines.Workspace import Workspace, WorkspaceManager


CompanionExecution = MissionApplicationExecution


@dataclass(frozen=True)
class CompanionDashboard:
    active_workspace: Workspace | None
    workspace_count: int
    mission_count: int


class CompanionApplication:
    def __init__(
        self,
        mission_engine: MissionEngine,
        planner: Planner,
        execution_engine: MissionExecutionEngine,
        *,
        provider_id: str,
        workspace_manager: WorkspaceManager | None = None,
        active_workspace_id: str | None = None,
    ) -> None:
        workspace_service = WorkspaceApplicationService(
            workspace_manager or WorkspaceManager(),
            active_workspace_id=active_workspace_id,
        )
        self._workspace_service = workspace_service
        self._mission_service = MissionApplicationService(
            mission_engine,
            planner,
            execution_engine,
            provider_id=provider_id,
            workspace_service=workspace_service,
        )

    @classmethod
    def default(cls) -> CompanionApplication:
        container = bootstrap_application()
        application = cls.__new__(cls)
        application._mission_service = container.mission_service
        application._workspace_service = container.workspace_service
        return application

    def create_workspace(
        self,
        *,
        name: str | None,
        description: str | None = "",
    ) -> Result:
        return self._workspace_service.create(
            name=name, description=description
        )

    def get_workspace(self, workspace_id: str | None) -> Result:
        return self._workspace_service.get(workspace_id)

    def list_workspaces(self, *, include_archived: bool = False) -> Result:
        return self._workspace_service.list(
            include_archived=include_archived
        )

    def open_workspace(self, workspace_id: str | None) -> Result:
        return self._workspace_service.set_active(workspace_id)

    def dashboard(self) -> CompanionDashboard:
        workspaces = self._workspace_service.list().data
        active_result = self._workspace_service.get_active()
        active = active_result.data if active_result.is_success else None
        return CompanionDashboard(
            active_workspace=active,
            workspace_count=len(workspaces),
            mission_count=sum(
                len(workspace.mission_ids) for workspace in workspaces
            ),
        )

    def execute_mission(
        self,
        *,
        title: str | None,
        objective: str | None,
        workspace_id: str | None = None,
    ) -> Result:
        return self._mission_service.execute_mission(
            title=title,
            objective=objective,
            workspace_id=workspace_id,
        )
