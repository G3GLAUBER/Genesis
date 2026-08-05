from __future__ import annotations

from Application.services.mission_copilot_service import (
    MissionCopilotApplicationService,
)
from Application.services.mission_service import MissionApplicationService
from Application.services.project_service import ProjectService
from Application.services.remodeling_service import RemodelingApplicationService
from Core.result import Result
from Engines.Execution import ExecutionStatus
from Engines.Remodeling import ProposalStatus
from Engines.Workflow import WorkflowEngine, WorkflowObservation


class WorkflowApplicationService:
    """Compose existing evidence and delegate guidance to WorkflowEngine."""

    def __init__(
        self,
        engine: WorkflowEngine,
        project_service: ProjectService,
        mission_service: MissionApplicationService,
        *,
        mission_copilot_service: MissionCopilotApplicationService | None = None,
        remodeling_service: RemodelingApplicationService | None = None,
    ) -> None:
        self._engine = engine
        self._projects = project_service
        self._missions = mission_service
        self._mission_copilot = mission_copilot_service
        self._remodeling = remodeling_service

    def evaluate_project(self, project_id: str | None) -> Result:
        project_result = self._projects.get(project_id)
        if not project_result.is_success:
            return project_result
        project = project_result.data
        mission_ids = tuple(project.mission_ids)

        copilot_completed = False
        if self._mission_copilot is not None:
            copilot_completed = any(
                self._mission_copilot.get_result_for_mission(mission_id).is_success
                for mission_id in mission_ids
            )

        proposal_pending = False
        proposal_approved = False
        if self._remodeling is not None:
            briefs_result = self._remodeling.list_briefs()
            proposals_result = self._remodeling.list_proposals()
            briefs = briefs_result.data if briefs_result.is_success else ()
            proposals = (
                proposals_result.data if proposals_result.is_success else ()
            )
            brief_ids = {
                brief.id for brief in briefs if brief.project_id == project.id
            }
            related = tuple(
                proposal
                for proposal in proposals
                if proposal.brief_id in brief_ids
            )
            proposal_approved = any(
                proposal.status in (ProposalStatus.APPROVED, ProposalStatus.APPLIED)
                for proposal in related
            )
            proposal_pending = any(
                proposal.status
                in (
                    ProposalStatus.DRAFT,
                    ProposalStatus.GENERATED,
                    ProposalStatus.REVIEWED,
                )
                for proposal in related
            )

        executions_result = self._missions.list_executions(
            workspace_id=project.workspace_id
        )
        executions = executions_result.data if executions_result.is_success else ()
        related_executions = tuple(
            execution
            for execution in executions
            if execution.mission.id in mission_ids
        )
        execution_pending = any(
            execution.report.status is not ExecutionStatus.COMPLETED
            for execution in related_executions
        )
        execution_completed = bool(related_executions) and all(
            execution.report.status is ExecutionStatus.COMPLETED
            for execution in related_executions
        )
        blockers = (
            ("A última Execution não foi concluída.",)
            if execution_pending
            else ()
        )
        # v0.1 has no public Application contract that exposes a Planning
        # independently of an Execution. Plans are currently created inside
        # MissionApplicationService and retained only by execution records;
        # inferring readiness here would manufacture Workflow evidence.
        planning_ready = False
        observation = WorkflowObservation(
            project_id=project.id,
            project_title=project.title,
            mission_ids=mission_ids,
            mission_copilot_completed=copilot_completed,
            proposal_pending=proposal_pending,
            proposal_approved=proposal_approved,
            planning_ready=planning_ready,
            execution_pending=execution_pending,
            execution_completed=execution_completed,
            project_completed=project.status.value == "completed",
            blockers=blockers,
        )
        return self._engine.evaluate(observation)

    def list_for_workspace(self, workspace_id: str | None) -> Result:
        projects_result = self._projects.list(workspace_id=workspace_id)
        if not projects_result.is_success:
            return projects_result
        states = []
        for project in projects_result.data:
            state = self.evaluate_project(project.id)
            if not state.is_success:
                return state
            states.append(state.data)
        return Result.success(
            message="Workflows do Workspace listados",
            data=tuple(states),
        )
