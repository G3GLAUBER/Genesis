from dataclasses import FrozenInstanceError

import pytest

from Core.registry import Registry
from Core.result import Result
from Engines.AI import AIOrchestrator, FakeProvider
from Engines.Execution import ExecutionStatus, MissionExecutionEngine
from Engines.Mission import MissionEngine
from Engines.Planning import Planner
from Interfaces.Companion import (
    CompanionApplication,
    CompanionDashboard,
    CompanionExecution,
)


def test_previous_public_constructor_executes_without_workspace():
    registry = Registry()
    provider = FakeProvider()
    registry.register(provider.provider_id, provider)
    application = CompanionApplication(
        MissionEngine(),
        Planner(),
        MissionExecutionEngine(
            AIOrchestrator(registry, provider_id=provider.provider_id)
        ),
        provider_id=provider.provider_id,
    )

    result = application.execute_mission(
        title="Compatibilidade",
        objective="Preservar o padrão público anterior",
    )

    assert result.is_success is True
    assert isinstance(result.data, CompanionExecution)
    assert result.data.report.status is ExecutionStatus.COMPLETED
    assert result.data.workspace is None


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
    assert result.data.mission.id in result.data.workspace.mission_ids


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


def test_companion_lists_creates_and_opens_workspaces():
    application = CompanionApplication.default()

    created = application.create_workspace(
        name="Novo Produto",
        description="Workspace de produto",
    )
    opened = application.open_workspace(created.data.id)

    assert created.is_success is True
    assert opened.data == created.data
    assert len(application.list_workspaces().data) == 2
    assert application.dashboard().active_workspace == created.data


def test_companion_dashboard_counts_workspaces_and_missions():
    application = CompanionApplication.default()
    workspace = application.create_workspace(name="Produto").data
    execution = application.execute_mission(
        title="Entregar Workspace",
        objective="Concluir a fundação",
        workspace_id=workspace.id,
    )

    dashboard = application.dashboard()

    assert isinstance(dashboard, CompanionDashboard)
    assert dashboard.workspace_count == 2
    assert dashboard.mission_count == 1
    assert dashboard.active_workspace.id == workspace.id
    assert execution.data.mission.id in execution.data.workspace.mission_ids


def test_companion_complete_workspace_mission_flow():
    application = CompanionApplication.default()
    workspace = application.create_workspace(name="Sprint Workspace").data

    execution = application.execute_mission(
        title="Fluxo completo",
        objective="Criar, planejar, executar e associar",
        workspace_id=workspace.id,
    )
    opened = application.open_workspace(workspace.id)

    assert execution.is_success is True
    assert execution.data.plan.mission_id == execution.data.mission.id
    assert execution.data.report.status is ExecutionStatus.COMPLETED
    assert opened.data.mission_ids == (execution.data.mission.id,)


def test_operational_dashboard_tracks_missions_memory_and_executions():
    application = CompanionApplication.default()
    workspace = application.dashboard().active_workspace
    execution = application.execute_mission(
        title="Dashboard operacional",
        objective="Atualizar métricas e timeline",
        workspace_id=workspace.id,
    )
    memory = application.store_memory(
        workspace_id=workspace.id,
        mission_id=execution.data.mission.id,
        category="resultado",
        title="Sprint validada",
        content="Companion operacional",
    )

    dashboard = application.dashboard()
    timeline = application.timeline()

    assert memory.is_success is True
    assert dashboard.mission_count == 1
    assert dashboard.memory_count == 1
    assert dashboard.execution_count == 1
    assert dashboard.application_health == "DISPONÍVEL"
    assert dashboard.available_service_count == 3
    assert dashboard.service_count == 3
    assert dashboard.last_activity is not None
    assert {item.title for item in timeline} == {
        "Missão criada",
        "Plano criado",
        "Execução concluída",
        "Memória registrada",
    }


def test_companion_lists_operational_data_only_for_active_workspace():
    application = CompanionApplication.default()
    first = application.dashboard().active_workspace
    application.execute_mission(
        title="Primeiro Workspace",
        objective="Manter isolamento operacional",
        workspace_id=first.id,
    )
    second = application.create_workspace(name="Segundo Workspace").data
    application.store_memory(
        workspace_id=second.id,
        category="nota",
        title="Memória isolada",
        content="Somente no segundo Workspace",
    )

    assert application.list_missions().data == ()
    assert len(application.list_memories().data) == 1
    assert application.dashboard().active_workspace.id == second.id


def test_application_health_is_degraded_without_memory_service():
    registry = Registry()
    provider = FakeProvider()
    registry.register(provider.provider_id, provider)
    application = CompanionApplication(
        MissionEngine(),
        Planner(),
        MissionExecutionEngine(
            AIOrchestrator(registry, provider_id=provider.provider_id)
        ),
        provider_id=provider.provider_id,
    )

    dashboard = application.dashboard()

    assert dashboard.application_health == "DEGRADADO"
    assert dashboard.available_service_count == 2
    assert dashboard.service_count == 3
