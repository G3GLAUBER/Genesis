from __future__ import annotations

from dataclasses import dataclass

from Core.registry import Registry
from Core.result import Result
from Engines.AI import AIOrchestrator, FakeProvider
from Engines.Execution import MissionExecutionEngine, MissionExecutionReport
from Engines.Mission import Mission, MissionEngine
from Engines.Planning import Plan, PlanStep, Planner
from Engines.Workspace import Workspace, WorkspaceManager


@dataclass(frozen=True)
class CompanionExecution:
    mission: Mission
    plan: Plan
    report: MissionExecutionReport
    provider_id: str
    workspace: Workspace | None = None


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
        self._mission_engine = mission_engine
        self._planner = planner
        self._execution_engine = execution_engine
        self._provider_id = provider_id
        self._workspace_manager = workspace_manager or WorkspaceManager()
        self._active_workspace_id = active_workspace_id

    @classmethod
    def default(cls) -> CompanionApplication:
        registry = Registry()
        provider = FakeProvider()
        registry.register(provider.provider_id, provider)
        orchestrator = AIOrchestrator(
            registry,
            provider_ids=(provider.provider_id,),
        )
        workspace_manager = WorkspaceManager()
        workspace_result = workspace_manager.create(
            name="Workspace principal",
            description="Workspace inicial do Genesis Companion",
        )
        return cls(
            mission_engine=MissionEngine(),
            planner=Planner(),
            execution_engine=MissionExecutionEngine(orchestrator),
            provider_id=provider.provider_id,
            workspace_manager=workspace_manager,
            active_workspace_id=workspace_result.data.id,
        )

    def create_workspace(
        self,
        *,
        name: str | None,
        description: str | None = "",
    ) -> Result:
        result = self._workspace_manager.create(
            name=name,
            description=description,
        )
        if result.is_success:
            self._active_workspace_id = result.data.id
        return result

    def get_workspace(self, workspace_id: str | None) -> Result:
        return self._workspace_manager.get(workspace_id)

    def list_workspaces(self, *, include_archived: bool = False) -> Result:
        return self._workspace_manager.list(include_archived=include_archived)

    def open_workspace(self, workspace_id: str | None) -> Result:
        result = self._workspace_manager.get(workspace_id)
        if result.is_success:
            self._active_workspace_id = result.data.id
        return result

    def dashboard(self) -> CompanionDashboard:
        workspaces = self._workspace_manager.list().data
        active_result = self._workspace_manager.get(self._active_workspace_id)
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
        selected_id = workspace_id or self._active_workspace_id
        if selected_id is not None:
            workspace_result = self._workspace_manager.get(selected_id)
            if not workspace_result.is_success:
                return workspace_result

        mission_result = self._mission_engine.create(
            title=title,
            objective=objective,
            source="Companion",
        )
        if not mission_result.is_success:
            return mission_result

        mission = mission_result.data
        plan_result = self._planner.create_plan(
            mission=mission,
            steps=self._demonstration_steps(),
        )
        if not plan_result.is_success:
            return plan_result

        plan = plan_result.data
        execution_result = self._execution_engine.execute(
            mission=mission,
            plan=plan,
        )
        if not execution_result.is_success:
            return execution_result

        workspace = None
        if selected_id is not None:
            association_result = self._workspace_manager.add_mission(
                selected_id,
                mission_id=mission.id,
            )
            if not association_result.is_success:
                return association_result
            workspace = association_result.data

        return Result.success(
            message="Missão criada e executada pelo Genesis Companion",
            data=CompanionExecution(
                mission=mission,
                plan=plan,
                report=execution_result.data,
                provider_id=self._provider_id,
                workspace=workspace,
            ),
        )

    @staticmethod
    def _demonstration_steps() -> tuple[PlanStep, ...]:
        understand = PlanStep.create(
            title="Compreender o objetivo",
            description="Analise o objetivo da missão e destaque seu foco.",
            order=1,
            capability="text_generation",
        )
        propose = PlanStep.create(
            title="Propor a primeira ação",
            description="Sugira uma primeira ação concreta para a missão.",
            order=2,
            dependencies=(understand.id,),
            capability="text_generation",
        )
        review = PlanStep.create(
            title="Revisar o plano de ação",
            description="Revise as etapas e apresente uma conclusão objetiva.",
            order=3,
            dependencies=(propose.id,),
            capability="text_generation",
        )
        return understand, propose, review
