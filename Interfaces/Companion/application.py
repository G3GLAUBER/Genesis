from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from Application.bootstrap import bootstrap_application
from Application.models import MissionApplicationExecution
from Application.services import (
    IntelligenceApplicationService,
    MemoryService,
    MissionApplicationService,
    ProjectService,
    WorkspaceApplicationService,
)
from Core.result import Result


if TYPE_CHECKING:
    from Engines.Execution import MissionExecutionEngine
    from Engines.Mission import MissionEngine
    from Engines.Planning import Planner
    from Engines.Projects import Project
    from Engines.Workspace import Workspace, WorkspaceManager
    from Engines.Intelligence import RoutingMode


CompanionExecution = MissionApplicationExecution


@dataclass(frozen=True)
class CompanionDashboard:
    active_workspace: Workspace | None
    workspace_count: int
    mission_count: int
    memory_count: int = 0
    execution_count: int = 0
    active_project_count: int = 0
    completed_project_count: int = 0
    recent_projects: tuple[Project, ...] = ()
    application_health: str = "DEGRADADO"
    available_service_count: int = 0
    service_count: int = 3
    last_activity: datetime | None = None
    storage_label: str = "Memória local"


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
        project_service: ProjectService | None = None,
        intelligence_service: IntelligenceApplicationService | None = None,
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
        self._project_service = project_service
        self._intelligence_service = intelligence_service
        self._persistence_mode = "memory"
        self._mission_service = MissionApplicationService(
            mission_engine,
            planner,
            execution_engine,
            provider_id=provider_id,
            workspace_service=workspace_service,
        )

    @classmethod
    def default(
        cls,
        *,
        persistent: bool = False,
        database_path: str | Path | None = None,
    ) -> CompanionApplication:
        container = bootstrap_application(
            persistent=persistent,
            database_path=database_path,
        )
        application = cls.__new__(cls)
        application._mission_service = container.mission_service
        application._workspace_service = container.workspace_service
        application._memory_service = container.memory_service
        application._project_service = container.project_service
        application._intelligence_service = container.intelligence_service
        application._persistence_mode = container.persistence_mode
        return application

    def list_provider_profiles(self) -> Result:
        if self._intelligence_service is None:
            return Result.error(
                message="IntelligenceApplicationService não está disponível"
            )
        return self._intelligence_service.list_provider_profiles()

    def route_intelligence(
        self,
        *,
        prompt: str | None,
        capability: str | None = "general_assistance",
        mode: RoutingMode,
    ) -> Result:
        if self._intelligence_service is None:
            return Result.error(
                message="IntelligenceApplicationService não está disponível"
            )
        return self._intelligence_service.route(
            prompt=prompt,
            capability=capability,
            mode=mode,
        )

    def create_manual_handoff(
        self,
        *,
        provider_id: str | None,
        prompt: str | None,
        workspace_id: str | None = None,
        project_id: str | None = None,
    ) -> Result:
        if self._intelligence_service is None:
            return Result.error(
                message="IntelligenceApplicationService não está disponível"
            )
        selected_workspace = (
            workspace_id or self._workspace_service.active_workspace_id
        )
        return self._intelligence_service.create_manual_handoff(
            provider_id=provider_id,
            prompt=prompt,
            workspace_id=selected_workspace,
            project_id=project_id,
        )

    def complete_manual_handoff(
        self,
        handoff_id: str | None,
        *,
        response: str | None,
        save_as_memory: bool = False,
    ) -> Result:
        if self._intelligence_service is None:
            return Result.error(
                message="IntelligenceApplicationService não está disponível"
            )
        return self._intelligence_service.complete_manual_handoff(
            handoff_id,
            response=response,
            save_as_memory=save_as_memory,
        )

    def list_manual_handoffs(self) -> Result:
        if self._intelligence_service is None:
            return Result.error(
                message="IntelligenceApplicationService não está disponível"
            )
        return self._intelligence_service.list_manual_handoffs()

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
        projects = self.list_projects(workspace_id=workspace_id)
        project_records = projects.data if projects.is_success else ()
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
            active_project_count=sum(
                project.status.value in ("planning", "active", "on_hold")
                for project in project_records
            ),
            completed_project_count=sum(
                project.status.value == "completed"
                for project in project_records
            ),
            recent_projects=tuple(reversed(project_records))[:3],
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
            storage_label=(
                "SQLite local" if self._persistence_mode == "sqlite"
                else "Memória local"
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

    def create_project(
        self,
        *,
        title: str | None,
        client: str | None,
        address: str | None,
        description: str | None = "",
        workspace_id: str | None = None,
    ) -> Result:
        if self._project_service is None:
            return Result.error(message="ProjectService não está disponível")
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._project_service.create(
            workspace_id=selected_id,
            title=title,
            client=client,
            address=address,
            description=description,
        )

    def list_projects(
        self,
        *,
        workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> Result:
        if self._project_service is None:
            return Result.error(message="ProjectService não está disponível")
        selected_id = workspace_id or self._workspace_service.active_workspace_id
        return self._project_service.list(
            workspace_id=selected_id,
            include_archived=include_archived,
        )

    def get_project(self, project_id: str | None) -> Result:
        if self._project_service is None:
            return Result.error(message="ProjectService não está disponível")
        return self._project_service.get(project_id)

    def archive_project(self, project_id: str | None) -> Result:
        if self._project_service is None:
            return Result.error(message="ProjectService não está disponível")
        return self._project_service.archive(project_id)

    def restore_project(self, project_id: str | None) -> Result:
        if self._project_service is None:
            return Result.error(message="ProjectService não está disponível")
        return self._project_service.restore(project_id)

    def attach_project_mission(
        self,
        project_id: str | None,
        *,
        mission_id: str | None,
    ) -> Result:
        if self._project_service is None:
            return Result.error(message="ProjectService não está disponível")
        return self._project_service.attach_mission(
            project_id,
            mission_id=mission_id,
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
