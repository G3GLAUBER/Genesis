from dataclasses import FrozenInstanceError, replace
from datetime import datetime

import pytest

from Core.registry import Registry
from Core.result import Result
from Engines.AI import (
    AIOrchestrator,
    AIRequest,
    AIResponse,
    FakeProvider,
)
from Engines.Execution import (
    ExecutionStatus,
    MissionExecutionEngine,
    MissionExecutionFailure,
    MissionExecutionReport,
    StepExecutionResult,
)
from Engines.Mission import MissionEngine
from Engines.Planning import Plan, PlanStep, Planner


class StubAIOrchestrator:
    def __init__(self, *outcomes: object) -> None:
        self._outcomes = list(outcomes)
        self.requests: list[AIRequest] = []

    def generate(self, request: AIRequest) -> Result:
        self.requests.append(request)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def success(
    content: str = "Resposta",
    *,
    provider_id: str = "provider",
    capability: str = "text_generation",
) -> Result:
    return Result.success(
        "Gerado",
        AIResponse(
            provider_id=provider_id,
            content=content,
            capability=capability,
        ),
    )


def create_mission():
    return MissionEngine().create(
        title="Missão",
        objective="Executar um plano",
        source="Tests",
    ).data


def create_step(
    title: str,
    order: int,
    *,
    dependencies: tuple[str, ...] = (),
    capability: str | None = "text_generation",
) -> PlanStep:
    return PlanStep.create(
        title=title,
        description=f"Descrição de {title}",
        order=order,
        dependencies=dependencies,
        capability=capability,
    )


def create_plan(mission, steps: tuple[PlanStep, ...]) -> Plan:
    result = Planner().create_plan(mission=mission, steps=steps)
    assert result.is_success is True
    return result.data


def execute(outcomes: tuple[object, ...], steps: tuple[PlanStep, ...]):
    mission = create_mission()
    plan = create_plan(mission, steps)
    orchestrator = StubAIOrchestrator(*outcomes)
    result = MissionExecutionEngine(orchestrator).execute(
        mission=mission,
        plan=plan,
    )
    return result, orchestrator, mission, plan


def test_executes_one_step_successfully():
    step = create_step("Única", 1)

    result, orchestrator, _, _ = execute((success(),), (step,))

    assert result.is_success is True
    assert result.data.step_results[0].status is ExecutionStatus.COMPLETED
    assert len(orchestrator.requests) == 1


def test_executes_multiple_steps_successfully():
    first = create_step("Primeira", 1)
    second = create_step("Segunda", 2, dependencies=(first.id,))

    result, orchestrator, _, _ = execute(
        (success("Um"), success("Dois")),
        (first, second),
    )

    assert result.is_success is True
    assert len(orchestrator.requests) == 2
    assert len(result.data.step_results) == 2


def test_executes_steps_in_plan_order():
    first = create_step("Primeira", 1)
    second = create_step("Segunda", 2)

    _, orchestrator, _, _ = execute(
        (success("Um"), success("Dois")),
        (second, first),
    )

    assert orchestrator.requests[0].prompt.startswith("Primeira\n\n")
    assert orchestrator.requests[1].prompt.startswith("Segunda\n\n")


def test_executes_step_after_completed_dependency():
    first = create_step("Dependência", 1)
    second = create_step("Dependente", 2, dependencies=(first.id,))

    result, _, _, _ = execute(
        (success(), success()),
        (first, second),
    )

    assert tuple(item.status for item in result.data.step_results) == (
        ExecutionStatus.COMPLETED,
        ExecutionStatus.COMPLETED,
    )


def test_rejects_plan_from_another_mission():
    mission = create_mission()
    other = create_mission()
    plan = create_plan(other, (create_step("Etapa", 1),))

    result = MissionExecutionEngine(StubAIOrchestrator()).execute(
        mission=mission,
        plan=plan,
    )

    assert result.is_success is False
    assert result.data.code == "mission_plan_mismatch"


def test_rejects_invalid_mission():
    mission = create_mission()
    plan = create_plan(mission, (create_step("Etapa", 1),))

    result = MissionExecutionEngine(StubAIOrchestrator()).execute(
        mission=None,
        plan=plan,
    )

    assert result.data == MissionExecutionFailure(
        code="invalid_mission",
        message="Mission inválida",
    )


def test_rejects_invalid_plan():
    result = MissionExecutionEngine(StubAIOrchestrator()).execute(
        mission=create_mission(),
        plan=None,
    )

    assert result.is_success is False
    assert result.data.code == "invalid_plan"


def test_step_without_capability_fails_without_ai_call():
    step = create_step("Sem capacidade", 1, capability=None)

    result, orchestrator, _, _ = execute((), (step,))

    assert result.is_success is False
    assert result.data.step_results[0].error == "Etapa sem capability"
    assert orchestrator.requests == []


def test_ai_orchestrator_success_completes_step():
    result, _, _, _ = execute(
        (success(),),
        (create_step("Etapa", 1),),
    )

    assert result.data.step_results[0].status is ExecutionStatus.COMPLETED


def test_ai_orchestrator_error_fails_step():
    result, _, _, _ = execute(
        (Result.error("Falha controlada"),),
        (create_step("Etapa", 1),),
    )

    step_result = result.data.step_results[0]
    assert step_result.status is ExecutionStatus.FAILED
    assert step_result.error == "Falha controlada"


def test_ai_orchestrator_exception_is_controlled_and_sanitized():
    result, _, _, _ = execute(
        (RuntimeError("token=secret"),),
        (create_step("Etapa", 1),),
    )

    assert result.is_success is False
    assert result.data.step_results[0].error == (
        "Falha inesperada do AIOrchestrator: RuntimeError"
    )
    assert "secret" not in repr(result.data)


def test_preserves_winning_provider():
    result, _, _, _ = execute(
        (success(provider_id="winner"),),
        (create_step("Etapa", 1),),
    )

    assert result.data.step_results[0].provider_id == "winner"


def test_preserves_response_content():
    result, _, _, _ = execute(
        (success("Conteúdo final"),),
        (create_step("Etapa", 1),),
    )

    assert result.data.step_results[0].content == "Conteúdo final"


def test_failure_stops_following_ai_calls():
    first = create_step("Primeira", 1)
    second = create_step("Segunda", 2)

    _, orchestrator, _, _ = execute(
        (Result.error("Falha"), success()),
        (first, second),
    )

    assert len(orchestrator.requests) == 1


def test_remaining_steps_are_marked_skipped():
    first = create_step("Primeira", 1)
    second = create_step("Segunda", 2)
    third = create_step("Terceira", 3)

    result, _, _, _ = execute(
        (Result.error("Falha"),),
        (first, second, third),
    )

    assert tuple(item.status for item in result.data.step_results) == (
        ExecutionStatus.FAILED,
        ExecutionStatus.SKIPPED,
        ExecutionStatus.SKIPPED,
    )


def test_success_report_is_completed():
    result, _, _, _ = execute(
        (success(),),
        (create_step("Etapa", 1),),
    )

    assert result.data.status is ExecutionStatus.COMPLETED


def test_failure_report_is_failed():
    result, _, _, _ = execute(
        (Result.error("Falha"),),
        (create_step("Etapa", 1),),
    )

    assert result.data.status is ExecutionStatus.FAILED


def test_report_and_step_timestamps_are_timezone_aware_and_ordered():
    result, _, _, _ = execute(
        (success(),),
        (create_step("Etapa", 1),),
    )
    report = result.data
    step_result = report.step_results[0]

    assert isinstance(report.started_at, datetime)
    assert report.started_at.tzinfo is not None
    assert report.started_at <= report.completed_at
    assert step_result.started_at <= step_result.completed_at


def test_execution_structures_are_immutable():
    result, _, _, _ = execute(
        (success(),),
        (create_step("Etapa", 1),),
    )
    report = result.data

    with pytest.raises(FrozenInstanceError):
        report.status = ExecutionStatus.FAILED
    with pytest.raises(FrozenInstanceError):
        report.step_results[0].content = "Alterado"


def test_execution_does_not_modify_original_inputs():
    mission = create_mission()
    first = create_step("Primeira", 1)
    second = create_step("Segunda", 2)
    plan = create_plan(mission, (second, first))
    original_mission = mission
    original_plan = plan
    original_steps = plan.steps

    MissionExecutionEngine(
        StubAIOrchestrator(success(), success())
    ).execute(mission=mission, plan=plan)

    assert mission == original_mission
    assert plan == original_plan
    assert plan.steps == original_steps


def test_result_success_contains_execution_report():
    result, _, _, _ = execute(
        (success(),),
        (create_step("Etapa", 1),),
    )

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, MissionExecutionReport)


def test_result_error_contains_structured_report():
    result, _, _, _ = execute(
        (Result.error("Falha"),),
        (create_step("Etapa", 1),),
    )

    assert isinstance(result, Result)
    assert result.is_success is False
    assert isinstance(result.data, MissionExecutionReport)


def test_empty_plan_is_rejected():
    mission = create_mission()
    valid_plan = create_plan(mission, (create_step("Etapa", 1),))
    empty_plan = replace(valid_plan, steps=())

    result = MissionExecutionEngine(StubAIOrchestrator()).execute(
        mission=mission,
        plan=empty_plan,
    )

    assert result.is_success is False
    assert result.data.code == "empty_plan"


def test_incomplete_dependency_prevents_execution():
    later = create_step("Posterior", 2)
    earlier = create_step(
        "Anterior",
        1,
        dependencies=(later.id,),
    )

    result, orchestrator, _, _ = execute((), (earlier, later))

    assert result.is_success is False
    assert "Dependências não concluídas" in result.data.step_results[0].error
    assert result.data.step_results[1].status is ExecutionStatus.SKIPPED
    assert orchestrator.requests == []


def test_is_compatible_with_real_ai_orchestrator_v2():
    registry = Registry()
    provider = FakeProvider()
    registry.register(provider.provider_id, provider)
    ai_orchestrator = AIOrchestrator(
        registry,
        provider_ids=(provider.provider_id,),
    )
    mission = create_mission()
    plan = create_plan(mission, (create_step("Etapa", 1),))

    result = MissionExecutionEngine(ai_orchestrator).execute(
        mission=mission,
        plan=plan,
    )

    assert result.is_success is True
    assert result.data.step_results[0].provider_id == "fake"


def test_invalid_ai_response_fails_step():
    invalid = Result.success(
        "Inválida",
        AIResponse(
            provider_id="provider",
            content="Conteúdo",
            capability="wrong_capability",
        ),
    )

    result, _, _, _ = execute(
        (invalid,),
        (create_step("Etapa", 1),),
    )

    assert result.is_success is False
    assert result.data.step_results[0].error == (
        "AIOrchestrator retornou AIResponse inválida"
    )


def test_request_uses_step_capability_title_and_description():
    step = create_step("Analisar", 1, capability="analysis")

    _, orchestrator, _, _ = execute(
        (success(capability="analysis"),),
        (step,),
    )

    assert orchestrator.requests == [
        AIRequest(
            prompt="Analisar\n\nDescrição de Analisar",
            capability="analysis",
        )
    ]
