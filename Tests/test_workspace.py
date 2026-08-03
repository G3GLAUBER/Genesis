from dataclasses import FrozenInstanceError
from datetime import datetime
from uuid import UUID

import pytest

from Core.result import Result
from Engines.Workspace import (
    Workspace,
    WorkspaceEngine,
    WorkspaceManager,
    WorkspaceStatus,
)


def create_workspace() -> Workspace:
    return WorkspaceEngine().create(
        name="  Genesis Lab  ",
        description="  Produto principal  ",
    ).data


def test_workspace_creation_is_normalized_and_uses_result():
    result = WorkspaceEngine().create(
        name="  Genesis Lab  ",
        description="  Produto principal  ",
    )

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, Workspace)
    assert result.data.name == "Genesis Lab"
    assert result.data.description == "Produto principal"
    assert result.data.status is WorkspaceStatus.ACTIVE
    assert str(UUID(result.data.id)) == result.data.id
    assert isinstance(result.data.created_at, datetime)
    assert result.data.created_at.tzinfo is not None


def test_workspace_rejects_invalid_name():
    result = WorkspaceEngine().create(name=" ", description="Descrição")

    assert result.is_success is False
    assert "name" in result.message


def test_workspace_is_immutable():
    workspace = create_workspace()

    with pytest.raises(FrozenInstanceError):
        workspace.name = "Outro"


def test_workspace_mission_ids_are_immutable():
    source = ["mission-1"]
    workspace = Workspace(
        id="workspace-1",
        name="Workspace",
        description="",
        created_at=datetime.now().astimezone(),
        status=WorkspaceStatus.ACTIVE,
        mission_ids=source,
    )
    source.append("mission-2")

    assert workspace.mission_ids == ("mission-1",)
    with pytest.raises(TypeError):
        workspace.mission_ids[0] = "changed"


def test_rename_returns_new_workspace_without_changing_original():
    original = create_workspace()
    result = WorkspaceEngine().rename(workspace=original, name="Novo nome")

    assert result.is_success is True
    assert result.data.name == "Novo nome"
    assert result.data.id == original.id
    assert original.name == "Genesis Lab"


def test_archive_and_restore_workspace():
    engine = WorkspaceEngine()
    original = create_workspace()

    archived = engine.archive(workspace=original)
    restored = engine.restore(workspace=archived.data)

    assert archived.data.status is WorkspaceStatus.ARCHIVED
    assert restored.data.status is WorkspaceStatus.ACTIVE
    assert original.status is WorkspaceStatus.ACTIVE


def test_add_and_remove_mission_without_mutating_workspace():
    engine = WorkspaceEngine()
    original = create_workspace()

    added = engine.add_mission(workspace=original, mission_id=" mission-1 ")
    removed = engine.remove_mission(
        workspace=added.data,
        mission_id="mission-1",
    )

    assert original.mission_ids == ()
    assert added.data.mission_ids == ("mission-1",)
    assert removed.data.mission_ids == ()


def test_duplicate_mission_is_rejected():
    engine = WorkspaceEngine()
    workspace = engine.add_mission(
        workspace=create_workspace(),
        mission_id="mission-1",
    ).data

    result = engine.add_mission(
        workspace=workspace,
        mission_id="mission-1",
    )

    assert result.is_success is False
    assert "já associada" in result.message


def test_archived_workspace_cannot_change_associations():
    engine = WorkspaceEngine()
    archived = engine.archive(workspace=create_workspace()).data

    result = engine.add_mission(
        workspace=archived,
        mission_id="mission-1",
    )

    assert result.is_success is False
    assert "arquivado" in result.message


def test_manager_rejects_duplicate_names_case_insensitively():
    manager = WorkspaceManager()
    manager.create(name="Genesis Lab")

    result = manager.create(name=" genesis lab ")

    assert result.is_success is False
    assert "já existe" in result.message


def test_manager_get_and_list_workspaces_in_creation_order():
    manager = WorkspaceManager()
    first = manager.create(name="Primeiro").data
    second = manager.create(name="Segundo").data

    listed = manager.list()

    assert manager.get(first.id).data == first
    assert listed.data == (first, second)


def test_manager_logical_delete_hides_workspace_and_restore_recovers_it():
    manager = WorkspaceManager()
    workspace = manager.create(name="Temporário").data

    deleted = manager.delete(workspace.id)

    assert deleted.data.status is WorkspaceStatus.ARCHIVED
    assert manager.list().data == ()
    assert manager.list(include_archived=True).data == (deleted.data,)

    restored = manager.restore(workspace.id)

    assert restored.data.status is WorkspaceStatus.ACTIVE
    assert manager.list().data == (restored.data,)


def test_manager_searches_active_workspaces_by_partial_name():
    manager = WorkspaceManager()
    genesis = manager.create(name="Genesis Produto").data
    manager.create(name="Operações")
    archived = manager.create(name="Genesis Arquivo").data
    manager.delete(archived.id)

    result = manager.search("GENESIS")

    assert result.data == (genesis,)
    assert len(manager.search("genesis", include_archived=True).data) == 2


def test_manager_complete_flow():
    manager = WorkspaceManager()
    created = manager.create(name="Produto", description="Sprint").data
    renamed = manager.rename(created.id, name="Genesis Produto").data
    associated = manager.add_mission(
        renamed.id,
        mission_id="mission-1",
    ).data
    disassociated = manager.remove_mission(
        associated.id,
        mission_id="mission-1",
    ).data
    archived = manager.delete(disassociated.id).data
    restored = manager.restore(archived.id).data

    assert restored.name == "Genesis Produto"
    assert restored.mission_ids == ()
    assert restored.status is WorkspaceStatus.ACTIVE
