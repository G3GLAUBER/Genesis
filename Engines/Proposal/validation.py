from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from uuid import UUID

from Engines.Proposal.models import (
    ApplyChangeStatus,
    Confidence,
    Proposal,
    ProposalAction,
    ProposalApplyPlan,
    ProposalApplyReport,
    ProposalChange,
    ProposalCreator,
    ProposalReview,
    ProposalSource,
    ProposalStatus,
    Recommendation,
    ReviewDecision,
)


_SENSITIVE_REFERENCE = re.compile(
    r"(?:authorization|bearer|cookie|password|secret|token|api[_-]?key|sk-[a-z0-9])",
    re.IGNORECASE,
)


def _is_uuid(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _is_aware_utc(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
        and value.utcoffset() == timedelta(0)
    )


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_texts(values: object) -> bool:
    return isinstance(values, tuple) and all(_non_empty_text(value) for value in values)


def _valid_uuid_sequence(values: object) -> bool:
    return isinstance(values, tuple) and all(_is_uuid(value) for value in values)


def validate_draft_input(
    *,
    workspace_id: object,
    title: object,
    objective: object,
    project_id: object = None,
    mission_id: object = None,
) -> str | None:
    if not _is_uuid(workspace_id):
        return "workspace_id deve ser um UUID válido"
    if not _non_empty_text(title):
        return "title deve ser texto não vazio"
    if not _non_empty_text(objective):
        return "objective deve ser texto não vazio"
    if project_id is not None and not _is_uuid(project_id):
        return "project_id deve ser um UUID válido"
    if mission_id is not None and not _is_uuid(mission_id):
        return "mission_id deve ser um UUID válido"
    return None


def validate_recommendation(recommendation: object) -> str | None:
    if not isinstance(recommendation, Recommendation):
        return "recommendation deve ser Recommendation"
    if not _non_empty_text(recommendation.direction):
        return "recommendation.direction deve ser texto não vazio"
    if not _non_empty_text(recommendation.reason):
        return "recommendation.reason deve ser texto não vazio"
    if not _valid_texts(recommendation.benefits):
        return "recommendation.benefits deve conter textos não vazios"
    if not _valid_texts(recommendation.concessions):
        return "recommendation.concessions deve conter textos não vazios"
    if not _valid_texts(recommendation.alternatives):
        return "recommendation.alternatives deve conter textos não vazios"
    if not isinstance(recommendation.confidence, Confidence):
        return "recommendation.confidence inválida"
    if recommendation.confidence is Confidence.HIGH and not _non_empty_text(
        recommendation.confidence_reason
    ):
        return "Confidence HIGH exige justificativa"
    return None


def _validate_payload(value: object, field: str) -> str | None:
    if value is not None and not isinstance(value, Mapping):
        return f"{field} deve ser um mapa"
    if isinstance(value, Mapping) and not all(
        isinstance(key, str) and bool(key.strip()) for key in value
    ):
        return f"{field} deve usar chaves de texto não vazias"
    return None


def _validate_workspace_payload(value: object, workspace_id: str) -> str | None:
    """Reject explicit workspace references that cross the Proposal boundary."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "workspace_id" and item != workspace_id:
                return "ProposalChange referencia outro Workspace"
            nested_error = _validate_workspace_payload(item, workspace_id)
            if nested_error:
                return nested_error
    elif isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            nested_error = _validate_workspace_payload(item, workspace_id)
            if nested_error:
                return nested_error
    return None


def validate_proposal_change(
    change: object,
    workspace_id: str | None = None,
) -> str | None:
    if not isinstance(change, ProposalChange):
        return "changes deve conter somente ProposalChange"
    if not _is_uuid(change.id):
        return "ProposalChange.id deve ser um UUID válido"
    if not isinstance(change.order, int) or isinstance(change.order, bool) or change.order <= 0:
        return "ProposalChange.order deve ser inteiro positivo"
    if not _non_empty_text(change.target_type):
        return "ProposalChange.target_type deve ser texto não vazio"
    if not _non_empty_text(change.summary):
        return "ProposalChange.summary deve ser texto não vazio"
    if not isinstance(change.action, ProposalAction):
        return "ProposalChange.action inválida"
    if change.target_id is not None and not _is_uuid(change.target_id):
        return "ProposalChange.target_id deve ser um UUID válido"
    if not _valid_uuid_sequence(change.dependencies):
        return "ProposalChange.dependencies deve conter UUIDs"
    if len(set(change.dependencies)) != len(change.dependencies):
        return "ProposalChange.dependencies não pode conter duplicados"
    before_error = _validate_payload(change.before, "ProposalChange.before")
    if before_error:
        return before_error
    after_error = _validate_payload(change.after, "ProposalChange.after")
    if after_error:
        return after_error
    if workspace_id is not None:
        for payload in (change.before, change.after):
            workspace_error = _validate_workspace_payload(payload, workspace_id)
            if workspace_error:
                return workspace_error
    if change.action is ProposalAction.CREATE:
        if change.target_id is not None:
            return "CREATE não pode declarar target_id"
        if not change.after:
            return "CREATE exige after"
    elif change.action is ProposalAction.UPDATE:
        if change.target_id is None:
            return "UPDATE exige target_id"
        if not change.after:
            return "UPDATE exige after"
    elif change.action in (ProposalAction.ASSOCIATE, ProposalAction.ARCHIVE):
        if change.target_id is None:
            return f"{change.action.name} exige target_id"
    return None


def _validate_change_graph(changes: tuple[ProposalChange, ...]) -> str | None:
    ids = {change.id for change in changes}
    if len(ids) != len(changes):
        return "changes não pode conter IDs duplicados"
    orders = [change.order for change in changes]
    if len(set(orders)) != len(orders):
        return "changes não pode conter orders duplicados"
    for change in changes:
        missing = set(change.dependencies) - ids
        if missing:
            return "dependency de change inexistente"
    visiting: set[str] = set()
    visited: set[str] = set()
    by_id = {change.id: change for change in changes}

    def visit(change_id: str) -> bool:
        if change_id in visiting:
            return False
        if change_id in visited:
            return True
        visiting.add(change_id)
        if not all(visit(dependency) for dependency in by_id[change_id].dependencies):
            return False
        visiting.remove(change_id)
        visited.add(change_id)
        return True

    if not all(visit(change.id) for change in changes):
        return "changes não pode conter dependências cíclicas"
    return None


def validate_proposal_source(source: object, workspace_id: str | None = None) -> str | None:
    if not isinstance(source, ProposalSource):
        return "sources deve conter somente ProposalSource"
    for field in ("kind", "label", "reference"):
        if not _non_empty_text(getattr(source, field)):
            return f"ProposalSource.{field} deve ser texto não vazio"
    if not _is_uuid(source.workspace_id):
        return "ProposalSource.workspace_id deve ser um UUID válido"
    if workspace_id is not None and source.workspace_id != workspace_id:
        return "ProposalSource pertence a outro Workspace"
    if not _is_aware_utc(source.captured_at):
        return "ProposalSource.captured_at deve ser datetime com timezone"
    if _SENSITIVE_REFERENCE.search(source.reference):
        return "ProposalSource.reference não pode conter credenciais ou segredos"
    return None


def validate_proposal(proposal: object) -> str | None:
    if not isinstance(proposal, Proposal):
        return "proposal deve ser Proposal"
    if not _is_uuid(proposal.id):
        return "Proposal.id deve ser um UUID válido"
    if not isinstance(proposal.version, int) or isinstance(proposal.version, bool) or proposal.version <= 0:
        return "Proposal.version deve ser inteiro positivo"
    if not _is_aware_utc(proposal.created_at):
        return "Proposal.created_at deve ser datetime com timezone"
    draft_error = validate_draft_input(
        workspace_id=proposal.workspace_id,
        title=proposal.title,
        objective=proposal.objective,
        project_id=proposal.project_id,
        mission_id=proposal.mission_id,
    )
    if draft_error:
        return draft_error
    if not isinstance(proposal.status, ProposalStatus):
        return "Proposal.status inválido"
    if proposal.summary is not None and not _non_empty_text(proposal.summary):
        return "Proposal.summary deve ser texto não vazio quando informado"
    if proposal.recommendation is not None:
        recommendation_error = validate_recommendation(proposal.recommendation)
        if recommendation_error:
            return recommendation_error
    if proposal.confidence is not None and not isinstance(proposal.confidence, Confidence):
        return "Proposal.confidence inválida"
    if proposal.confidence is Confidence.HIGH and not _non_empty_text(
        proposal.confidence_reason
    ):
        return "Confidence HIGH exige justificativa"
    if not isinstance(proposal.created_by, ProposalCreator):
        return "Proposal.created_by inválido"
    for field in ("assumptions", "risks", "missing_information"):
        if not _valid_texts(getattr(proposal, field)):
            return f"Proposal.{field} deve conter textos não vazios"
    for change in proposal.changes:
        change_error = validate_proposal_change(change, proposal.workspace_id)
        if change_error:
            return change_error
    graph_error = _validate_change_graph(proposal.changes)
    if graph_error:
        return graph_error
    for source in proposal.sources:
        source_error = validate_proposal_source(source, proposal.workspace_id)
        if source_error:
            return source_error
    if proposal.document_id is not None and not _is_uuid(proposal.document_id):
        return "Proposal.document_id deve ser um UUID válido"
    for review in proposal.reviews:
        review_error = validate_review(review)
        if review_error:
            return review_error
        if review.proposal_id != proposal.id:
            return "ProposalReview pertence a outra Proposal"
    for report in proposal.apply_reports:
        report_error = validate_apply_report(report)
        if report_error:
            return report_error
        if report.proposal_id != proposal.id:
            return "ProposalApplyReport pertence a outra Proposal"
    return None


def validate_status_transition(
    current: ProposalStatus,
    target: ProposalStatus,
) -> str | None:
    transitions = {
        ProposalStatus.DRAFT: {
            ProposalStatus.GENERATED,
            ProposalStatus.REJECTED,
        },
        ProposalStatus.GENERATED: {
            ProposalStatus.REVIEWED,
            ProposalStatus.REJECTED,
        },
        ProposalStatus.REVIEWED: {
            ProposalStatus.REVIEWED,
            ProposalStatus.APPROVED,
            ProposalStatus.REJECTED,
        },
        ProposalStatus.APPROVED: {
            ProposalStatus.APPLIED,
            ProposalStatus.APPLY_FAILED,
        },
        ProposalStatus.REJECTED: set(),
        ProposalStatus.APPLIED: set(),
        ProposalStatus.APPLY_FAILED: set(),
    }
    if target not in transitions.get(current, set()):
        return f"Transição inválida: {current.value} → {target.value}"
    return None


def validate_review(review: object) -> str | None:
    if not isinstance(review, ProposalReview):
        return "review deve ser ProposalReview"
    if not _is_uuid(review.id) or not _is_uuid(review.proposal_id):
        return "Review IDs devem ser UUIDs válidos"
    if not isinstance(review.proposal_version, int) or review.proposal_version <= 0:
        return "ProposalReview.proposal_version deve ser inteiro positivo"
    if not _non_empty_text(review.reviewer):
        return "ProposalReview.reviewer deve ser texto não vazio"
    if not isinstance(review.decision, ReviewDecision):
        return "ProposalReview.decision inválida"
    if not _non_empty_text(review.notes) and review.decision is ReviewDecision.COMMENTED:
        return "Review COMMENTED exige notes"
    if not _valid_uuid_sequence(review.changed_change_ids):
        return "changed_change_ids deve conter UUIDs"
    if review.created_at is not None and not _is_aware_utc(review.created_at):
        return "ProposalReview.created_at deve ser datetime com timezone"
    return None


def validate_apply_plan(plan: object) -> str | None:
    if not isinstance(plan, ProposalApplyPlan):
        return "plan deve ser ProposalApplyPlan"
    if not _is_uuid(plan.proposal_id):
        return "ProposalApplyPlan.proposal_id deve ser UUID"
    if not isinstance(plan.proposal_version, int) or plan.proposal_version <= 0:
        return "ProposalApplyPlan.proposal_version deve ser inteiro positivo"
    if plan.workspace_id is not None and not _is_uuid(plan.workspace_id):
        return "ProposalApplyPlan.workspace_id deve ser UUID"
    if plan.idempotency_key is not None and not _non_empty_text(plan.idempotency_key):
        return "ProposalApplyPlan.idempotency_key deve ser texto não vazio"
    if not isinstance(plan.statuses, Mapping):
        return "ProposalApplyPlan.statuses deve ser mapa"
    if not all(
        _is_uuid(key) and value is ApplyChangeStatus.PENDING
        for key, value in plan.statuses.items()
    ):
        return "ProposalApplyPlan.statuses inválido"
    if plan.created_at is not None and not _is_aware_utc(plan.created_at):
        return "ProposalApplyPlan.created_at deve ser datetime com timezone"
    for change in plan.changes:
        error = validate_proposal_change(change, plan.workspace_id)
        if error:
            return error
    if plan.statuses and set(plan.statuses) != {change.id for change in plan.changes}:
        return "ProposalApplyPlan.statuses deve conter exatamente as mudanças"
    return _validate_change_graph(plan.changes)


def validate_apply_report(report: object) -> str | None:
    if not isinstance(report, ProposalApplyReport):
        return "report deve ser ProposalApplyReport"
    if not _is_uuid(report.proposal_id):
        return "ProposalApplyReport.proposal_id deve ser UUID"
    if not isinstance(report.proposal_version, int) or report.proposal_version <= 0:
        return "ProposalApplyReport.proposal_version deve ser inteiro positivo"
    if report.workspace_id is not None and not _is_uuid(report.workspace_id):
        return "ProposalApplyReport.workspace_id deve ser UUID"
    if report.idempotency_key is not None and not _non_empty_text(report.idempotency_key):
        return "ProposalApplyReport.idempotency_key deve ser texto não vazio"
    if not isinstance(report.statuses, Mapping):
        return "ProposalApplyReport.statuses deve ser mapa"
    if not all(_is_uuid(key) and isinstance(value, ApplyChangeStatus) for key, value in report.statuses.items()):
        return "ProposalApplyReport.statuses inválido"
    if not isinstance(report.reasons, Mapping):
        return "ProposalApplyReport.reasons deve ser mapa"
    if not all(
        _is_uuid(key) and _non_empty_text(value)
        for key, value in report.reasons.items()
    ):
        return "ProposalApplyReport.reasons inválido"
    if not isinstance(report.final_status, ProposalStatus):
        return "ProposalApplyReport.final_status inválido"
    if report.final_status not in (
        ProposalStatus.APPLIED,
        ProposalStatus.APPLY_FAILED,
    ):
        return "ProposalApplyReport.final_status deve ser APPLIED ou APPLY_FAILED"
    if report.final_status is ProposalStatus.APPLY_FAILED and not (
        _non_empty_text(report.reason) or report.reasons
    ):
        return "Apply FAILED exige motivo"
    if report.final_status is ProposalStatus.APPLIED and any(
        status is not ApplyChangeStatus.APPLIED
        for status in report.statuses.values()
    ):
        return "Apply APPLIED exige todas as mudanças aplicadas"
    if report.completed_at is not None and not _is_aware_utc(report.completed_at):
        return "ProposalApplyReport.completed_at deve ser datetime com timezone"
    return None


def topologically_order_changes(
    changes: tuple[ProposalChange, ...],
) -> tuple[ProposalChange, ...] | None:
    """Return deterministic dependency order, or None for an invalid graph."""

    ids = {change.id for change in changes}
    if len(ids) != len(changes):
        return None
    by_id = {change.id: change for change in changes}
    remaining = set(ids)
    ordered: list[ProposalChange] = []
    while remaining:
        ready = sorted(
            (
                by_id[change_id]
                for change_id in remaining
                if set(by_id[change_id].dependencies).isdisjoint(remaining)
            ),
            key=lambda change: (change.order, change.id),
        )
        if not ready:
            return None
        ordered.extend(ready)
        remaining.difference_update(change.id for change in ready)
    return tuple(ordered)


__all__ = [
    "validate_apply_plan",
    "validate_apply_report",
    "validate_draft_input",
    "validate_proposal",
    "validate_proposal_change",
    "validate_proposal_source",
    "validate_recommendation",
    "validate_review",
    "validate_status_transition",
    "topologically_order_changes",
]
