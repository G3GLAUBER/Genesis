from __future__ import annotations

import sqlite3
from datetime import datetime

from Engines.Projects import Project, ProjectRepository, ProjectStatus
from Infrastructure.Persistence.database import SQLiteDatabase


class SQLiteProjectRepository(ProjectRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def store(self, project: Project) -> Project:
        with self._database.transaction() as connection:
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "title=excluded.title, "
                "client=excluded.client, "
                "address=excluded.address, "
                "description=excluded.description, "
                "status=excluded.status",
                (
                    project.id,
                    project.workspace_id,
                    project.title,
                    project.client,
                    project.address,
                    project.description,
                    project.status.value,
                    project.created_at.isoformat(),
                ),
            )
            connection.execute(
                "DELETE FROM project_missions WHERE project_id=?",
                (project.id,),
            )
            connection.executemany(
                "INSERT INTO project_missions VALUES (?, ?)",
                ((project.id, item) for item in project.mission_ids),
            )
        return project

    def get(self, project_id: str) -> Project | None:
        connection = self._database.connect()
        try:
            row = connection.execute(
                "SELECT * FROM projects WHERE id=?",
                (project_id,),
            ).fetchone()
            return self._model(connection, row) if row else None
        finally:
            connection.close()

    def list(self, workspace_id: str | None = None) -> tuple[Project, ...]:
        connection = self._database.connect()
        try:
            if workspace_id is None:
                rows = connection.execute(
                    "SELECT * FROM projects ORDER BY rowid"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM projects "
                    "WHERE workspace_id=? ORDER BY rowid",
                    (workspace_id,),
                ).fetchall()
            return tuple(self._model(connection, row) for row in rows)
        finally:
            connection.close()

    @staticmethod
    def _model(
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> Project:
        missions = connection.execute(
            "SELECT mission_id FROM project_missions "
            "WHERE project_id=? ORDER BY rowid",
            (row["id"],),
        ).fetchall()
        return Project(
            row["id"],
            row["workspace_id"],
            row["title"],
            row["client"],
            row["address"],
            row["description"],
            ProjectStatus(row["status"]),
            datetime.fromisoformat(row["created_at"]),
            tuple(item[0] for item in missions),
        )
