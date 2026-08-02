from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import uuid4

from Core.result import Result
from Engines.Mission.models import Mission, MissionStatus


class MissionEngine:
    def create(
        self,
        *,
        title: str | None = None,
        objective: str | None = None,
        source: str | None = None,
        constraints: Iterable[str] | str | None = (),
        success_criteria: Iterable[str] | str | None = (),
    ) -> Result:
        try:
            normalized_title = self._normalize_required_text(title, "title")
            normalized_objective = self._normalize_required_text(
                objective,
                "objective",
            )
            normalized_source = self._normalize_required_text(source, "source")
            normalized_constraints = self._normalize_items(
                constraints,
                "constraints",
            )
            normalized_criteria = self._normalize_items(
                success_criteria,
                "success_criteria",
            )
        except (TypeError, ValueError) as error:
            return Result.error(message=f"Missão inválida: {error}")

        mission = Mission(
            id=str(uuid4()),
            title=normalized_title,
            objective=normalized_objective,
            status=MissionStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            constraints=normalized_constraints,
            success_criteria=normalized_criteria,
            source=normalized_source,
        )
        return Result.success(message="Missão criada", data=mission)

    @staticmethod
    def _normalize_required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve ser um texto não vazio")
        return value.strip()

    @classmethod
    def _normalize_items(
        cls,
        values: Iterable[str] | str | None,
        field: str,
    ) -> tuple[str, ...]:
        if isinstance(values, str):
            values = (values,)

        try:
            items = tuple(values)
        except TypeError as error:
            raise ValueError(f"{field} deve ser uma coleção de textos") from error

        return tuple(
            cls._normalize_required_text(item, field)
            for item in items
        )
