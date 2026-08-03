from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from Core.result import Result
from Engines.Projects.models import Project, ProjectStatus
from Engines.Projects.repository import ProjectRepository


class ProjectEngine:
    def __init__(self, repository: ProjectRepository) -> None:
        if not isinstance(repository, ProjectRepository):
            raise TypeError("repository deve implementar ProjectRepository")
        self._repository = repository

    def create(
        self,
        *,
        workspace_id: str | None,
        title: str | None,
        client: str | None,
        address: str | None,
        description: str | None = "",
    ) -> Result:
        try:
            project = Project(
                id=str(uuid4()),
                workspace_id=self._required_text(
                    workspace_id, "workspace_id"
                ),
                title=self._required_text(title, "title"),
                client=self._required_text(client, "client"),
                address=self._required_text(address, "address"),
                description=self._description(description),
                status=ProjectStatus.PLANNING,
                created_at=datetime.now(timezone.utc),
            )
        except ValueError as error:
            return Result.error(message=f"Projeto inválido: {error}")
        return self._store(project, "Projeto criado")

    def list(
        self,
        *,
        workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> Result:
        try:
            workspace = self._optional_text(workspace_id, "workspace_id")
        except ValueError as error:
            return Result.error(message=f"Listagem inválida: {error}")
        try:
            projects = self._repository.list(workspace)
        except Exception as error:
            return self._repository_error(error)
        visible = tuple(
            project
            for project in projects
            if include_archived or project.status is not ProjectStatus.ARCHIVED
        )
        return Result.success(message="Projetos listados", data=visible)

    def get(self, project_id: str | None) -> Result:
        try:
            normalized_id = self._required_text(project_id, "project_id")
            project = self._repository.get(normalized_id)
        except ValueError as error:
            return Result.error(message=f"Consulta inválida: {error}")
        except Exception as error:
            return self._repository_error(error)
        if project is None:
            return Result.error(message="Projeto não encontrado")
        return Result.success(message="Projeto encontrado", data=project)

    def archive(self, project_id: str | None) -> Result:
        current = self.get(project_id)
        if not current.is_success:
            return current
        if current.data.status is ProjectStatus.ARCHIVED:
            return Result.error(message="Projeto já está arquivado")
        return self._store(
            replace(current.data, status=ProjectStatus.ARCHIVED),
            "Projeto arquivado",
        )

    def restore(self, project_id: str | None) -> Result:
        current = self.get(project_id)
        if not current.is_success:
            return current
        if current.data.status is not ProjectStatus.ARCHIVED:
            return Result.error(message="Projeto não está arquivado")
        return self._store(
            replace(current.data, status=ProjectStatus.ACTIVE),
            "Projeto restaurado",
        )

    def attach_mission(
        self,
        project_id: str | None,
        *,
        mission_id: str | None,
    ) -> Result:
        current = self.get(project_id)
        if not current.is_success:
            return current
        if current.data.status is ProjectStatus.ARCHIVED:
            return Result.error(
                message="Projeto arquivado não aceita novas missões"
            )
        try:
            normalized_id = self._required_text(mission_id, "mission_id")
        except ValueError as error:
            return Result.error(message=f"Associação inválida: {error}")
        if normalized_id in current.data.mission_ids:
            return Result.error(message="Missão já associada ao Projeto")
        return self._store(
            replace(
                current.data,
                mission_ids=current.data.mission_ids + (normalized_id,),
            ),
            "Missão associada ao Projeto",
        )

    def _store(self, project: Project, message: str) -> Result:
        try:
            stored = self._repository.store(project)
        except Exception as error:
            return self._repository_error(error)
        return Result.success(message=message, data=stored)

    @staticmethod
    def _required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve ser texto não vazio")
        return value.strip()

    @classmethod
    def _optional_text(cls, value: object, field: str) -> str | None:
        if value is None:
            return None
        return cls._required_text(value, field)

    @staticmethod
    def _description(value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("description deve ser texto")
        return value.strip()

    @staticmethod
    def _repository_error(error: Exception) -> Result:
        return Result.error(
            message=(
                "Falha no repository de projetos: "
                f"{type(error).__name__}"
            )
        )
