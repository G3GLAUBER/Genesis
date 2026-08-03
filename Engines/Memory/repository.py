from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from Engines.Memory.models import MemoryQuery, MemoryRecord


class MemoryRepository(ABC):
    @abstractmethod
    def store(self, record: MemoryRecord) -> MemoryRecord:
        """Armazena um registro e retorna o valor armazenado."""

    @abstractmethod
    def search(self, query: MemoryQuery) -> tuple[MemoryRecord, ...]:
        """Pesquisa registros respeitando o isolamento da consulta."""

    @abstractmethod
    def list(
        self,
        workspace_id: str,
        *,
        mission_id: str | None = None,
    ) -> tuple[MemoryRecord, ...]:
        """Lista o histórico isolado por Workspace e missão opcional."""

    @abstractmethod
    def delete(self, workspace_id: str, record_id: str) -> bool:
        """Remove um registro do Workspace e informa se ele existia."""

    @abstractmethod
    def clear(self, workspace_id: str) -> int:
        """Remove os registros do Workspace e retorna a quantidade removida."""


class InMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._lock = RLock()

    def store(self, record: MemoryRecord) -> MemoryRecord:
        with self._lock:
            self._records[record.id] = record
            return record

    def search(self, query: MemoryQuery) -> tuple[MemoryRecord, ...]:
        text = (query.text or "").casefold()
        with self._lock:
            matches = tuple(
                record
                for record in reversed(tuple(self._records.values()))
                if record.workspace_id == query.workspace_id
                and (
                    query.mission_id is None
                    or record.mission_id == query.mission_id
                )
                and (
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
        with self._lock:
            return tuple(
                record
                for record in reversed(tuple(self._records.values()))
                if record.workspace_id == workspace_id
                and (mission_id is None or record.mission_id == mission_id)
            )

    def delete(self, workspace_id: str, record_id: str) -> bool:
        with self._lock:
            record = self._records.get(record_id)
            if record is None or record.workspace_id != workspace_id:
                return False
            del self._records[record_id]
            return True

    def clear(self, workspace_id: str) -> int:
        with self._lock:
            record_ids = tuple(
                record.id
                for record in self._records.values()
                if record.workspace_id == workspace_id
            )
            for record_id in record_ids:
                del self._records[record_id]
            return len(record_ids)
