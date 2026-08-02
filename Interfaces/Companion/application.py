from __future__ import annotations

from dataclasses import dataclass

from Core.registry import Registry
from Core.result import Result
from Engines.AI import AIOrchestrator, FakeProvider
from Engines.Execution import MissionExecutionEngine, MissionExecutionReport
from Engines.Mission import Mission, MissionEngine
from Engines.Planning import Plan, PlanStep, Planner


@dataclass(frozen=True)
class CompanionExecution:
    mission: Mission
    plan: Plan
    report: MissionExecutionReport
    provider_id: str


class CompanionApplication:
    def __init__(
        self,
        mission_engine: MissionEngine,
        planner: Planner,
        execution_engine: MissionExecutionEngine,
        *,
        provider_id: str,
    ) -> None:
        self._mission_engine = mission_engine
        self._planner = planner
        self._execution_engine = execution_engine
        self._provider_id = provider_id

    @classmethod
    def default(cls) -> CompanionApplication:
        registry = Registry()
        provider = FakeProvider()
        registry.register(provider.provider_id, provider)
        orchestrator = AIOrchestrator(
            registry,
            provider_ids=(provider.provider_id,),
        )
        return cls(
            mission_engine=MissionEngine(),
            planner=Planner(),
            execution_engine=MissionExecutionEngine(orchestrator),
            provider_id=provider.provider_id,
        )

    def execute_mission(
        self,
        *,
        title: str | None,
        objective: str | None,
    ) -> Result:
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

        return Result.success(
            message="Missão criada e executada pelo Genesis Companion",
            data=CompanionExecution(
                mission=mission,
                plan=plan,
                report=execution_result.data,
                provider_id=self._provider_id,
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
