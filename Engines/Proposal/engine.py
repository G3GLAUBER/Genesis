from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from Core.result import Result
from Engines.Proposal.models import (
    ApplyChangeStatus,
    Confidence,
    Proposal,
    ProposalAction,
    ProposalApplyPlan,
    ProposalApplyReport,
    ProposalChange,
    ProposalReview,
    ProposalSource,
    ProposalStatus,
    Recommendation,
    ReviewDecision,
)
from Engines.Proposal.validation import (
    topologically_order_changes,
    validate_apply_plan,
    validate_apply_report,
    validate_draft_input,
    validate_proposal,
    validate_review,
    validate_status_transition,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _error(message: str) -> Result:
    return Result.error(message=message)


class ProposalEngine:
    """Pure commercial Proposal lifecycle and Apply contract."""

    def create_draft(
        self,
        *,
        workspace_id: str,
        title: str,
        objective: str,
        project_id: str | None = None,
        mission_id: str | None = None,
    ) -> Result:
        input_error = validate_draft_input(
            workspace_id=workspace_id,
            title=title,
            objective=objective,
            project_id=project_id,
            mission_id=mission_id,
        )
        if input_error:
            return _error(input_error)

        proposal = Proposal(
            id=str(uuid4()),
            version=1,
            created_at=_now(),
            workspace_id=workspace_id,
            project_id=project_id,
            mission_id=mission_id,
            title=title,
            objective=objective,
            status=ProposalStatus.DRAFT,
        )
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        return Result.success(message="Proposal DRAFT criada", data=proposal)

    def record_generation(
        self,
        proposal: Proposal,
        summary: str,
        recommendation: Recommendation | None,
        changes: Sequence[ProposalChange],
        assumptions: Sequence[str],
        risks: Sequence[str],
        missing_information: Sequence[str],
        sources: Sequence[ProposalSource],
        confidence: Confidence,
    ) -> Result:
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        transition_error = validate_status_transition(
            proposal.status,
            ProposalStatus.GENERATED,
        )
        if transition_error:
            return _error(transition_error)
        if not isinstance(summary, str) or not summary.strip():
            return _error("summary deve ser texto não vazio")
        if not isinstance(confidence, Confidence):
            return _error("confidence inválida")

        generated = replace(
            proposal,
            version=proposal.version + 1,
            status=ProposalStatus.GENERATED,
            summary=summary,
            recommendation=recommendation,
            changes=tuple(changes),
            assumptions=tuple(assumptions),
            risks=tuple(risks),
            missing_information=tuple(missing_information),
            sources=tuple(sources),
            confidence=confidence,
            rejection_reason=None,
        )
        generated_error = validate_proposal(generated)
        if generated_error:
            return _error(generated_error)
        if not generated.sources:
            return _error("Proposal GENERATED exige pelo menos uma Source")
        return Result.success(
            message="Proposal GENERATED registrada",
            data=generated,
        )

    def review(self, proposal: Proposal, review: ProposalReview) -> Result:
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        review_error = validate_review(review)
        if review_error:
            return _error(review_error)
        if proposal.status not in (ProposalStatus.GENERATED, ProposalStatus.REVIEWED):
            return _error("review exige Proposal em GENERATED ou REVIEWED")
        if review.proposal_id != proposal.id:
            return _error("Review pertence a outra Proposal")
        if review.proposal_version != proposal.version:
            return _error("Review referencia uma versão desatualizada")
        if review.decision is ReviewDecision.REJECTED:
            if not isinstance(review.notes, str) or not review.notes.strip():
                return _error("Review REJECTED exige justificativa")
            recorded_review = review
            if recorded_review.created_at is None:
                recorded_review = replace(recorded_review, created_at=_now())
            rejected = replace(
                proposal,
                status=ProposalStatus.REJECTED,
                rejection_reason=recorded_review.notes,
                reviews=(*proposal.reviews, recorded_review),
            )
            rejected_error = validate_proposal(rejected)
            if rejected_error:
                return _error(rejected_error)
            return Result.success(
                message="Proposal REJECTED registrada",
                data=rejected,
            )
        change_ids = {change.id for change in proposal.changes}
        if not set(review.changed_change_ids).issubset(change_ids):
            return _error("Review referencia mudança inexistente")

        recorded_review = review
        if recorded_review.created_at is None:
            recorded_review = replace(recorded_review, created_at=_now())
        reviewed = replace(
            proposal,
            status=ProposalStatus.REVIEWED,
            reviews=(*proposal.reviews, recorded_review),
            rejection_reason=None,
        )
        reviewed_error = validate_proposal(reviewed)
        if reviewed_error:
            return _error(reviewed_error)
        return Result.success(message="Proposal REVIEWED registrada", data=reviewed)

    def approve(
        self,
        proposal: Proposal,
        reviewer: str,
        notes: str = "",
    ) -> Result:
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        transition_error = validate_status_transition(
            proposal.status,
            ProposalStatus.APPROVED,
        )
        if transition_error:
            return _error(transition_error)
        if not isinstance(reviewer, str) or not reviewer.strip():
            return _error("reviewer deve ser texto não vazio")
        if not proposal.reviews:
            return _error("approve exige ProposalReview válida")
        latest = proposal.reviews[-1]
        if latest.proposal_version != proposal.version:
            return _error("Review não corresponde à versão atual")
        if latest.decision is not ReviewDecision.ACCEPTED:
            return _error("approve exige Review ACCEPTED")

        approved = replace(
            proposal,
            status=ProposalStatus.APPROVED,
            approved_at=_now(),
            approved_by=reviewer,
            approval_notes=notes,
            rejection_reason=None,
        )
        approved_error = validate_proposal(approved)
        if approved_error:
            return _error(approved_error)
        return Result.success(message="Proposal APPROVED registrada", data=approved)

    def reject(self, proposal: Proposal, reviewer: str, reason: str) -> Result:
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        transition_error = validate_status_transition(
            proposal.status,
            ProposalStatus.REJECTED,
        )
        if transition_error:
            return _error(transition_error)
        if not isinstance(reviewer, str) or not reviewer.strip():
            return _error("reviewer deve ser texto não vazio")
        if not isinstance(reason, str) or not reason.strip():
            return _error("reason deve ser texto não vazio")

        recorded_review = ProposalReview(
            id=str(uuid4()),
            proposal_id=proposal.id,
            proposal_version=proposal.version,
            reviewer=reviewer,
            decision=ReviewDecision.REJECTED,
            notes=reason,
            created_at=_now(),
        )
        rejected = replace(
            proposal,
            status=ProposalStatus.REJECTED,
            rejection_reason=reason,
            reviews=(*proposal.reviews, recorded_review),
        )
        rejected_error = validate_proposal(rejected)
        if rejected_error:
            return _error(rejected_error)
        return Result.success(message="Proposal REJECTED registrada", data=rejected)

    def build_apply_plan(self, proposal: Proposal) -> Result:
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        if proposal.status is not ProposalStatus.APPROVED:
            return _error("build_apply_plan exige Proposal em APPROVED")
        if not proposal.approved_by or proposal.approved_at is None:
            return _error("Proposal APPROVED não possui aprovação rastreável")

        ordered = topologically_order_changes(proposal.changes)
        if ordered is None:
            return _error("changes possui dependências inválidas ou cíclicas")
        plan = ProposalApplyPlan(
            proposal_id=proposal.id,
            proposal_version=proposal.version,
            changes=ordered,
            workspace_id=proposal.workspace_id,
            idempotency_key=self._idempotency_key(proposal),
            statuses={
                change.id: ApplyChangeStatus.PENDING
                for change in ordered
            },
            created_at=_now(),
        )
        plan_error = validate_apply_plan(plan)
        if plan_error:
            return _error(plan_error)
        return Result.success(message="ProposalApplyPlan criado", data=plan)

    def validate_apply_report(
        self,
        proposal: Proposal,
        report: ProposalApplyReport,
    ) -> Result:
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return _error(proposal_error)
        report_error = validate_apply_report(report)
        if report_error:
            return _error(report_error)
        if proposal.status is not ProposalStatus.APPROVED:
            return _error("Apply exige Proposal em APPROVED")
        if report.proposal_id != proposal.id:
            return _error("Apply Report pertence a outra Proposal")
        if report.proposal_version != proposal.version:
            return _error("Apply Report referencia uma versão desatualizada")
        if report.workspace_id != proposal.workspace_id:
            return _error("Apply Report pertence a outro Workspace")
        if report.idempotency_key != self._idempotency_key(proposal):
            return _error("Apply Report possui chave de idempotência inválida")

        change_ids = {change.id for change in proposal.changes}
        if set(report.statuses) != change_ids:
            return _error("Apply Report deve conter exatamente as mudanças da Proposal")
        if not set(report.reasons).issubset(change_ids):
            return _error("Apply Report possui motivo para mudança inexistente")
        by_id = {change.id: change for change in proposal.changes}
        for change in proposal.changes:
            status = report.statuses[change.id]
            dependency_statuses = (
                report.statuses[dependency]
                for dependency in change.dependencies
            )
            if status is ApplyChangeStatus.APPLIED and any(
                dependency_status is not ApplyChangeStatus.APPLIED
                for dependency_status in dependency_statuses
            ):
                return _error("mudança aplicada depende de mudança não aplicada")
            if status in (
                ApplyChangeStatus.FAILED,
                ApplyChangeStatus.SKIPPED,
                ApplyChangeStatus.ROLLED_BACK,
            ) and change.id not in report.reasons and not report.reason:
                return _error("falha de mudança exige motivo")
            if change.target_id is None and by_id[change.id].action is ProposalAction.UPDATE:
                return _error("UPDATE sem target_id no Apply Report")

        if report.final_status is ProposalStatus.APPLIED:
            if any(
                status is not ApplyChangeStatus.APPLIED
                for status in report.statuses.values()
            ):
                return _error("APPLIED exige sucesso total")
        elif not any(
            status in (
                ApplyChangeStatus.FAILED,
                ApplyChangeStatus.SKIPPED,
                ApplyChangeStatus.ROLLED_BACK,
            )
            for status in report.statuses.values()
        ):
            return _error("APPLY_FAILED exige falha ou mudança não executada")

        completed_at = report.completed_at or _now()
        recorded_report = replace(report, completed_at=completed_at)
        final = replace(
            proposal,
            status=report.final_status,
            applied_at=completed_at if report.final_status is ProposalStatus.APPLIED else None,
            apply_reports=(*proposal.apply_reports, recorded_report),
        )
        final_error = validate_proposal(final)
        if final_error:
            return _error(final_error)
        return Result.success(
            message=f"Apply {report.final_status.value.upper()} registrado",
            data=final,
        )

    @staticmethod
    def _idempotency_key(proposal: Proposal) -> str:
        return f"proposal:{proposal.id}:version:{proposal.version}"


__all__ = ["ProposalEngine"]
