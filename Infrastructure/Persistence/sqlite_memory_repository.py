from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from Engines.Memory import MemoryQuery, MemoryRecord, MemoryRepository
from Infrastructure.Persistence.database import SQLiteDatabase


class SQLiteMemoryRepository(MemoryRepository):
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def store(self, record: MemoryRecord) -> MemoryRecord:
        with self._database.transaction() as connection:
            connection.execute(
                "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.id,
                    record.workspace_id,
                    record.mission_id,
                    record.category,
                    record.title,
                    record.content,
                    json.dumps(
                        dict(record.metadata),
                        sort_keys=True,
                        ensure_ascii=False,
                    ),
                    record.created_at.isoformat(),
                ),
            )
        return record

    def search(self, query: MemoryQuery) -> tuple[MemoryRecord, ...]:
        records = self.list(query.workspace_id, mission_id=query.mission_id)
        text = (query.text or "").casefold()
        matches = tuple(
            record
            for record in records
            if (
                query.category is None
                or record.category.casefold() == query.category.casefold()
            )
            and (
                not text
                or text in record.title.casefold()
                or text in record.content.casefold()
            )
        )
        return matches if query.limit is None else matches[: query.limit]

    def list(
        self,
        workspace_id: str,
        *,
        mission_id: str | None = None,
    ) -> tuple[MemoryRecord, ...]:
        connection = self._database.connect()
        try:
            sql = "SELECT * FROM memories WHERE workspace_id=?"
            params: tuple[str, ...] = (workspace_id,)
            if mission_id is not None:
                sql += " AND mission_id=?"
                params += (mission_id,)
            rows = connection.execute(sql + " ORDER BY rowid DESC", params).fetchall()
            return tuple(self._model(row) for row in rows)
        finally:
            connection.close()

    def delete(self, workspace_id: str, record_id: str) -> bool:
        with self._database.transaction() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE workspace_id=? AND id=?",
                (workspace_id, record_id),
            )
            return cursor.rowcount > 0

    def clear(self, workspace_id: str) -> int:
        with self._database.transaction() as connection:
            return connection.execute(
                "DELETE FROM memories WHERE workspace_id=?",
                (workspace_id,),
            ).rowcount

    @staticmethod
    def _model(row: sqlite3.Row) -> MemoryRecord:
        metadata: dict[str, Any] = json.loads(row["metadata"])
        return MemoryRecord(
            row["id"],
            row["workspace_id"],
            row["mission_id"],
            row["category"],
            row["title"],
            row["content"],
            metadata,
            datetime.fromisoformat(row["created_at"]),
        )
