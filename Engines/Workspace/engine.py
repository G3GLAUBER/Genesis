from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from Core.result import Result
from Engines.Workspace.models import Workspace, WorkspaceStatus


class WorkspaceEngine:
    def create(
        self,
        *,
        name: str | None = None,
        description: str | None = "",
    ) -> Result:
        try:
            normalized_name = self._normalize_required_text(name, "name")
            normalized_description = self._normalize_description(description)
        except ValueError as error:
            return Result.error(message=f"Workspace inválido: {error}")

        workspace = Workspace(
            id=str(uuid4()),
            name=normalized_name,
            description=normalized_description,
            created_at=datetime.now(timezone.utc),
            status=WorkspaceStatus.ACTIVE,
        )
        return Result.success(message="Workspace criado", data=workspace)

    def rename(self, *, workspace: Workspace, name: str | None) -> Result:
        error = self._validate_active(workspace)
        if error is not None:
            return error
        try:
            normalized_name = self._normalize_required_text(name, "name")
        except ValueError as validation_error:
            return Result.error(
                message=f"Workspace inválido: {validation_error}"
            )
        return Result.success(
            message="Workspace renomeado",
            data=replace(workspace, name=normalized_name),
        )

    def archive(self, *, workspace: Workspace) -> Result:
        error = self._validate_workspace(workspace)
        if error is not None:
            return error
        if workspace.status is WorkspaceStatus.ARCHIVED:
            return Result.error(message="Workspace já está arquivado")
        return Result.success(
            message="Workspace arquivado",
            data=replace(workspace, status=WorkspaceStatus.ARCHIVED),
        )

    def restore(self, *, workspace: Workspace) -> Result:
        error = self._validate_workspace(workspace)
        if error is not None:
            return error
        if workspace.status is WorkspaceStatus.ACTIVE:
            return Result.error(message="Workspace já está ativo")
        return Result.success(
            message="Workspace restaurado",
            data=replace(workspace, status=WorkspaceStatus.ACTIVE),
        )

    def add_mission(
        self,
        *,
        workspace: Workspace,
        mission_id: str | None,
    ) -> Result:
        error = self._validate_active(workspace)
        if error is not None:
            return error
        try:
            normalized_id = self._normalize_required_text(
                mission_id,
                "mission_id",
            )
        except ValueError as validation_error:
            return Result.error(
                message=f"Workspace inválido: {validation_error}"
            )
        if normalized_id in workspace.mission_ids:
            return Result.error(message="Missão já associada ao Workspace")
        return Result.success(
            message="Missão associada ao Workspace",
            data=replace(
                workspace,
                mission_ids=workspace.mission_ids + (normalized_id,),
            ),
        )

    def remove_mission(
        self,
        *,
        workspace: Workspace,
        mission_id: str | None,
    ) -> Result:
        error = self._validate_active(workspace)
        if error is not None:
            return error
        try:
            normalized_id = self._normalize_required_text(
                mission_id,
                "mission_id",
            )
        except ValueError as validation_error:
            return Result.error(
                message=f"Workspace inválido: {validation_error}"
            )
        if normalized_id not in workspace.mission_ids:
            return Result.error(message="Missão não associada ao Workspace")
        return Result.success(
            message="Missão removida do Workspace",
            data=replace(
                workspace,
                mission_ids=tuple(
                    item
                    for item in workspace.mission_ids
                    if item != normalized_id
                ),
            ),
        )

    @staticmethod
    def _normalize_required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve ser um texto não vazio")
        return value.strip()

    @staticmethod
    def _normalize_description(value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("description deve ser um texto")
        return value.strip()

    @staticmethod
    def _validate_workspace(workspace: object) -> Result | None:
        if not isinstance(workspace, Workspace):
            return Result.error(message="Workspace inválido")
        return None

    @classmethod
    def _validate_active(cls, workspace: object) -> Result | None:
        error = cls._validate_workspace(workspace)
        if error is not None:
            return error
        if workspace.status is WorkspaceStatus.ARCHIVED:
            return Result.error(message="Workspace está arquivado")
        return None
