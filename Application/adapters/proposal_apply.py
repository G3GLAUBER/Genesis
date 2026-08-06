from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from Application.services.memory_service import MemoryService
from Application.services.mission_service import MissionApplicationService
from Application.services.project_service import ProjectService
from Application.services.workspace_service import WorkspaceApplicationService
from Core.result import Result
from Engines.Proposal.models import Proposal, ProposalAction, ProposalChange


@dataclass(frozen=True)
class ApplyExecution:
    """Safe, structured evidence returned by one concrete adapter."""

    change_id: str
    resource_type: str
    resource_id: str
    message: str


class ProposalChangeAdapter(Protocol):
    def supports(self, change: ProposalChange) -> bool: ...

    def execute(self, proposal: Proposal, change: ProposalChange) -> Result: ...


def _payload(change: ProposalChange) -> Mapping[str, Any] | None:
    if not isinstance(change.after, Mapping):
        return None
    return change.after


def _required_text(payload: Mapping[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


class MissionProposalAdapter:
    def __init__(
        self,
        mission_service: MissionApplicationService,
        workspace_service: WorkspaceApplicationService,
        project_service: ProjectService,
    ) -> None:
        self._missions = mission_service
        self._workspaces = workspace_service
        self._projects = project_service

    def supports(self, change: ProposalChange) -> bool:
        return (
            change.action is ProposalAction.CREATE
            and change.target_type == "mission"
        )

    def execute(self, proposal: Proposal, change: ProposalChange) -> Result:
        payload = _payload(change)
        if payload is None:
            return Result.error(message="Mission change exige payload after")
        workspace_id = payload.get("workspace_id", proposal.workspace_id)
        if workspace_id != proposal.workspace_id:
            return Result.error(message="Mission change referencia outro Workspace")
        title = _required_text(payload, "title")
        objective = _required_text(payload, "objective")
        if title is None or objective is None:
            return Result.error(
                message="Mission change exige title e objective"
            )
        project_id = payload.get("project_id", proposal.project_id)
        if project_id is not None:
            project = self._projects.get(project_id)
            if not project.is_success:
                return project
            if project.data.workspace_id != proposal.workspace_id:
                return Result.error(
                    message="Projeto da Mission pertence a outro Workspace"
                )
        created = self._missions.create_mission(
            title=title,
            objective=objective,
            source=f"Proposal:{proposal.id}",
            constraints=payload.get("constraints", ()),
            success_criteria=payload.get("success_criteria", ()),
        )
        if not created.is_success:
            return created
        associated_workspace = self._workspaces.associate_mission(
            proposal.workspace_id,
            mission_id=created.data.id,
        )
        if not associated_workspace.is_success:
            return Result.error(
                message=(
                    "Mission criada, mas não foi associada ao Workspace: "
                    f"{associated_workspace.message}"
                ),
                data=created.data,
            )
        if project_id is not None:
            associated_project = self._projects.attach_mission(
                project_id,
                mission_id=created.data.id,
            )
            if not associated_project.is_success:
                return Result.error(
                    message=(
                        "Mission criada, mas não foi associada ao Project: "
                        f"{associated_project.message}"
                    ),
                    data=created.data,
                )
        return Result.success(
            message="Mission criada e associada",
            data=ApplyExecution(
                change_id=change.id,
                resource_type="mission",
                resource_id=created.data.id,
                message="Mission criada e associada ao Workspace",
            ),
        )


class ProjectMissionProposalAdapter:
    def __init__(
        self,
        project_service: ProjectService,
        workspace_service: WorkspaceApplicationService,
        mission_service: MissionApplicationService | None = None,
    ) -> None:
        self._projects = project_service
        self._workspaces = workspace_service
        self._missions = mission_service

    def supports(self, change: ProposalChange) -> bool:
        return (
            change.action is ProposalAction.ASSOCIATE
            and change.target_type in {"project_mission", "mission_project"}
        )

    def execute(self, proposal: Proposal, change: ProposalChange) -> Result:
        payload = _payload(change)
        if payload is None:
            return Result.error(message="Association change exige payload after")
        project_id = change.target_id or payload.get("project_id")
        mission_id = payload.get("mission_id")
        if not isinstance(project_id, str) or not project_id.strip():
            return Result.error(message="Association exige project_id")
        if not isinstance(mission_id, str) or not mission_id.strip():
            return Result.error(message="Association exige mission_id")
        project = self._projects.get(project_id)
        if not project.is_success:
            return project
        if project.data.workspace_id != proposal.workspace_id:
            return Result.error(message="Projeto pertence a outro Workspace")
        workspace_id = payload.get("workspace_id", proposal.workspace_id)
        if workspace_id != proposal.workspace_id:
            return Result.error(message="Association referencia outro Workspace")
        workspace = self._workspaces.get(proposal.workspace_id)
        if not workspace.is_success:
            return workspace
        if self._missions is not None:
            missions = self._missions.list_missions(
                workspace_id=proposal.workspace_id,
            )
            if not missions.is_success:
                return missions
            if not any(mission.id == mission_id for mission in missions.data):
                return Result.error(
                    message="Mission não pertence ao Workspace da Proposal"
                )
        associated = self._projects.attach_mission(
            project_id,
            mission_id=mission_id,
        )
        if not associated.is_success:
            return associated
        return Result.success(
            message="Mission associada ao Project",
            data=ApplyExecution(
                change_id=change.id,
                resource_type="project",
                resource_id=project_id,
                message=f"Mission {mission_id} associada ao Project",
            ),
        )


class MemoryProposalAdapter:
    def __init__(
        self,
        memory_service: MemoryService,
        mission_service: MissionApplicationService | None = None,
    ) -> None:
        self._memory = memory_service
        self._missions = mission_service

    def supports(self, change: ProposalChange) -> bool:
        return (
            change.action is ProposalAction.CREATE
            and change.target_type == "memory"
        )

    def execute(self, proposal: Proposal, change: ProposalChange) -> Result:
        payload = _payload(change)
        if payload is None:
            return Result.error(message="Memory change exige payload after")
        workspace_id = payload.get("workspace_id", proposal.workspace_id)
        if workspace_id != proposal.workspace_id:
            return Result.error(message="Memory change referencia outro Workspace")
        mission_id = payload.get("mission_id", proposal.mission_id)
        if mission_id is not None and self._missions is not None:
            missions = self._missions.list_missions(
                workspace_id=proposal.workspace_id,
            )
            if not missions.is_success:
                return missions
            if not any(mission.id == mission_id for mission in missions.data):
                return Result.error(
                    message="Mission da Memory não pertence ao Workspace da Proposal"
                )
        category = _required_text(payload, "category")
        title = _required_text(payload, "title")
        content = _required_text(payload, "content")
        if category is None or title is None or content is None:
            return Result.error(
                message="Memory change exige category, title e content"
            )
        stored = self._memory.store(
            workspace_id=proposal.workspace_id,
            mission_id=mission_id,
            category=category,
            title=title,
            content=content,
            metadata={
                "proposal_id": proposal.id,
                "proposal_version": proposal.version,
                "project_id": proposal.project_id,
            },
        )
        if not stored.is_success:
            return stored
        return Result.success(
            message="Memory criada",
            data=ApplyExecution(
                change_id=change.id,
                resource_type="memory",
                resource_id=stored.data.id,
                message="Memory armazenada no Workspace",
            ),
        )


__all__ = [
    "ApplyExecution",
    "MemoryProposalAdapter",
    "MissionProposalAdapter",
    "ProjectMissionProposalAdapter",
    "ProposalChangeAdapter",
]
