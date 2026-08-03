from __future__ import annotations

from collections.abc import Iterable

from Application.models import MissionApplicationExecution
from Application.services.workspace_service import WorkspaceApplicationService
from Core.result import Result
from Engines.Execution import MissionExecutionEngine
from Engines.Mission import Mission, MissionEngine
from Engines.Planning import Plan, PlanStep, Planner


class MissionApplicationService:
    def __init__(
        self,
        mission_engine: MissionEngine,
        planner: Planner,
        execution_engine: MissionExecutionEngine,
        *,
        provider_id: str,
        workspace_service: WorkspaceApplicationService | None = None,
    ) -> None:
        self._mission_engine = mission_engine
        self._planner = planner
        self._execution_engine = execution_engine
        self._provider_id = provider_id
        self._workspace_service = workspace_service

    def create_mission(
        self,
        *,
        title: str | None,
        objective: str | None,
        source: str = "Companion",
        constraints: Iterable[str] | str | None = (),
        success_criteria: Iterable[str] | str | None = (),
    ) -> Result:
        return self._mission_engine.create(
            title=title,
            objective=objective,
            source=source,
            constraints=constraints,
            success_criteria=success_criteria,
        )

    def create_demonstration_plan(self, mission: Mission) -> Result:
        return self._planner.create_plan(
            mission=mission,
            steps=self._demonstration_steps(),
        )

    def execute(self, *, mission: Mission, plan: Plan) -> Result:
        return self._execution_engine.execute(mission=mission, plan=plan)

    def execute_mission(
        self,
        *,
        title: str | None,
        objective: str | None,
        workspace_id: str | None = None,
    ) -> Result:
        selected_id = workspace_id
        if selected_id is None and self._workspace_service is not None:
            selected_id = self._workspace_service.active_workspace_id
        if selected_id is not None:
            if self._workspace_service is None:
                return Result.error(message="Workspace não está disponível")
            workspace_result = self._workspace_service.get(selected_id)
            if not workspace_result.is_success:
                return workspace_result

        mission_result = self.create_mission(
            title=title,
            objective=objective,
        )
        if not mission_result.is_success:
            return mission_result

        mission = mission_result.data
        plan_result = self.create_demonstration_plan(mission)
        if not plan_result.is_success:
            return plan_result

        plan = plan_result.data
        execution_result = self.execute(mission=mission, plan=plan)
        if not execution_result.is_success:
            return execution_result

        workspace = None
        if selected_id is not None:
            association = self._workspace_service.associate_mission(
                selected_id,
                mission_id=mission.id,
            )
            if not association.is_success:
                return association
            workspace = association.data

        return Result.success(
            message="Missão criada e executada pelo Genesis Companion",
            data=MissionApplicationExecution(
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
