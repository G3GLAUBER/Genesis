import sqlite3

import pytest

from Application import bootstrap_application
from Engines.Memory import MemoryEngine, MemoryQuery
from Engines.Projects import ProjectEngine
from Engines.Workspace import WorkspaceEngine, WorkspaceManager
from Infrastructure.Persistence import (
    SQLiteDatabase,
    SQLiteMemoryRepository,
    SQLiteProjectRepository,
    SQLiteWorkspaceRepository,
    migrate,
)
from Interfaces.Companion import CompanionApplication


@pytest.fixture
def database(tmp_path):
    db = SQLiteDatabase(tmp_path / "genesis-test.db")
    migrate(db)
    return db


def test_database_is_created_migrated_versioned_and_idempotent(database):
    migrate(database)
    assert database.path.exists()
    connection = database.connect()
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        versions = connection.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()
    finally:
        connection.close()
    assert {"schema_migrations", "workspaces", "projects", "memories"} <= tables
    assert [row[0] for row in versions] == [1]


def test_foreign_keys_and_rollback(database):
    connection = database.connect()
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()
    with pytest.raises(sqlite3.IntegrityError):
        with database.transaction() as connection:
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("p", "missing", "t", "c", "a", "d", "active", "now"),
            )
    connection = database.connect()
    try:
        assert connection.execute("SELECT count(*) FROM projects").fetchone()[0] == 0
    finally:
        connection.close()


def test_workspace_persists_crud_search_and_missions(database):
    first = WorkspaceManager(
        WorkspaceEngine(), repository=SQLiteWorkspaceRepository(database)
    )
    created = first.create(name="Persistente", description="SQLite").data
    first.add_mission(created.id, mission_id="mission-1")
    second = WorkspaceManager(
        WorkspaceEngine(), repository=SQLiteWorkspaceRepository(database)
    )
    assert second.get(created.id).data.mission_ids == ("mission-1",)
    assert second.list().data[0].name == "Persistente"
    assert second.search("sist").data[0].id == created.id
    assert second.create(name="persistente").is_success is False
    assert second.delete(created.id).is_success is True
    assert second.restore(created.id).is_success is True


def test_project_persists_isolates_archives_and_attaches(database):
    workspaces = WorkspaceManager(
        WorkspaceEngine(), repository=SQLiteWorkspaceRepository(database)
    )
    one = workspaces.create(name="One").data
    two = workspaces.create(name="Two").data
    engine = ProjectEngine(SQLiteProjectRepository(database))
    project = engine.create(
        workspace_id=one.id, title="Obra", client="Cliente", address="Rua"
    ).data
    engine.attach_mission(project.id, mission_id="mission-1")
    reopened = ProjectEngine(SQLiteProjectRepository(database))
    assert reopened.get(project.id).data.mission_ids == ("mission-1",)
    assert len(reopened.list(workspace_id=one.id).data) == 1
    assert reopened.list(workspace_id=two.id).data == ()
    assert reopened.archive(project.id).is_success is True
    assert reopened.restore(project.id).is_success is True
    missing = reopened.create(
        workspace_id="missing", title="X", client="C", address="A"
    )
    assert missing.is_success is False


def test_memory_persists_searches_json_deletes_and_clears(database):
    workspaces = WorkspaceManager(
        WorkspaceEngine(), repository=SQLiteWorkspaceRepository(database)
    )
    one = workspaces.create(name="Memory One").data
    two = workspaces.create(name="Memory Two").data
    engine = MemoryEngine(SQLiteMemoryRepository(database))
    record = engine.store(
        workspace_id=one.id,
        mission_id=None,
        category="decisão",
        title="SQLite",
        content="Persistência textual",
        metadata={"priority": 1, "tags": ["local"]},
    ).data
    engine.store(
        workspace_id=two.id, category="nota", title="Outra", content="Isolada"
    )
    reopened = MemoryEngine(SQLiteMemoryRepository(database))
    restored = reopened.history(workspace_id=one.id).data[0]
    assert restored.id == record.id
    assert dict(restored.metadata) == {"priority": 1, "tags": ("local",)}
    assert reopened.search(MemoryQuery(one.id, "textual")).data.total == 1
    assert (
        reopened.search(
            MemoryQuery(one.id, category="decisão")
        ).data.total
        == 1
    )
    assert reopened.delete(workspace_id=one.id, record_id=record.id).is_success
    assert reopened.clear(workspace_id=two.id).data == 1


def test_bootstrap_modes_and_restart_preserve_all_domains(tmp_path):
    path = tmp_path / "restart.db"
    first = bootstrap_application(database_path=path)
    workspace = first.workspace_service.get_active().data
    project = first.project_service.create(
        workspace_id=workspace.id, title="Persisted", client="C", address="A"
    ).data
    memory = first.memory_service.store(
        workspace_id=workspace.id, category="note", title="Saved", content="Yes"
    ).data
    second = bootstrap_application(database_path=path)
    assert second.persistence_mode == "sqlite"
    assert second.project_service.get(project.id).is_success
    history = second.memory_service.history(workspace_id=workspace.id)
    assert history.data[0].id == memory.id
    memory_mode = bootstrap_application(persistent=False)
    assert memory_mode.persistence_mode == "memory"
    assert memory_mode.database is None


def test_default_bootstrap_is_memory_isolated_and_creates_no_file(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    first = bootstrap_application()
    first.workspace_service.create(name="Somente primeira")
    second = bootstrap_application()

    assert first.persistence_mode == "memory"
    assert second.persistence_mode == "memory"
    assert len(first.workspace_service.list().data) == 2
    assert len(second.workspace_service.list().data) == 1
    assert not (tmp_path / "Data" / "genesis.db").exists()


def test_explicit_persistence_and_custom_path_survive_composition(tmp_path):
    path = tmp_path / "custom" / "genesis.db"
    first = bootstrap_application(persistent=True, database_path=path)
    workspace = first.workspace_service.create(name="Persistência explícita").data
    second = bootstrap_application(persistent=True, database_path=path)
    implied = bootstrap_application(database_path=path)

    assert path.exists()
    assert second.workspace_service.get(workspace.id).is_success
    assert implied.persistence_mode == "sqlite"
    assert implied.workspace_service.get(workspace.id).is_success


def test_persistent_companion_uses_controlled_database(tmp_path):
    path = tmp_path / "companion.db"
    first = CompanionApplication.default(database_path=path)
    project = first.create_project(
        title="Companion persistente", client="Cliente", address="Rua"
    ).data
    second = CompanionApplication.default(database_path=path)

    assert second.get_project(project.id).is_success
    assert second.dashboard().storage_label == "SQLite local"
