from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from threading import RLock
from typing import Any

from Application.adapters.proposal_apply import (
    ApplyExecution,
    MemoryProposalAdapter,
    MissionProposalAdapter,
    ProjectMissionProposalAdapter,
    ProposalChangeAdapter,
)
from Application.services.memory_service import MemoryService
from Application.services.mission_service import MissionApplicationService
from Application.services.project_service import ProjectService
from Application.services.workspace_service import WorkspaceApplicationService
from Core.result import Result
from Engines.Proposal import (
    ApplyChangeStatus,
    Confidence,
    Proposal,
    ProposalApplyPlan,
    ProposalApplyReport,
    ProposalChange,
    ProposalEngine,
    ProposalReview,
    ProposalSource,
    ProposalStatus,
    Recommendation,
)


@dataclass(frozen=True)
class ApplyConfirmation:
    proposal_id: str
    proposal_version: int
    workspace_id: str
    idempotency_key: str
    scope: str = "proposal"


class ProposalApplicationService:
    """Application orchestration for volatile Proposal use cases."""

    def __init__(
        self,
        proposal_engine: ProposalEngine,
        mission_service: MissionApplicationService,
        project_service: ProjectService,
        memory_service: MemoryService,
        workspace_service: WorkspaceApplicationService,
        *,
        adapters: Sequence[ProposalChangeAdapter] | None = None,
    ) -> None:
        self._engine = proposal_engine
        self._missions = mission_service
        self._projects = project_service
        self._memory = memory_service
        self._workspaces = workspace_service
        self._proposals: dict[str, Proposal] = {}
        self._reports: dict[str, ProposalApplyReport] = {}
        self._completed_changes: dict[tuple[str, int], set[str]] = {}
        self._lock = RLock()
        self._adapters = tuple(adapters or self._default_adapters())

    def create_draft(self, **kwargs: Any) -> Result:
        workspace_id = kwargs.get("workspace_id")
        workspace = self._workspaces.get(workspace_id)
        if not workspace.is_success:
            return workspace
        project_id = kwargs.get("project_id")
        if project_id is not None:
            project = self._projects.get(project_id)
            if not project.is_success:
                return project
            if project.data.workspace_id != workspace_id:
                return Result.error(
                    message="Project pertence a outro Workspace"
                )
        mission_id = kwargs.get("mission_id")
        if mission_id is not None:
            missions = self._missions.list_missions(workspace_id=workspace_id)
            if not missions.is_success:
                return missions
            if not any(mission.id == mission_id for mission in missions.data):
                return Result.error(
                    message="Mission pertence a outro Workspace ou não existe"
                )
        result = self._engine.create_draft(**kwargs)
        if result.is_success:
            self._store(result.data)
        return result

    def generate(
        self,
        proposal_id: str | None,
        summary: str,
        recommendation: Recommendation | None,
        changes: Sequence[ProposalChange],
        assumptions: Sequence[str],
        risks: Sequence[str],
        missing_information: Sequence[str],
        sources: Sequence[ProposalSource],
        confidence: Confidence,
    ) -> Result:
        proposal = self._get_proposal(proposal_id)
        if not proposal.is_success:
            return proposal
        result = self._engine.record_generation(
            proposal.data,
            summary,
            recommendation,
            changes,
            assumptions,
            risks,
            missing_information,
            sources,
            confidence,
        )
        if result.is_success:
            self._store(result.data)
        return result

    def record_generation(
        self,
        proposal_id: str | None,
        summary: str,
        recommendation: Recommendation | None,
        changes: Sequence[ProposalChange],
        assumptions: Sequence[str],
        risks: Sequence[str],
        missing_information: Sequence[str],
        sources: Sequence[ProposalSource],
        confidence: Confidence,
    ) -> Result:
        return self.generate(
            proposal_id,
            summary,
            recommendation,
            changes,
            assumptions,
            risks,
            missing_information,
            sources,
            confidence,
        )

    def review(self, proposal_id: str | None, review: ProposalReview) -> Result:
        proposal = self._get_proposal(proposal_id)
        if not proposal.is_success:
            return proposal
        result = self._engine.review(proposal.data, review)
        if result.is_success:
            self._store(result.data)
        return result

    def approve(
        self,
        proposal_id: str | None,
        reviewer: str,
        notes: str = "",
    ) -> Result:
        proposal = self._get_proposal(proposal_id)
        if not proposal.is_success:
            return proposal
        result = self._engine.approve(proposal.data, reviewer, notes)
        if result.is_success:
            self._store(result.data)
        return result

    def reject(
        self,
        proposal_id: str | None,
        reviewer: str,
        reason: str,
    ) -> Result:
        proposal = self._get_proposal(proposal_id)
        if not proposal.is_success:
            return proposal
        result = self._engine.reject(proposal.data, reviewer, reason)
        if result.is_success:
            self._store(result.data)
        return result

    def build_apply_plan(self, proposal_id: str | None) -> Result:
        proposal = self._get_proposal(proposal_id)
        if not proposal.is_success:
            return proposal
        return self._engine.build_apply_plan(proposal.data)

    def get(self, proposal_id: str | None) -> Result:
        return self._get_proposal(proposal_id)

    def list(self, workspace_id: str | None = None) -> Result:
        if workspace_id is not None:
            workspace = self._workspaces.get(workspace_id)
            if not workspace.is_success:
                return workspace
        with self._lock:
            proposals = tuple(
                proposal
                for proposal in reversed(tuple(self._proposals.values()))
                if workspace_id is None or proposal.workspace_id == workspace_id
            )
        return Result.success(message="Proposals listadas", data=proposals)

    def apply(
        self,
        proposal_id: str | None,
        plan: ProposalApplyPlan | None = None,
        confirmation: ApplyConfirmation | Mapping[str, Any] | None = None,
        *,
        proposal_version: int | None = None,
    ) -> Result:
        proposal_result = self._get_proposal(proposal_id)
        if not proposal_result.is_success:
            return proposal_result
        proposal = proposal_result.data
        if proposal.status is ProposalStatus.APPLIED:
            return Result.error(message="Proposal já foi aplicada")
        if proposal.status is ProposalStatus.APPLY_FAILED:
            return Result.error(message="Proposal possui Apply FAILED; retry explícito não disponível")
        if proposal.status is not ProposalStatus.APPROVED:
            return Result.error(message="Apply exige Proposal em APPROVED")
        if proposal_version is not None and proposal_version != proposal.version:
            return Result.error(message="Versão da Proposal não corresponde")

        if plan is None:
            plan_result = self._engine.build_apply_plan(proposal)
            if not plan_result.is_success:
                return plan_result
            plan = plan_result.data
        plan_error = self._validate_plan(proposal, plan)
        if plan_error:
            return Result.error(message=plan_error)
        confirmation_error = self._validate_confirmation(
            proposal,
            plan,
            confirmation,
        )
        if confirmation_error:
            return Result.error(message=confirmation_error)

        statuses: dict[str, ApplyChangeStatus] = {}
        reasons: dict[str, str] = {}
        results: dict[str, Mapping[str, Any]] = {}
        completed_key = (proposal.id, proposal.version)
        with self._lock:
            completed = set(self._completed_changes.get(completed_key, set()))

        for change in plan.changes:
            if change.id in completed:
                statuses[change.id] = ApplyChangeStatus.APPLIED
                results[change.id] = {
                    "resource_type": "previously_applied",
                    "resource_id": change.id,
                    "message": "Change já concluída nesta Proposal/version",
                }
                continue
            blocked = [
                dependency
                for dependency in change.dependencies
                if statuses.get(dependency) is not ApplyChangeStatus.APPLIED
            ]
            if blocked:
                statuses[change.id] = ApplyChangeStatus.SKIPPED
                reasons[change.id] = (
                    "Dependências não concluídas: " + ", ".join(blocked)
                )
                continue
            adapter = self._adapter_for(change)
            if adapter is None:
                statuses[change.id] = ApplyChangeStatus.FAILED
                reasons[change.id] = (
                    f"Nenhum adapter suportado para {change.action.value}/"
                    f"{change.target_type}"
                )
                continue
            try:
                outcome = adapter.execute(proposal, change)
            except Exception as error:
                statuses[change.id] = ApplyChangeStatus.FAILED
                reasons[change.id] = f"Falha controlada no adapter: {type(error).__name__}"
                continue
            if (
                not outcome.is_success
                or not isinstance(outcome.data, ApplyExecution)
                or outcome.data.change_id != change.id
            ):
                statuses[change.id] = ApplyChangeStatus.FAILED
                reasons[change.id] = outcome.message or "Adapter não produziu evidência"
                continue
            statuses[change.id] = ApplyChangeStatus.APPLIED
            results[change.id] = {
                "resource_type": outcome.data.resource_type,
                "resource_id": outcome.data.resource_id,
                "message": outcome.data.message,
            }
            completed.add(change.id)

        final_status = (
            ProposalStatus.APPLIED
            if all(status is ApplyChangeStatus.APPLIED for status in statuses.values())
            else ProposalStatus.APPLY_FAILED
        )
        report = ProposalApplyReport(
            proposal_id=proposal.id,
            proposal_version=proposal.version,
            statuses=statuses,
            final_status=final_status,
            reason=(
                "Apply concluído"
                if final_status is ProposalStatus.APPLIED
                else "Apply parcial ou falho"
            ),
            workspace_id=proposal.workspace_id,
            idempotency_key=plan.idempotency_key,
            reasons=reasons,
            results=results,
        )
        validated = self._engine.validate_apply_report(proposal, report)
        if not validated.is_success:
            return validated
        with self._lock:
            self._store(validated.data)
            self._reports[proposal.id] = report
            self._completed_changes[completed_key] = completed
        return Result.success(
            message="Proposal aplicada" if final_status is ProposalStatus.APPLIED else "Apply FAILED",
            data=validated.data,
        )

    def get_apply_report(self, proposal_id: str | None) -> Result:
        proposal = self._get_proposal(proposal_id)
        if not proposal.is_success:
            return proposal
        with self._lock:
            report = self._reports.get(proposal.data.id)
        if report is None:
            return Result.error(message="Apply Report não encontrado")
        return Result.success(message="Apply Report encontrado", data=report)

    def _default_adapters(self) -> tuple[ProposalChangeAdapter, ...]:
        return (
            MissionProposalAdapter(
                self._missions,
                self._workspaces,
                self._projects,
            ),
            ProjectMissionProposalAdapter(
                self._projects,
                self._workspaces,
                self._missions,
            ),
            MemoryProposalAdapter(self._memory, self._missions),
        )

    def _adapter_for(self, change: ProposalChange) -> ProposalChangeAdapter | None:
        return next(
            (adapter for adapter in self._adapters if adapter.supports(change)),
            None,
        )

    def _get_proposal(self, proposal_id: str | None) -> Result:
        if not isinstance(proposal_id, str) or not proposal_id.strip():
            return Result.error(message="proposal_id é obrigatório")
        with self._lock:
            proposal = self._proposals.get(proposal_id.strip())
        if proposal is None:
            return Result.error(message="Proposal não encontrada")
        return Result.success(message="Proposal encontrada", data=proposal)

    def _store(self, proposal: Proposal) -> None:
        with self._lock:
            self._proposals[proposal.id] = proposal

    def _validate_plan(self, proposal: Proposal, plan: ProposalApplyPlan) -> str | None:
        if not isinstance(plan, ProposalApplyPlan):
            return "Apply Plan inválido"
        if plan.proposal_id != proposal.id:
            return "Apply Plan pertence a outra Proposal"
        if plan.proposal_version != proposal.version:
            return "Apply Plan referencia uma versão desatualizada"
        if plan.workspace_id != proposal.workspace_id:
            return "Apply Plan pertence a outro Workspace"
        expected_key = f"proposal:{proposal.id}:version:{proposal.version}"
        if plan.idempotency_key != expected_key:
            return "Apply Plan possui chave de idempotência inválida"
        expected_result = self._engine.build_apply_plan(proposal)
        if not expected_result.is_success:
            return expected_result.message
        expected = expected_result.data
        if tuple(change.id for change in plan.changes) != tuple(
            change.id for change in expected.changes
        ):
            return "Apply Plan não corresponde às mudanças ordenadas da Proposal"
        if dict(plan.statuses) != dict(expected.statuses):
            return "Apply Plan possui status inicial inválido"
        return None

    @staticmethod
    def _validate_confirmation(
        proposal: Proposal,
        plan: ProposalApplyPlan,
        confirmation: ApplyConfirmation | Mapping[str, Any] | None,
    ) -> str | None:
        if isinstance(confirmation, ApplyConfirmation):
            values = confirmation.__dict__
        elif isinstance(confirmation, Mapping):
            values = confirmation
        else:
            return "Apply exige confirmação explícita"
        if values.get("scope", "proposal") != "proposal":
            return "Confirmação possui alcance inválido"
        if values.get("proposal_id") != proposal.id:
            return "Confirmação pertence a outra Proposal"
        if values.get("proposal_version") != proposal.version:
            return "Confirmação referencia versão incorreta"
        if values.get("workspace_id") != proposal.workspace_id:
            return "Confirmação pertence a outro Workspace"
        if values.get("idempotency_key") != plan.idempotency_key:
            return "Confirmação possui chave de idempotência inválida"
        return None


__all__ = ["ApplyConfirmation", "ProposalApplicationService"]
