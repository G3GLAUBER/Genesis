from dataclasses import FrozenInstanceError

import pytest

from Application import (
    MissionApplicationExecution,
    MissionApplicationService,
    WorkspaceApplicationService,
    bootstrap_application,
)
from Core.result import Result
from Engines.Execution import ExecutionStatus
from Engines.Workspace import WorkspaceManager, WorkspaceStatus
from Interfaces.Companion import CompanionApplication, CompanionExecution


def test_bootstrap_composes_isolated_application_dependencies():
    first = bootstrap_application(persistent=False)
    second = bootstrap_application(persistent=False)

    assert first.registry.get("fake") is first.provider
    assert first.ai_orchestrator.provider_ids == ("fake",)
    assert first.mission_service._mission_engine is first.mission_engine
    assert first.mission_service._planner is first.planner
    assert first.mission_service._execution_engine is first.execution_engine
    assert first.workspace_service._manager is first.workspace_manager
    assert first.workspace_manager._engine is first.workspace_engine
    assert first.project_service._engine is first.project_engine
    assert first.project_engine._repository is first.project_repository
    assert first.workspace_manager is not second.workspace_manager
    assert first.project_repository is not second.project_repository


def test_mission_service_creates_plans_and_executes_mission():
    container = bootstrap_application(persistent=False)

    result = container.mission_service.execute_mission(
        title="Application Layer",
        objective="Coordenar casos de uso",
    )

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, MissionApplicationExecution)
    assert result.data.plan.mission_id == result.data.mission.id
    assert result.data.report.status is ExecutionStatus.COMPLETED
    assert len(result.data.plan.steps) == 3


def test_mission_service_optionally_associates_workspace():
    container = bootstrap_application(persistent=False)
    workspace = container.workspace_service.create(name="Produto").data

    result = container.mission_service.execute_mission(
        title="Missão associada",
        objective="Validar associação opcional",
        workspace_id=workspace.id,
    )

    assert result.is_success is True
    assert result.data.workspace.id == workspace.id
    assert result.data.mission.id in result.data.workspace.mission_ids


def test_mission_service_supports_legacy_use_without_workspace():
    container = bootstrap_application(persistent=False)
    service = MissionApplicationService(
        container.mission_engine,
        container.planner,
        container.execution_engine,
        provider_id=container.provider.provider_id,
    )

    result = service.execute_mission(
        title="Uso legado",
        objective="Executar sem Workspace",
    )

    assert result.is_success is True
    assert result.data.workspace is None


def test_workspace_service_coordinates_crud_active_and_association():
    service = WorkspaceApplicationService(WorkspaceManager())
    created = service.create(name="Workspace", description="Aplicação")
    listed = service.list()
    obtained = service.get(created.data.id)
    associated = service.associate_mission(
        created.data.id,
        mission_id="mission-1",
    )
    archived = service.archive(created.data.id)
    restored = service.restore(created.data.id)
    activated = service.set_active(created.data.id)

    assert listed.data == (created.data,)
    assert obtained.data == created.data
    assert associated.data.mission_ids == ("mission-1",)
    assert archived.data.status is WorkspaceStatus.ARCHIVED
    assert restored.data.status is WorkspaceStatus.ACTIVE
    assert activated.is_success is True
    assert service.active_workspace_id == created.data.id


def test_application_failures_remain_controlled_results():
    container = bootstrap_application(persistent=False)

    invalid_mission = container.mission_service.execute_mission(
        title=" ",
        objective="Objetivo",
    )
    missing_workspace = container.mission_service.execute_mission(
        title="Missão",
        objective="Objetivo",
        workspace_id="missing",
    )

    assert isinstance(invalid_mission, Result)
    assert invalid_mission.is_success is False
    assert isinstance(missing_workspace, Result)
    assert missing_workspace.is_success is False


def test_application_execution_dto_is_immutable():
    execution = bootstrap_application(persistent=False).mission_service.execute_mission(
        title="Imutabilidade",
        objective="Proteger retorno agregado",
    ).data

    with pytest.raises(FrozenInstanceError):
        execution.provider_id = "other"


def test_companion_delegates_to_application_services_and_keeps_alias():
    application = CompanionApplication.default(persistent=False)

    result = application.execute_mission(
        title="Companion",
        objective="Usar Application Layer",
    )

    assert isinstance(application._mission_service, MissionApplicationService)
    assert isinstance(
        application._workspace_service,
        WorkspaceApplicationService,
    )
    assert CompanionExecution is MissionApplicationExecution
    assert isinstance(result.data, CompanionExecution)
