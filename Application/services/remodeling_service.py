from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from threading import RLock

from Application.services.intelligence_service import IntelligenceApplicationService
from Application.services.memory_service import MemoryService
from Application.services.mission_service import MissionApplicationService
from Application.services.project_service import ProjectService
from Application.services.workspace_service import WorkspaceApplicationService
from Core.result import Result
from Engines.Intelligence import ManualHandoff, RoutingDecision, RoutingMode
from Engines.Remodeling import (
    ProposalStatus,
    RemodelingBrief,
    RemodelingEngine,
    RemodelingProposal,
)


@dataclass(frozen=True)
class RemodelingProposalRequest:
    brief: RemodelingBrief
    decision: RoutingDecision
    handoff: ManualHandoff
    status: ProposalStatus = ProposalStatus.DRAFT


@dataclass(frozen=True)
class RemodelingApplicationReport:
    proposal_id: str
    workspace_id: str
    project_id: str
    mission_ids: tuple[str, ...]
    memory_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "mission_ids", tuple(self.mission_ids))
        object.__setattr__(self, "memory_ids", tuple(self.memory_ids))


class RemodelingApplicationService:
    def __init__(
        self,
        engine: RemodelingEngine,
        intelligence_service: IntelligenceApplicationService,
        mission_service: MissionApplicationService,
        project_service: ProjectService,
        memory_service: MemoryService,
        workspace_service: WorkspaceApplicationService,
    ) -> None:
        self._engine = engine
        self._intelligence = intelligence_service
        self._missions = mission_service
        self._projects = project_service
        self._memory = memory_service
        self._workspaces = workspace_service
        self._requests: dict[str, RemodelingProposalRequest] = {}
        self._reports: dict[str, RemodelingApplicationReport] = {}
        self._lock = RLock()

    def create_brief(
        self,
        *,
        project_id: str | None,
        workspace_id: str | None,
        project_type: str | None,
        room_length: object = None,
        room_width: object = None,
        room_height: object = None,
        current_condition: str | None,
        desired_result: str | None,
        budget_limit: object = None,
        deadline: date | str | None = None,
        constraints=(),
        client_preferences=(),
        known_materials=(),
        notes: str | None = "",
    ) -> Result:
        workspace = self._workspaces.get(workspace_id)
        if not workspace.is_success:
            return workspace
        project = self._projects.get(project_id)
        if not project.is_success:
            return project
        if project.data.workspace_id != workspace.data.id:
            return Result.error(message="Projeto não pertence ao Workspace informado")
        return self._engine.create_brief(
            project_id=project.data.id,
            workspace_id=workspace.data.id,
            project_type=project_type,
            room_length=room_length,
            room_width=room_width,
            room_height=room_height,
            current_condition=current_condition,
            desired_result=desired_result,
            budget_limit=budget_limit,
            deadline=deadline,
            constraints=constraints,
            client_preferences=client_preferences,
            known_materials=known_materials,
            notes=notes,
        )

    def validate_brief(self, brief: object) -> Result:
        return self._engine.validate_brief(brief)

    def identify_missing_information(self, brief_id: str | None) -> Result:
        brief = self._engine.get_brief(brief_id)
        if not brief.is_success:
            return brief
        return self._engine.identify_missing_information(brief.data)

    def request_proposal(self, brief_id: str | None) -> Result:
        brief_result = self._engine.get_brief(brief_id)
        if not brief_result.is_success:
            return brief_result
        brief = brief_result.data
        prompt = self._proposal_prompt(brief)
        routed = self._intelligence.route(
            prompt=prompt,
            capability="general_assistance",
            mode=RoutingMode.FREE_ONLY,
        )
        if not routed.is_success:
            return routed
        decision = routed.data
        if not decision.requires_manual_handoff:
            return Result.error(
                message="Remodeling v0.1 requer provider manual em FREE_ONLY"
            )
        handoff = self._intelligence.create_manual_handoff(
            provider_id=decision.selected_provider_id,
            prompt=decision.prompt,
            workspace_id=brief.workspace_id,
            project_id=brief.project_id,
        )
        if not handoff.is_success:
            return handoff
        request = RemodelingProposalRequest(
            brief=brief,
            decision=decision,
            handoff=handoff.data,
        )
        with self._lock:
            self._requests[handoff.data.id] = request
        return Result.success(message="Handoff de remodelação criado", data=request)

    def complete_handoff(
        self,
        handoff_id: str | None,
        *,
        response: str | None,
    ) -> Result:
        with self._lock:
            request = self._requests.get(handoff_id or "")
        if request is None:
            return Result.error(message="Handoff de remodelação não encontrado")
        return self._intelligence.complete_manual_handoff(
            handoff_id,
            response=response,
            save_as_memory=False,
        )

    def build_proposal(self, handoff_id: str | None) -> Result:
        with self._lock:
            request = self._requests.get(handoff_id or "")
        if request is None:
            return Result.error(message="Handoff de remodelação não encontrado")
        handoffs = self._intelligence.list_manual_handoffs()
        if not handoffs.is_success:
            return handoffs
        handoff = next(
            (item for item in handoffs.data if item.id == handoff_id), None
        )
        if handoff is None or handoff.response is None:
            return Result.error(message="Handoff ainda não foi concluído")
        return self._engine.build_proposal(
            brief=request.brief,
            raw_response=handoff.response,
            provider_id=request.decision.selected_provider_id,
            routing_reason=request.decision.reason,
            alternatives=request.decision.alternatives,
        )

    def get_proposal(self, proposal_id: str | None) -> Result:
        return self._engine.get_proposal(proposal_id)

    def list_briefs(self) -> Result:
        return Result.success(message="Briefs listados", data=self._engine.list_briefs())

    def list_proposals(self) -> Result:
        return Result.success(
            message="Propostas listadas", data=self._engine.list_proposals()
        )

    def review_proposal(self, proposal_id: str | None) -> Result:
        return self._engine.transition(proposal_id, ProposalStatus.REVIEWED)

    def approve_proposal(self, proposal_id: str | None) -> Result:
        return self._engine.transition(proposal_id, ProposalStatus.APPROVED)

    def reject_proposal(self, proposal_id: str | None) -> Result:
        return self._engine.transition(proposal_id, ProposalStatus.REJECTED)

    def apply_proposal(self, proposal_id: str | None) -> Result:
        with self._lock:
            return self._apply_proposal_locked(proposal_id)

    def _apply_proposal_locked(self, proposal_id: str | None) -> Result:
        proposal_result = self._engine.get_proposal(proposal_id)
        if not proposal_result.is_success:
            return proposal_result
        proposal: RemodelingProposal = proposal_result.data
        if proposal.status is ProposalStatus.APPLIED:
            return Result.error(message="Proposta já foi aplicada")
        if proposal.status is not ProposalStatus.APPROVED:
            return Result.error(message="Somente proposta aprovada pode ser aplicada")
        if proposal.id in self._reports:
            return Result.error(message="Proposta já foi aplicada")
        brief = self._engine.get_brief(proposal.brief_id).data
        mission_ids: list[str] = []
        memory_ids: list[str] = []
        for suggestion in proposal.suggested_missions:
            created = self._missions.create_mission(
                title=suggestion.title,
                objective=suggestion.objective,
                source=f"RemodelingProposal:{proposal.id}",
            )
            if not created.is_success:
                return created
            associated_workspace = self._workspaces.associate_mission(
                brief.workspace_id, mission_id=created.data.id
            )
            if not associated_workspace.is_success:
                return associated_workspace
            associated_project = self._projects.attach_mission(
                brief.project_id, mission_id=created.data.id
            )
            if not associated_project.is_success:
                return associated_project
            mission_ids.append(created.data.id)
        memories = (
            *proposal.suggested_memories,
            _audit_memory(proposal),
        )
        for suggestion in memories:
            stored = self._memory.store(
                workspace_id=brief.workspace_id,
                category=suggestion.category,
                title=suggestion.title,
                content=suggestion.content,
                metadata={
                    "proposal_id": proposal.id,
                    "project_id": brief.project_id,
                    "preliminary": True,
                },
            )
            if not stored.is_success:
                return stored
            memory_ids.append(stored.data.id)
        applied = self._engine.transition(proposal.id, ProposalStatus.APPLIED)
        if not applied.is_success:
            return applied
        report = RemodelingApplicationReport(
            proposal_id=proposal.id,
            workspace_id=brief.workspace_id,
            project_id=brief.project_id,
            mission_ids=tuple(mission_ids),
            memory_ids=tuple(memory_ids),
        )
        self._reports[proposal.id] = report
        return Result.success(message="Proposta aplicada", data=report)

    def _proposal_prompt(self, brief: RemodelingBrief) -> str:
        missing = self._engine.identify_missing_information(brief).data
        return (
            "Prepare uma proposta preliminar de remodelação em JSON estrito. "
            "Não apresente valores como preços finais.\n"
            f"Project type: {brief.project_type}\n"
            f"Dimensions: {brief.room_length} x {brief.room_width} x {brief.room_height} m\n"
            f"Current condition: {brief.current_condition}\n"
            f"Desired result: {brief.desired_result}\n"
            f"Budget limit: {brief.budget_limit or 'não informado'} EUR\n"
            f"Deadline: {brief.deadline or 'não informado'}\n"
            f"Constraints: {list(brief.constraints)}\n"
            f"Preferences: {list(brief.client_preferences)}\n"
            f"Known materials: {list(brief.known_materials)}\n"
            f"Known gaps: {list(missing)}\n"
            "Retorne somente um objeto JSON com: phases (order, title, description, "
            "dependencies por order, capability, estimated_duration, materials, risks), "
            "risks, missing_information, suggested_missions (title, objective), "
            "suggested_memories (category, title, content), preliminary_budget "
            "(currency EUR, line_items com category, description, quantity, unit, "
            "unit_price, total, source, contingency_rate, assumptions, confidence_level), "
            "e assumptions. Valores podem ser omitidos."
        )


def _audit_memory(proposal: RemodelingProposal):
    from Engines.Remodeling import SuggestedMemory

    return SuggestedMemory(
        category="remodeling_proposal",
        title="Proposta preliminar aprovada",
        content=(
            f"Proposta {proposal.id}: {len(proposal.phases)} fases; "
            f"orçamento preliminar {proposal.preliminary_budget.total} "
            f"{proposal.preliminary_budget.currency}. Não é preço final."
        ),
    )
