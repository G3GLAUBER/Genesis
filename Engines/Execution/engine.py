from __future__ import annotations

from datetime import datetime, timezone

from Core.result import Result
from Engines.AI import AIOrchestrator, AIRequest, AIResponse
from Engines.Execution.models import (
    ExecutionStatus,
    MissionExecutionFailure,
    MissionExecutionReport,
    StepExecutionResult,
)
from Engines.Mission import Mission
from Engines.Planning import Plan, PlanStep


class MissionExecutionEngine:
    def __init__(self, ai_orchestrator: AIOrchestrator) -> None:
        self._ai_orchestrator = ai_orchestrator

    def execute(self, *, mission: Mission, plan: Plan) -> Result:
        validation_error = self._validate_inputs(mission, plan)
        if validation_error is not None:
            return Result.error(
                message=validation_error.message,
                data=validation_error,
            )

        started_at = self._now()
        ordered_steps = tuple(sorted(plan.steps, key=lambda step: step.order))
        step_results: list[StepExecutionResult] = []
        completed_steps: set[str] = set()

        for index, step in enumerate(ordered_steps):
            step_result = self._execute_step(step, completed_steps)
            step_results.append(step_result)

            if step_result.status is ExecutionStatus.COMPLETED:
                completed_steps.add(step.id)
                continue

            step_results.extend(
                self._skip_steps(ordered_steps[index + 1 :])
            )
            report = self._build_report(
                mission=mission,
                plan=plan,
                status=ExecutionStatus.FAILED,
                step_results=step_results,
                started_at=started_at,
            )
            return Result.error(
                message=f"Execução da missão falhou na etapa: {step.id}",
                data=report,
            )

        report = self._build_report(
            mission=mission,
            plan=plan,
            status=ExecutionStatus.COMPLETED,
            step_results=step_results,
            started_at=started_at,
        )
        return Result.success(
            message="Missão executada com sucesso",
            data=report,
        )

    def _execute_step(
        self,
        step: PlanStep,
        completed_steps: set[str],
    ) -> StepExecutionResult:
        started_at = self._now()

        if not step.capability:
            return self._failed_step(
                step=step,
                error="Etapa sem capability",
                started_at=started_at,
            )

        incomplete = tuple(
            dependency
            for dependency in step.dependencies
            if dependency not in completed_steps
        )
        if incomplete:
            return self._failed_step(
                step=step,
                error=(
                    "Dependências não concluídas: "
                    + ", ".join(incomplete)
                ),
                started_at=started_at,
            )

        request = AIRequest(
            prompt=self._build_prompt(step),
            capability=step.capability,
        )

        try:
            result = self._ai_orchestrator.generate(request)
        except Exception as error:
            return self._failed_step(
                step=step,
                error=(
                    "Falha inesperada do AIOrchestrator: "
                    f"{type(error).__name__}"
                ),
                started_at=started_at,
            )

        if not isinstance(result, Result):
            return self._failed_step(
                step=step,
                error="AIOrchestrator retornou resultado inválido",
                started_at=started_at,
            )
        if not result.is_success:
            return self._failed_step(
                step=step,
                error=result.message,
                started_at=started_at,
            )
        if not self._is_valid_response(result.data, request):
            return self._failed_step(
                step=step,
                error="AIOrchestrator retornou AIResponse inválida",
                started_at=started_at,
            )

        response = result.data
        return StepExecutionResult(
            step_id=step.id,
            status=ExecutionStatus.COMPLETED,
            provider_id=response.provider_id,
            content=response.content,
            error=None,
            started_at=started_at,
            completed_at=self._now(),
        )

    @staticmethod
    def _validate_inputs(
        mission: object,
        plan: object,
    ) -> MissionExecutionFailure | None:
        if not isinstance(mission, Mission):
            return MissionExecutionFailure(
                code="invalid_mission",
                message="Mission inválida",
            )
        if not isinstance(plan, Plan):
            return MissionExecutionFailure(
                code="invalid_plan",
                message="Plan inválido",
                mission_id=mission.id,
            )
        if plan.mission_id != mission.id:
            return MissionExecutionFailure(
                code="mission_plan_mismatch",
                message="Plan não pertence à Mission informada",
                mission_id=mission.id,
                plan_id=plan.id,
            )
        if not plan.steps:
            return MissionExecutionFailure(
                code="empty_plan",
                message="Plan não possui etapas",
                mission_id=mission.id,
                plan_id=plan.id,
            )
        if any(not isinstance(step, PlanStep) for step in plan.steps):
            return MissionExecutionFailure(
                code="invalid_plan",
                message="Plan contém etapa inválida",
                mission_id=mission.id,
                plan_id=plan.id,
            )
        return None

    @staticmethod
    def _build_prompt(step: PlanStep) -> str:
        return f"{step.title}\n\n{step.description}"

    @staticmethod
    def _is_valid_response(response: object, request: AIRequest) -> bool:
        return (
            isinstance(response, AIResponse)
            and isinstance(response.provider_id, str)
            and bool(response.provider_id.strip())
            and isinstance(response.content, str)
            and response.capability == request.capability
        )

    @classmethod
    def _failed_step(
        cls,
        *,
        step: PlanStep,
        error: str,
        started_at: datetime,
    ) -> StepExecutionResult:
        return StepExecutionResult(
            step_id=step.id,
            status=ExecutionStatus.FAILED,
            provider_id=None,
            content=None,
            error=error,
            started_at=started_at,
            completed_at=cls._now(),
        )

    @classmethod
    def _skip_steps(
        cls,
        steps: tuple[PlanStep, ...],
    ) -> tuple[StepExecutionResult, ...]:
        return tuple(
            StepExecutionResult(
                step_id=step.id,
                status=ExecutionStatus.SKIPPED,
                provider_id=None,
                content=None,
                error="Execução interrompida por falha anterior",
                started_at=None,
                completed_at=cls._now(),
            )
            for step in steps
        )

    @classmethod
    def _build_report(
        cls,
        *,
        mission: Mission,
        plan: Plan,
        status: ExecutionStatus,
        step_results: list[StepExecutionResult],
        started_at: datetime,
    ) -> MissionExecutionReport:
        return MissionExecutionReport(
            mission_id=mission.id,
            plan_id=plan.id,
            status=status,
            step_results=tuple(step_results),
            started_at=started_at,
            completed_at=cls._now(),
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
