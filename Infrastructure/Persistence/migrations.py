from __future__ import annotations

from Infrastructure.Persistence.database import SQLiteDatabase


MIGRATIONS = ((1, """
CREATE TABLE IF NOT EXISTS workspaces (
 id TEXT PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
 description TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workspace_missions (
 workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
 mission_id TEXT NOT NULL, PRIMARY KEY (workspace_id, mission_id));
CREATE TABLE IF NOT EXISTS projects (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
 title TEXT NOT NULL, client TEXT NOT NULL, address TEXT NOT NULL,
 description TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS project_missions (
 project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
 mission_id TEXT NOT NULL, PRIMARY KEY (project_id, mission_id));
CREATE TABLE IF NOT EXISTS memories (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
 mission_id TEXT, category TEXT NOT NULL, title TEXT NOT NULL,
 content TEXT NOT NULL, metadata TEXT NOT NULL, created_at TEXT NOT NULL);
"""),)


def migrate(database: SQLiteDatabase) -> None:
    with database.transaction() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        applied = {
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations"
            )
        }
        for version, script in MIGRATIONS:
            if version not in applied:
                for statement in script.split(";"):
                    if statement.strip():
                        connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations(version) VALUES (?)",
                    (version,),
                )
