from __future__ import annotations

import sqlite3
from datetime import datetime

from Engines.Workspace import Workspace, WorkspaceRepository, WorkspaceStatus
from Infrastructure.Persistence.database import SQLiteDatabase


class SQLiteWorkspaceRepository(WorkspaceRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def store(self, workspace: Workspace) -> Workspace:
        with self._database.transaction() as connection:
            connection.execute(
                "INSERT INTO workspaces VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "name=excluded.name, "
                "description=excluded.description, "
                "status=excluded.status",
                (
                    workspace.id,
                    workspace.name,
                    workspace.description,
                    workspace.created_at.isoformat(),
                    workspace.status.value,
                ),
            )
            connection.execute(
                "DELETE FROM workspace_missions WHERE workspace_id=?",
                (workspace.id,),
            )
            connection.executemany(
                "INSERT INTO workspace_missions VALUES (?, ?)",
                ((workspace.id, item) for item in workspace.mission_ids),
            )
        return workspace

    def get(self, workspace_id: str) -> Workspace | None:
        connection = self._database.connect()
        try:
            row = connection.execute(
                "SELECT * FROM workspaces WHERE id=?",
                (workspace_id,),
            ).fetchone()
            return self._model(connection, row) if row else None
        finally:
            connection.close()

    def list(self) -> tuple[Workspace, ...]:
        connection = self._database.connect()
        try:
            rows = connection.execute(
                "SELECT * FROM workspaces ORDER BY rowid"
            ).fetchall()
            return tuple(self._model(connection, row) for row in rows)
        finally:
            connection.close()

    @staticmethod
    def _model(
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> Workspace:
        missions = connection.execute(
            "SELECT mission_id FROM workspace_missions "
            "WHERE workspace_id=? ORDER BY rowid",
            (row["id"],),
        ).fetchall()
        return Workspace(
            row["id"],
            row["name"],
            row["description"],
            datetime.fromisoformat(row["created_at"]),
            WorkspaceStatus(row["status"]),
            tuple(item[0] for item in missions),
        )
