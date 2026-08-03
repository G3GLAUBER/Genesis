from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

from Core.result import Result
from Engines.Memory.models import (
    MemoryQuery,
    MemoryRecord,
    MemorySearchResult,
)
from Engines.Memory.repository import MemoryRepository


class MemoryEngine:
    def __init__(self, repository: MemoryRepository) -> None:
        if not isinstance(repository, MemoryRepository):
            raise TypeError("repository deve implementar MemoryRepository")
        self._repository = repository

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
        try:
            record = MemoryRecord(
                id=str(uuid4()),
                workspace_id=self._required_text(
                    workspace_id, "workspace_id"
                ),
                mission_id=self._optional_text(mission_id, "mission_id"),
                category=self._required_text(category, "category"),
                title=self._required_text(title, "title"),
                content=self._required_text(content, "content"),
                metadata=self._metadata(metadata),
                created_at=datetime.now(timezone.utc),
            )
        except (TypeError, ValueError) as error:
            return Result.error(message=f"Memória inválida: {error}")
        try:
            stored = self._repository.store(record)
        except Exception as error:
            return self._repository_error(error)
        return Result.success(message="Memória armazenada", data=stored)

    def search(self, query: MemoryQuery) -> Result:
        validation = self._validate_query(query)
        if validation is not None:
            return Result.error(message=f"Consulta inválida: {validation}")
        normalized = MemoryQuery(
            workspace_id=query.workspace_id.strip(),
            text=query.text.strip(),
            mission_id=self._optional_text(query.mission_id, "mission_id"),
            category=self._optional_text(query.category, "category"),
            limit=query.limit,
        )
        try:
            records = self._repository.search(normalized)
        except Exception as error:
            return self._repository_error(error)
        return Result.success(
            message="Busca de memória concluída",
            data=MemorySearchResult(
                query=normalized,
                records=records,
                total=len(records),
            ),
        )

    def history(
        self,
        *,
        workspace_id: str | None,
        mission_id: str | None = None,
    ) -> Result:
        try:
            workspace = self._required_text(workspace_id, "workspace_id")
            mission = self._optional_text(mission_id, "mission_id")
        except ValueError as error:
            return Result.error(message=f"Histórico inválido: {error}")
        try:
            records = self._repository.list(workspace, mission_id=mission)
        except Exception as error:
            return self._repository_error(error)
        return Result.success(message="Histórico de memória listado", data=records)

    def delete(
        self,
        *,
        workspace_id: str | None,
        record_id: str | None,
    ) -> Result:
        try:
            workspace = self._required_text(workspace_id, "workspace_id")
            record = self._required_text(record_id, "record_id")
        except ValueError as error:
            return Result.error(message=f"Exclusão inválida: {error}")
        try:
            deleted = self._repository.delete(workspace, record)
        except Exception as error:
            return self._repository_error(error)
        if not deleted:
            return Result.error(message="Memória não encontrada")
        return Result.success(message="Memória removida", data=record)

    def clear(self, *, workspace_id: str | None) -> Result:
        try:
            workspace = self._required_text(workspace_id, "workspace_id")
        except ValueError as error:
            return Result.error(message=f"Limpeza inválida: {error}")
        try:
            removed = self._repository.clear(workspace)
        except Exception as error:
            return self._repository_error(error)
        return Result.success(message="Memória do Workspace limpa", data=removed)

    @classmethod
    def _validate_query(cls, query: object) -> str | None:
        if not isinstance(query, MemoryQuery):
            return "query deve ser MemoryQuery"
        try:
            cls._required_text(query.workspace_id, "workspace_id")
            cls._required_text(query.text, "text", allow_empty=True)
            cls._optional_text(query.mission_id, "mission_id")
            cls._optional_text(query.category, "category")
        except ValueError as error:
            return str(error)
        if query.limit is not None and (
            not isinstance(query.limit, int)
            or isinstance(query.limit, bool)
            or query.limit < 1
        ):
            return "limit deve ser um inteiro positivo"
        return None

    @staticmethod
    def _required_text(
        value: object,
        field: str,
        *,
        allow_empty: bool = False,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field} deve ser texto")
        normalized = value.strip()
        if not normalized and not allow_empty:
            raise ValueError(f"{field} deve ser texto não vazio")
        return normalized

    @classmethod
    def _optional_text(cls, value: object, field: str) -> str | None:
        if value is None:
            return None
        return cls._required_text(value, field)

    @staticmethod
    def _metadata(value: object) -> Mapping[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("metadata deve ser um mapeamento")
        if any(not isinstance(key, str) or not key.strip() for key in value):
            raise ValueError("metadata deve possuir chaves textuais não vazias")
        return dict(value)

    @staticmethod
    def _repository_error(error: Exception) -> Result:
        return Result.error(
            message=(
                "Falha no repository de memória: "
                f"{type(error).__name__}"
            )
        )
