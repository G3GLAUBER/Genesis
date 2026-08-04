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
    RemodelingApplicationService,
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
class CompanionPriority:
    rank: int
    kind: str
    level: str
    title: str
    reason: str
    action_label: str
    href: str


@dataclass(frozen=True)
class CompanionOnboardingStep:
    title: str
    description: str
    complete: bool
    href: str


@dataclass(frozen=True)
class CompanionCommandCenter:
    greeting: str
    priorities: tuple[CompanionPriority, ...]
    onboarding_steps: tuple[CompanionOnboardingStep, ...]
    show_onboarding: bool
    primary_action_label: str
    primary_action_href: str
    intelligence_state: str
    intelligence_description: str


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
    command_center: CompanionCommandCenter | None = None


@dataclass(frozen=True)
class CompanionActivity:
    kind: str
    title: str
    description: str
    occurred_at: datetime


def greeting_for_hour(hour: int) -> str:
    """Return the calm, locale-neutral greeting used by the Command Center."""
    if 5 <= hour < 12:
        return "Bom dia."
    if 12 <= hour < 19:
        return "Boa tarde."
    return "Boa noite."


def _compose_command_center(
    *,
    active_workspace,
    missions,
    executions,
    memories,
    projects,
    handoffs,
    proposals,
    application_health: str,
    intelligence_available: bool,
) -> CompanionCommandCenter:
    pending_handoffs = tuple(
        item
        for item in handoffs
        if getattr(getattr(item, "status", None), "value", None) == "pending"
    )
    pending_proposals = tuple(
        item
        for item in proposals
        if getattr(getattr(item, "status", None), "value", None)
        in ("generated", "reviewed", "approved")
    )
    executed_mission_ids = {
        item.mission.id for item in executions if getattr(item, "mission", None)
    }
    pending_missions = tuple(
        item for item in missions if item.id not in executed_mission_ids
    )
    inactive_projects = tuple(
        item
        for item in projects
        if getattr(getattr(item, "status", None), "value", None)
        in ("planning", "active", "on_hold")
        and not getattr(item, "mission_ids", ())
    )
    unassociated_memories = tuple(
        item
        for item in memories
        if getattr(item, "mission_id", None) is None
        and not getattr(item, "metadata", {}).get("project_id")
    )
    priorities: list[CompanionPriority] = []

    def add_priority(
        rank: int,
        kind: str,
        level: str,
        title: str,
        reason: str,
        action_label: str,
        href: str,
    ) -> None:
        priorities.append(
            CompanionPriority(
                rank, kind, level, title, reason, action_label, href
            )
        )

    if application_health == "DEGRADADO":
        add_priority(
            1,
            "health",
            "high",
            "Alguns serviços precisam de atenção.",
            "A experiência pode estar parcialmente indisponível.",
            "Ver Application Health",
            "/doctor",
        )
    if pending_handoffs:
        add_priority(
            2,
            "handoff",
            "high",
            "Há um handoff aguardando resposta.",
            "O Genesis precisa da sua resposta para manter a decisão em movimento.",
            "Revisar handoff",
            "/intelligence",
        )
    if pending_proposals:
        add_priority(
            3,
            "proposal",
            "medium",
            "Há uma proposta aguardando sua revisão.",
            "Nada será aplicado sem a sua aprovação.",
            "Revisar proposta",
            "/remodeling",
        )
    if pending_missions:
        add_priority(
            4,
            "mission",
            "medium",
            "Há uma missão pendente.",
            "Retome o objetivo para preservar a continuidade.",
            "Ver missões",
            "/missions",
        )
    if inactive_projects:
        project = inactive_projects[0]
        add_priority(
            5,
            "project",
            "medium",
            "Este projeto ainda não tem atividade.",
            f'“{project.title}” precisa de uma primeira missão.',
            "Abrir projetos",
            "/projects",
        )
    if unassociated_memories:
        add_priority(
            6,
            "memory",
            "low",
            "Há uma memória sem associação.",
            "Associe contexto para encontrá-la no momento certo.",
            "Organizar Memory",
            "/memory",
        )

    show_onboarding = not projects and not missions and not memories
    if show_onboarding:
        add_priority(
            7,
            "onboarding",
            "low",
            "Defina o primeiro contexto de trabalho.",
            "Comece por um projeto para o Genesis orientar os próximos passos.",
            "Criar primeiro projeto",
            "/projects#new-project",
        )
    if not priorities:
        add_priority(
            8,
            "healthy",
            "healthy",
            "Você está em dia.",
            "Não há decisões ou ações pendentes neste momento.",
            "Abrir Intelligence",
            "/intelligence",
        )

    ordered_priorities = tuple(
        sorted(priorities, key=lambda item: (item.rank, item.kind))[:3]
    )
    onboarding_steps = (
        CompanionOnboardingStep(
            "Crie um Workspace.",
            "Dê um contexto claro ao seu trabalho.",
            active_workspace is not None,
            "/workspaces",
        ),
        CompanionOnboardingStep(
            "Crie um Projeto.",
            "Transforme uma intenção em progresso acompanhável.",
            bool(projects),
            "/projects#new-project",
        ),
        CompanionOnboardingStep(
            "Registre sua primeira missão ou memória.",
            "Comece a construir continuidade.",
            bool(missions or memories),
            "/missions#new-mission",
        ),
    )
    if active_workspace is None:
        primary_action_label = "Criar Workspace"
        primary_action_href = "/workspaces"
    elif not projects:
        primary_action_label = "Criar primeiro projeto"
        primary_action_href = "/projects#new-project"
    elif not missions and not memories:
        primary_action_label = "Criar primeira missão"
        primary_action_href = "/missions#new-mission"
    else:
        primary_action_label = ordered_priorities[0].action_label
        primary_action_href = ordered_priorities[0].href

    if not intelligence_available:
        intelligence_state = "Serviço indisponível"
        intelligence_description = (
            "Intelligence não está disponível nesta composição local."
        )
    elif pending_handoffs:
        intelligence_state = "Handoff aguardando resposta"
        intelligence_description = (
            "Há uma decisão que depende da sua revisão antes de continuar."
        )
    elif pending_proposals:
        intelligence_state = "Recomendação disponível"
        intelligence_description = (
            "Revise o contexto e as alternativas antes de decidir."
        )
    else:
        intelligence_state = "Modo Free First ativo"
        intelligence_description = (
            "Nenhuma decisão pendente. O Genesis prioriza recursos gratuitos."
        )

    return CompanionCommandCenter(
        greeting=greeting_for_hour(datetime.now().astimezone().hour),
        priorities=ordered_priorities,
        onboarding_steps=onboarding_steps,
        show_onboarding=show_onboarding,
        primary_action_label=primary_action_label,
        primary_action_href=primary_action_href,
        intelligence_state=intelligence_state,
        intelligence_description=intelligence_description,
    )


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
        remodeling_service: RemodelingApplicationService | None = None,
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
        self._remodeling_service = remodeling_service
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
        application._remodeling_service = container.remodeling_service
        application._persistence_mode = container.persistence_mode
        return application

    def create_remodeling_brief(self, **values) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        return self._remodeling_service.create_brief(**values)

    def request_remodeling_proposal(self, brief_id: str | None) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        return self._remodeling_service.request_proposal(brief_id)

    def complete_remodeling_handoff(
        self, handoff_id: str | None, *, response: str | None
    ) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        completed = self._remodeling_service.complete_handoff(
            handoff_id, response=response
        )
        if not completed.is_success:
            return completed
        return self._remodeling_service.build_proposal(handoff_id)

    def get_remodeling_proposal(self, proposal_id: str | None) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        return self._remodeling_service.get_proposal(proposal_id)

    def list_remodeling_briefs(self) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        return self._remodeling_service.list_briefs()

    def list_remodeling_proposals(self) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        return self._remodeling_service.list_proposals()

    def review_remodeling_proposal(self, proposal_id: str | None) -> Result:
        return self._remodeling_action("review_proposal", proposal_id)

    def approve_remodeling_proposal(self, proposal_id: str | None) -> Result:
        return self._remodeling_action("approve_proposal", proposal_id)

    def reject_remodeling_proposal(self, proposal_id: str | None) -> Result:
        return self._remodeling_action("reject_proposal", proposal_id)

    def apply_remodeling_proposal(self, proposal_id: str | None) -> Result:
        return self._remodeling_action("apply_proposal", proposal_id)

    def _remodeling_action(self, method: str, proposal_id: str | None) -> Result:
        if self._remodeling_service is None:
            return Result.error(
                message="RemodelingApplicationService não está disponível"
            )
        return getattr(self._remodeling_service, method)(proposal_id)

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
        handoffs_result = self.list_manual_handoffs()
        handoffs = (
            handoffs_result.data if handoffs_result.is_success else ()
        )
        proposals_result = self.list_remodeling_proposals()
        proposals = (
            proposals_result.data if proposals_result.is_success else ()
        )
        available_service_count = sum(
            service is not None
            for service in (
                self._workspace_service,
                self._mission_service,
                self._memory_service,
            )
        )
        service_count = 3
        application_health = (
            "DISPONÍVEL"
            if available_service_count == service_count
            else "DEGRADADO"
        )
        command_center = _compose_command_center(
            active_workspace=active,
            missions=missions,
            executions=executions,
            memories=memory_records,
            projects=project_records,
            handoffs=handoffs,
            proposals=proposals,
            application_health=application_health,
            intelligence_available=self._intelligence_service is not None,
        )
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
            application_health=application_health,
            available_service_count=available_service_count,
            service_count=service_count,
            last_activity=(
                activities[0].occurred_at if activities else None
            ),
            storage_label=(
                "SQLite local" if self._persistence_mode == "sqlite"
                else "Memória local"
            ),
            command_center=command_center,
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
