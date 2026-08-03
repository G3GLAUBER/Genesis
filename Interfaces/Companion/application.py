from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from Application.bootstrap import bootstrap_application
from Application.models import MissionApplicationExecution
from Application.services import (
    MemoryService,
    MissionApplicationService,
    WorkspaceApplicationService,
)
from Core.result import Result


if TYPE_CHECKING:
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
    memory_count: int = 0
    execution_count: int = 0
    application_health: str = "DEGRADADO"
    available_service_count: int = 0
    service_count: int = 3
    last_activity: datetime | None = None


@dataclass(frozen=True)
class CompanionActivity:
    kind: str
    title: str
    description: str
    occurred_at: datetime


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
        memory_service: MemoryService | None = None,
    ) -> None:
        workspace_service = (
            WorkspaceApplicationService(
                workspace_manager,
                active_workspace_id=active_workspace_id,
            )
            if workspace_manager is not None
            else WorkspaceApplicationService.default(
                active_workspace_id=active_workspace_id,
            )
        )
        self._workspace_service = workspace_service
        self._memory_service = memory_service
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
        application._memory_service = container.memory_service
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
        workspace_id = active.id if active is not None else None
        missions = self._mission_service.list_missions(
            workspace_id=workspace_id
        ).data
        executions = self._mission_service.list_executions(
            workspace_id=workspace_id
        ).data
        memories = self.list_memories(workspace_id=workspace_id)
        memory_records = memories.data if memories.is_success else ()
        activities = self.timeline(workspace_id=workspace_id)
        available_service_count = sum(
            service is not None
            for service in (
                self._workspace_service,
                self._mission_service,
                self._memory_service,
            )
        )
        service_count = 3
        return CompanionDashboard(
            active_workspace=active,
            workspace_count=len(workspaces),
            mission_count=len(missions),
            memory_count=len(memory_records),
            execution_count=len(executions),
            application_health=(
                "DISPONÍVEL"
                if available_service_count == service_count
                else "DEGRADADO"
            ),
            available_service_count=available_service_count,
            service_count=service_count,
            last_activity=(
                activities[0].occurred_at if activities else None
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

    def list_missions(self, *, workspace_id: str | None = None) -> Result:
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._mission_service.list_missions(workspace_id=selected_id)

    def list_executions(self, *, workspace_id: str | None = None) -> Result:
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._mission_service.list_executions(workspace_id=selected_id)

    def store_memory(
        self,
        *,
        category: str | None,
        title: str | None,
        content: str | None,
        workspace_id: str | None = None,
        mission_id: str | None = None,
    ) -> Result:
        if self._memory_service is None:
            return Result.error(message="MemoryService não está disponível")
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._memory_service.store(
            workspace_id=selected_id,
            mission_id=mission_id,
            category=category,
            title=title,
            content=content,
        )

    def list_memories(self, *, workspace_id: str | None = None) -> Result:
        if self._memory_service is None:
            return Result.error(message="MemoryService não está disponível")
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._memory_service.history(workspace_id=selected_id)

    def search_memories(
        self,
        *,
        text: str | None = "",
        category: str | None = None,
        workspace_id: str | None = None,
    ) -> Result:
        if self._memory_service is None:
            return Result.error(message="MemoryService não está disponível")
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._memory_service.search(
            workspace_id=selected_id,
            text=text,
            category=category,
        )

    def timeline(
        self,
        *,
        workspace_id: str | None = None,
    ) -> tuple[CompanionActivity, ...]:
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        executions_result = self._mission_service.list_executions(
            workspace_id=selected_id
        )
        executions = (
            executions_result.data if executions_result.is_success else ()
        )
        memories_result = self.list_memories(workspace_id=selected_id)
        memories = memories_result.data if memories_result.is_success else ()
        activities = []
        for execution in executions:
            activities.extend(
                (
                    CompanionActivity(
                        kind="mission",
                        title="Missão criada",
                        description=execution.mission.title,
                        occurred_at=execution.mission.created_at,
                    ),
                    CompanionActivity(
                        kind="plan",
                        title="Plano criado",
                        description=f"{len(execution.plan.steps)} etapas",
                        occurred_at=execution.plan.created_at,
                    ),
                    CompanionActivity(
                        kind="execution",
                        title="Execução concluída",
                        description=execution.report.status.value,
                        occurred_at=execution.report.completed_at,
                    ),
                )
            )
        activities.extend(
            CompanionActivity(
                kind="memory",
                title="Memória registrada",
                description=memory.title,
                occurred_at=memory.created_at,
            )
            for memory in memories
        )
        return tuple(
            sorted(
                activities,
                key=lambda activity: activity.occurred_at,
                reverse=True,
            )
        )
