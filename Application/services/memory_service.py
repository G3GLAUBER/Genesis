from __future__ import annotations

from typing import Any, Mapping

from Core.result import Result
from Engines.Memory import MemoryEngine, MemoryQuery


class MemoryService:
    def __init__(self, engine: MemoryEngine) -> None:
        self._engine = engine

    def store(
        self,
        *,
        workspace_id: str | None,
        category: str | None,
        title: str | None,
        content: str | None,
        mission_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Result:
        return self._engine.store(
            workspace_id=workspace_id,
            mission_id=mission_id,
            category=category,
            title=title,
            content=content,
            metadata=metadata,
        )

    def search(
        self,
        *,
        workspace_id: str | None,
        text: str | None = "",
        mission_id: str | None = None,
        category: str | None = None,
        limit: int | None = None,
    ) -> Result:
        return self._engine.search(
            MemoryQuery(
                workspace_id=workspace_id,
                text=text,
                mission_id=mission_id,
                category=category,
                limit=limit,
            )
        )

    def history(
        self,
        *,
        workspace_id: str | None,
        mission_id: str | None = None,
    ) -> Result:
        return self._engine.history(
            workspace_id=workspace_id,
            mission_id=mission_id,
        )

    def delete(
        self,
        *,
        workspace_id: str | None,
        record_id: str | None,
    ) -> Result:
        return self._engine.delete(
            workspace_id=workspace_id,
            record_id=record_id,
        )

    def clear(self, *, workspace_id: str | None) -> Result:
        return self._engine.clear(workspace_id=workspace_id)
