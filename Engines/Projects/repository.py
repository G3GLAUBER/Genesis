from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from Engines.Projects.models import Project


class ProjectRepository(ABC):
    @abstractmethod
    def store(self, project: Project) -> Project:
        """Armazena um projeto e retorna o valor armazenado."""

    @abstractmethod
    def get(self, project_id: str) -> Project | None:
        """Obtém um projeto pelo identificador."""

    @abstractmethod
    def list(self, workspace_id: str | None = None) -> tuple[Project, ...]:
        """Lista projetos em ordem de criação, opcionalmente por Workspace."""


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}
        self._lock = RLock()

    def store(self, project: Project) -> Project:
        with self._lock:
            self._projects[project.id] = project
            return project

    def get(self, project_id: str) -> Project | None:
        with self._lock:
            return self._projects.get(project_id)

    def list(self, workspace_id: str | None = None) -> tuple[Project, ...]:
        with self._lock:
            return tuple(
                project
                for project in self._projects.values()
                if workspace_id is None
                or project.workspace_id == workspace_id
            )

