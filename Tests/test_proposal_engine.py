from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from Engines.Proposal import (
    ApplyChangeStatus,
    Confidence,
    ProposalAction,
    ProposalApplyReport,
    ProposalChange,
    ProposalReview,
    ProposalSource,
    ProposalStatus,
    ProposalEngine,
    ReviewDecision,
)


def _id() -> str:
    return str(uuid4())


def _source(workspace_id: str) -> ProposalSource:
    return ProposalSource(
        kind="manual",
        label="Contexto de revisão",
        reference="manual-context",
        captured_at=datetime.now(timezone.utc),
        workspace_id=workspace_id,
    )


def _change(
    *,
    order: int,
    target_type: str = "project",
    target_id: str | None = None,
    dependencies: tuple[str, ...] = (),
) -> ProposalChange:
    return ProposalChange(
        id=_id(),
        order=order,
        target_type=target_type,
        target_id=target_id,
        action=(
            ProposalAction.CREATE
            if target_id is None
            else ProposalAction.UPDATE
        ),
        summary=f"Alteração {order}",
        after={"title": f"Resultado {order}"},
        dependencies=dependencies,
    )


def _generated(engine: ProposalEngine):
    workspace_id = _id()
    draft_result = engine.create_draft(
        workspace_id=workspace_id,
        title="Proposta de teste",
        objective="Validar o lifecycle comercial",
    )
    assert draft_result.is_success
    draft = draft_result.data
    first = _change(order=1)
    generated_result = engine.record_generation(
        draft,
        summary="Resumo consolidado",
        recommendation=None,
        changes=(first,),
        assumptions=("Contexto disponível",),
        risks=("Dados incompletos",),
        missing_information=(),
        sources=(_source(workspace_id),),
        confidence=Confidence.MEDIUM,
    )
    assert generated_result.is_success
    return generated_result.data, workspace_id, first


def _approved(engine: ProposalEngine):
    generated, workspace_id, change = _generated(engine)
    review = ProposalReview(
        id=_id(),
        proposal_id=generated.id,
        proposal_version=generated.version,
        reviewer="Reviewer",
        decision=ReviewDecision.ACCEPTED,
        notes="Conteúdo validado",
    )
    reviewed_result = engine.review(generated, review)
    assert reviewed_result.is_success
    approved_result = engine.approve(reviewed_result.data, "Approver")
    assert approved_result.is_success
    return approved_result.data, workspace_id, change


def test_generation_review_and_approve_are_immutable_and_versioned():
    engine = ProposalEngine()
    generated, _, _ = _generated(engine)
    assert generated.status is ProposalStatus.GENERATED
    assert generated.version == 2

    review = ProposalReview(
        id=_id(),
        proposal_id=generated.id,
        proposal_version=generated.version,
        reviewer="Reviewer",
        decision=ReviewDecision.ACCEPTED,
        notes="Aceite",
    )
    reviewed_result = engine.review(generated, review)
    assert reviewed_result.is_success
    reviewed = reviewed_result.data
    assert reviewed is not generated
    assert reviewed.status is ProposalStatus.REVIEWED
    assert reviewed.version == generated.version
    assert reviewed.reviews == (reviewed.reviews[0],)

    approved_result = engine.approve(reviewed, "Approver", notes="Autorizado")
    assert approved_result.is_success
    approved = approved_result.data
    assert approved.status is ProposalStatus.APPROVED
    assert approved.version == reviewed.version
    assert approved.approved_by == "Approver"
    assert approved.approval_notes == "Autorizado"
    assert generated.status is ProposalStatus.GENERATED


def test_review_rejects_stale_version_and_approve_requires_accepted_review():
    engine = ProposalEngine()
    generated, _, _ = _generated(engine)
    stale = ProposalReview(
        id=_id(),
        proposal_id=generated.id,
        proposal_version=generated.version - 1,
        reviewer="Reviewer",
        decision=ReviewDecision.ACCEPTED,
    )
    assert not engine.review(generated, stale).is_success

    requested = ProposalReview(
        id=_id(),
        proposal_id=generated.id,
        proposal_version=generated.version,
        reviewer="Reviewer",
        decision=ReviewDecision.REQUESTED_CHANGES,
        notes="Faltam dados",
    )
    reviewed = engine.review(generated, requested)
    assert reviewed.is_success
    assert not engine.approve(reviewed.data, "Approver").is_success


def test_reject_preserves_content_and_audit_and_blocks_future_actions():
    engine = ProposalEngine()
    generated, _, _ = _generated(engine)
    rejected_result = engine.reject(generated, "Reviewer", "Risco não aceitável")
    assert rejected_result.is_success
    rejected = rejected_result.data
    assert rejected.status is ProposalStatus.REJECTED
    assert rejected.summary == generated.summary
    assert rejected.rejection_reason == "Risco não aceitável"
    assert rejected.reviews[-1].decision is ReviewDecision.REJECTED
    assert not engine.approve(rejected, "Approver").is_success
    assert not engine.build_apply_plan(rejected).is_success


def test_invalid_transitions_are_controlled():
    engine = ProposalEngine()
    draft_result = engine.create_draft(
        workspace_id=_id(), title="Título", objective="Objetivo"
    )
    draft = draft_result.data
    assert not engine.build_apply_plan(draft).is_success
    assert not engine.approve(draft, "Approver").is_success
    rejected = engine.reject(draft, "Reviewer", "Não seguir")
    assert rejected.is_success
    assert not engine.reject(rejected.data, "Reviewer", "Tentar novamente").is_success


def test_apply_plan_is_deterministic_and_does_not_execute_changes():
    engine = ProposalEngine()
    workspace_id = _id()
    draft = engine.create_draft(
        workspace_id=workspace_id,
        title="Plano",
        objective="Ordenar mudanças",
    ).data
    first = _change(order=2)
    second = _change(order=1, dependencies=(first.id,))
    generated = engine.record_generation(
        draft,
        "Resumo",
        None,
        (first, second),
        (),
        (),
        (),
        (_source(workspace_id),),
        Confidence.LOW,
    ).data
    reviewed = engine.review(
        generated,
        ProposalReview(
            id=_id(),
            proposal_id=generated.id,
            proposal_version=generated.version,
            reviewer="Reviewer",
            decision=ReviewDecision.ACCEPTED,
        ),
    ).data
    approved = engine.approve(reviewed, "Approver").data
    plan_result = engine.build_apply_plan(approved)
    assert plan_result.is_success
    plan = plan_result.data
    assert plan.workspace_id == workspace_id
    assert plan.changes == (first, second)
    assert plan.idempotency_key == f"proposal:{approved.id}:version:{approved.version}"
    assert approved.status is ProposalStatus.APPROVED


def test_apply_report_success_marks_applied_and_second_attempt_is_rejected():
    engine = ProposalEngine()
    approved, workspace_id, change = _approved(engine)
    report = ProposalApplyReport(
        proposal_id=approved.id,
        proposal_version=approved.version,
        statuses={change.id: ApplyChangeStatus.APPLIED},
        final_status=ProposalStatus.APPLIED,
        workspace_id=workspace_id,
        idempotency_key=f"proposal:{approved.id}:version:{approved.version}",
        completed_at=datetime.now(timezone.utc),
    )
    applied_result = engine.validate_apply_report(approved, report)
    assert applied_result.is_success
    applied = applied_result.data
    assert applied.status is ProposalStatus.APPLIED
    assert applied.apply_reports == (report,)
    assert not engine.validate_apply_report(applied, report).is_success


def test_apply_report_preserves_partial_failure_and_blocks_dependents():
    engine = ProposalEngine()
    workspace_id = _id()
    draft = engine.create_draft(
        workspace_id=workspace_id, title="Plano", objective="Falha parcial"
    ).data
    first = _change(order=1)
    dependent = _change(order=2, dependencies=(first.id,))
    generated = engine.record_generation(
        draft,
        "Resumo",
        None,
        (first, dependent),
        (),
        (),
        (),
        (_source(workspace_id),),
        Confidence.MEDIUM,
    ).data
    reviewed = engine.review(
        generated,
        ProposalReview(
            id=_id(),
            proposal_id=generated.id,
            proposal_version=generated.version,
            reviewer="Reviewer",
            decision=ReviewDecision.ACCEPTED,
        ),
    ).data
    approved = engine.approve(reviewed, "Approver").data
    report = ProposalApplyReport(
        proposal_id=approved.id,
        proposal_version=approved.version,
        statuses={
            first.id: ApplyChangeStatus.FAILED,
            dependent.id: ApplyChangeStatus.SKIPPED,
        },
        final_status=ProposalStatus.APPLY_FAILED,
        reason="A primeira mudança falhou",
        reasons={dependent.id: "Dependência bloqueada"},
        workspace_id=workspace_id,
        idempotency_key=f"proposal:{approved.id}:version:{approved.version}",
        completed_at=datetime.now(timezone.utc),
    )
    result = engine.validate_apply_report(approved, report)
    assert result.is_success
    failed = result.data
    assert failed.status is ProposalStatus.APPLY_FAILED
    assert failed.apply_reports[0].statuses[dependent.id] is ApplyChangeStatus.SKIPPED
    assert not engine.validate_apply_report(failed, report).is_success


def test_apply_report_rejects_cross_workspace_and_invalid_idempotency():
    engine = ProposalEngine()
    approved, _, change = _approved(engine)
    report = ProposalApplyReport(
        proposal_id=approved.id,
        proposal_version=approved.version,
        statuses={change.id: ApplyChangeStatus.APPLIED},
        final_status=ProposalStatus.APPLIED,
        workspace_id=_id(),
        idempotency_key="wrong-key",
    )
    assert not engine.validate_apply_report(approved, report).is_success
