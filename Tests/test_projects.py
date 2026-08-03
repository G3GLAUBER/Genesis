from dataclasses import FrozenInstanceError
from datetime import timezone

import pytest

from Application import ProjectService, bootstrap_application
from Core.result import Result
from Engines.Projects import (
    InMemoryProjectRepository,
    Project,
    ProjectEngine,
    ProjectRepository,
    ProjectStatus,
)
from Interfaces.Companion import CompanionApplication


@pytest.fixture
def engine() -> ProjectEngine:
    return ProjectEngine(InMemoryProjectRepository())


def _create(engine: ProjectEngine, **overrides) -> Result:
    fields = {
        "workspace_id": "workspace-1",
        "title": "Empresa Remodelações",
        "client": "Cliente Exemplo",
        "address": "Rua Principal, 10",
        "description": "Remodelação integral",
    }
    fields.update(overrides)
    return engine.create(**fields)


def test_project_creation_is_normalized_immutable_and_utc(engine):
    result = _create(
        engine,
        title="  Empresa Remodelações  ",
        description="  Obra completa  ",
    )

    assert result.is_success is True
    assert isinstance(result.data, Project)
    assert result.data.title == "Empresa Remodelações"
    assert result.data.description == "Obra completa"
    assert result.data.status is ProjectStatus.PLANNING
    assert result.data.created_at.tzinfo is timezone.utc

    with pytest.raises(FrozenInstanceError):
        result.data.title = "Alterado"


@pytest.mark.parametrize(
    "field",
    ("workspace_id", "title", "client", "address"),
)
def test_project_rejects_missing_required_text(engine, field):
    result = _create(engine, **{field: " "})

    assert result.is_success is False
    assert field in result.message


def test_project_description_must_be_text(engine):
    result = _create(engine, description=None)

    assert result.is_success is False
    assert "description" in result.message


def test_repository_contract_and_instances_are_isolated():
    first = InMemoryProjectRepository()
    second = InMemoryProjectRepository()
    project = _create(ProjectEngine(first)).data

    assert isinstance(first, ProjectRepository)
    assert first.get(project.id) == project
    assert second.get(project.id) is None


def test_list_and_get_are_isolated_by_workspace(engine):
    first = _create(engine).data
    second = _create(
        engine,
        workspace_id="workspace-2",
        title="Segunda obra",
    ).data

    assert engine.get(first.id).data == first
    assert engine.list(workspace_id="workspace-1").data == (first,)
    assert engine.list(workspace_id="workspace-2").data == (second,)
    assert engine.get("missing").is_success is False


def test_archive_restore_and_archived_filter(engine):
    project = _create(engine).data
    archived = engine.archive(project.id)

    assert archived.data.status is ProjectStatus.ARCHIVED
    assert engine.list().data == ()
    assert engine.list(include_archived=True).data == (archived.data,)
    assert engine.archive(project.id).is_success is False

    restored = engine.restore(project.id)
    assert restored.data.status is ProjectStatus.ACTIVE
    assert engine.restore(project.id).is_success is False


def test_attach_mission_is_immutable_and_rejects_duplicates(engine):
    project = _create(engine).data
    attached = engine.attach_mission(project.id, mission_id="mission-1")

    assert project.mission_ids == ()
    assert attached.data.mission_ids == ("mission-1",)
    assert engine.attach_mission(
        project.id,
        mission_id="mission-1",
    ).is_success is False


def test_archived_project_does_not_accept_missions(engine):
    project = _create(engine).data
    engine.archive(project.id)

    result = engine.attach_mission(project.id, mission_id="mission-1")

    assert result.is_success is False
    assert "arquivado" in result.message


def test_project_service_reuses_engine_and_validates_workspace():
    container = bootstrap_application(persistent=False)
    workspace = container.workspace_service.get_active().data

    created = container.project_service.create(
        workspace_id=workspace.id,
        title="Projeto Application",
        client="Cliente",
        address="Morada",
    )
    missing = container.project_service.create(
        workspace_id="missing",
        title="Projeto inválido",
        client="Cliente",
        address="Morada",
    )

    assert isinstance(container.project_service, ProjectService)
    assert container.project_service._engine is container.project_engine
    assert created.is_success is True
    assert container.project_service.get(created.data.id).data == created.data
    assert missing.is_success is False


def test_project_service_coordinates_full_flow():
    service = ProjectService(ProjectEngine(InMemoryProjectRepository()))
    created = service.create(
        workspace_id="workspace-1",
        title="Fluxo completo",
        client="Cliente",
        address="Morada",
    )
    attached = service.attach_mission(
        created.data.id,
        mission_id="mission-1",
    )
    archived = service.archive(created.data.id)
    restored = service.restore(created.data.id)

    assert service.list().data == (restored.data,)
    assert attached.data.mission_ids == ("mission-1",)
    assert archived.data.status is ProjectStatus.ARCHIVED
    assert restored.data.status is ProjectStatus.ACTIVE


def test_companion_project_api_and_dashboard_preserve_default_flow():
    application = CompanionApplication.default(persistent=False)
    created = application.create_project(
        title="Projeto Companion",
        client="Cliente",
        address="Morada",
    )

    dashboard = application.dashboard()

    assert created.is_success is True
    assert application.get_project(created.data.id).data == created.data
    assert application.list_projects().data == (created.data,)
    assert dashboard.active_project_count == 1
    assert dashboard.completed_project_count == 0
    assert dashboard.recent_projects == (created.data,)
