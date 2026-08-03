from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from Core.result import Result
from Engines.Intelligence.models import HandoffStatus, ManualHandoff


class ManualHandoffManager:
    def __init__(self) -> None:
        self._items: dict[str, ManualHandoff] = {}
        self._lock = RLock()

    def create(
        self,
        *,
        provider_id: str | None,
        prompt: str | None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        mission_id: str | None = None,
    ) -> Result:
        try:
            handoff = ManualHandoff(
                id=str(uuid4()),
                provider_id=self._required(provider_id, "provider_id"),
                prompt=self._required(prompt, "prompt"),
                status=HandoffStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                workspace_id=self._optional(workspace_id),
                project_id=self._optional(project_id),
                mission_id=self._optional(mission_id),
            )
        except ValueError as error:
            return Result.error(message=f"ManualHandoff inválido: {error}")
        with self._lock:
            self._items[handoff.id] = handoff
        return Result.success(message="ManualHandoff criado", data=handoff)

    def complete(self, handoff_id: str | None, *, response: str | None) -> Result:
        normalized_id = self._optional(handoff_id)
        with self._lock:
            current = self._items.get(normalized_id or "")
            if current is None:
                return Result.error(message="ManualHandoff não encontrado")
            if current.status is HandoffStatus.COMPLETED:
                return Result.error(message="ManualHandoff já concluído")
            try:
                content = self._required(response, "response")
            except ValueError as error:
                return Result.error(message=f"Resposta inválida: {error}")
            completed = replace(
                current,
                status=HandoffStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                response=content,
            )
            self._items[current.id] = completed
        return Result.success(message="ManualHandoff concluído", data=completed)

    def list(self) -> tuple[ManualHandoff, ...]:
        with self._lock:
            return tuple(self._items.values())

    @staticmethod
    def _required(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve ser texto não vazio")
        return value.strip()

    @staticmethod
    def _optional(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None
