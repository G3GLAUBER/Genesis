from dataclasses import FrozenInstanceError, replace

import pytest

from Core.result import Result
from Engines.Mission import MissionEngine
from Engines.Planning import Plan, Planner, PlanStatus, PlanStep, StepStatus


def create_mission():
    return MissionEngine().create(
        title="Criar renda adicional",
        objective="Aumentar a renda mensal",
        source="CLI",
    ).data


def create_steps():
    research = PlanStep.create(
        title="Pesquisa",
        description="Pesquisar oportunidades",
        order=1,
        capability="web_search",
    )
    execute = PlanStep.create(
        title="Execução",
        description="Executar oportunidade escolhida",
        order=2,
        dependencies=(research.id,),
    )
    return research, execute


def create_plan_result() -> Result:
    research, execute = create_steps()
    return Planner().create_plan(
        mission=create_mission(),
        steps=(research, execute),
    )


def test_creates_valid_plan():
    plan = create_plan_result().data

    assert isinstance(plan, Plan)
    assert plan.status is PlanStatus.READY
    assert all(step.status is StepStatus.PENDING for step in plan.steps)


def test_plan_references_mission_id():
    mission = create_mission()
    steps = create_steps()

    result = Planner().create_plan(mission=mission, steps=steps)

    assert result.data.mission_id == mission.id


def test_steps_are_sorted_deterministically():
    first, second = create_steps()

    result = Planner().create_plan(
        mission=create_mission(),
        steps=(second, first),
    )

    assert result.data.steps == (first, second)


def test_duplicate_order_is_rejected():
    first, second = create_steps()
    duplicate = replace(second, order=first.order)

    result = Planner().create_plan(
        mission=create_mission(),
        steps=(first, duplicate),
    )

    assert result.is_success is False
    assert "ordem de etapa duplicada" in result.message


def test_missing_dependency_is_rejected():
    step = PlanStep.create(
        title="Etapa",
        description="Descrição",
        order=1,
        dependencies=("missing",),
    )

    result = Planner().create_plan(
        mission=create_mission(),
        steps=(step,),
    )

    assert result.is_success is False
    assert "dependência inexistente" in result.message


def test_circular_dependency_is_rejected():
    first = PlanStep(
        id="first",
        title="Primeira",
        description="Primeira etapa",
        order=1,
        dependencies=("second",),
    )
    second = PlanStep(
        id="second",
        title="Segunda",
        description="Segunda etapa",
        order=2,
        dependencies=("first",),
    )

    result = Planner().create_plan(
        mission=create_mission(),
        steps=(first, second),
    )

    assert result.is_success is False
    assert "circulares" in result.message


def test_plan_step_is_immutable():
    step = create_steps()[0]

    with pytest.raises(FrozenInstanceError):
        step.order = 3


def test_plan_is_immutable():
    plan = create_plan_result().data

    with pytest.raises(FrozenInstanceError):
        plan.status = PlanStatus.ACTIVE


def test_invalid_mission_is_rejected():
    result = Planner().create_plan(
        mission="not-a-mission",
        steps=create_steps(),
    )

    assert result.is_success is False
    assert "mission deve ser uma Mission" in result.message


def test_empty_step_list_is_rejected():
    result = Planner().create_plan(mission=create_mission(), steps=())

    assert result.is_success is False
    assert "steps não pode ser vazio" in result.message


def test_capability_is_preserved():
    plan = create_plan_result().data

    assert plan.steps[0].capability == "web_search"


def test_success_result_contains_plan():
    result = create_plan_result()

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, Plan)


def test_invalid_step_returns_error_result():
    invalid = PlanStep.create(
        title=" ",
        description="Descrição",
        order=1,
    )

    result = Planner().create_plan(
        mission=create_mission(),
        steps=(invalid,),
    )

    assert isinstance(result, Result)
    assert result.is_success is False
    assert result.data is None


def test_planning_does_not_modify_supplied_steps():
    first, second = create_steps()
    supplied = (second, first)
    snapshot = tuple(supplied)

    Planner().create_plan(mission=create_mission(), steps=supplied)

    assert supplied == snapshot
    assert supplied == (second, first)
