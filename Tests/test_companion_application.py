from dataclasses import FrozenInstanceError

import pytest

from Core.result import Result
from Engines.Execution import ExecutionStatus
from Interfaces.Companion import CompanionApplication, CompanionExecution


def test_companion_creates_plans_and_executes_mission():
    result = CompanionApplication.default().execute_mission(
        title="Criar uma renda adicional",
        objective="Aumentar a renda mensal em mil euros",
    )

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, CompanionExecution)
    assert result.data.mission.title == "Criar uma renda adicional"
    assert result.data.plan.mission_id == result.data.mission.id
    assert len(result.data.plan.steps) == 3
    assert result.data.report.status is ExecutionStatus.COMPLETED


def test_companion_uses_fake_provider_for_every_step():
    result = CompanionApplication.default().execute_mission(
        title="Missão",
        objective="Executar demonstração",
    )

    assert result.data.provider_id == "fake"
    assert tuple(
        step.provider_id for step in result.data.report.step_results
    ) == ("fake", "fake", "fake")
    assert all(
        step.content.startswith("Fake: ")
        for step in result.data.report.step_results
    )


def test_companion_rejects_invalid_form_data():
    result = CompanionApplication.default().execute_mission(
        title=" ",
        objective="Objetivo",
    )

    assert result.is_success is False
    assert "title" in result.message


def test_companion_execution_is_immutable():
    result = CompanionApplication.default().execute_mission(
        title="Missão",
        objective="Objetivo",
    )

    with pytest.raises(FrozenInstanceError):
        result.data.provider_id = "outro"
