from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from Application import ApplicationContainer, bootstrap_application
from Application.services import ProposalApplicationService
from Engines.Proposal import (
    Confidence,
    ProposalAction,
    ProposalChange,
    ProposalReview,
    ProposalSource,
    ProposalStatus,
    ReviewDecision,
)


def _id() -> str:
    return str(uuid4())


def _source(workspace_id: str) -> ProposalSource:
    return ProposalSource(
        kind="manual",
        label="Sprint 3",
        reference="test",
        captured_at=datetime.now(timezone.utc),
        workspace_id=workspace_id,
    )


def _approved(service: ProposalApplicationService, workspace_id: str, changes=()):
    draft = service.create_draft(
        workspace_id=workspace_id,
        title="Proposal de teste",
        objective="Validar coordenação",
    ).data
    generated = service.record_generation(
        draft.id,
        summary="Resumo consolidado",
        recommendation=None,
        changes=changes,
        assumptions=(),
        risks=(),
        missing_information=(),
        sources=(_source(workspace_id),),
        confidence=Confidence.MEDIUM,
    ).data
    reviewed = service.review(
        generated.id,
        ProposalReview(
            id=_id(),
            proposal_id=generated.id,
            proposal_version=generated.version,
            reviewer="reviewer",
            decision=ReviewDecision.ACCEPTED,
        ),
    ).data
    return service.approve(reviewed.id, "approver").data


def _confirm(service, proposal):
    plan = service.build_apply_plan(proposal.id).data
    return plan, {
        "proposal_id": proposal.id,
        "proposal_version": proposal.version,
        "workspace_id": proposal.workspace_id,
        "idempotency_key": plan.idempotency_key,
    }


def test_bootstrap_composes_volatile_proposal_service_without_breaking_container():
    container = bootstrap_application()
    assert isinstance(container, ApplicationContainer)
    assert isinstance(container.proposal_service, ProposalApplicationService)
    assert container.proposal_engine is not None
    assert bootstrap_application().proposal_service is not container.proposal_service


def test_service_delegates_lifecycle_and_preserves_immutable_proposal():
    container = bootstrap_application()
    service = container.proposal_service
    workspace_id = container.workspace_service.active_workspace_id
    original = service.create_draft(
        workspace_id=workspace_id,
        title="Proposal",
        objective="Objetivo",
    ).data
    change = ProposalChange(
        id=_id(),
        order=1,
        target_type="unsupported",
        target_id=None,
        action=ProposalAction.CREATE,
        summary="Mudança",
        after={"value": "x"},
    )
    generated = service.record_generation(
        original.id,
        summary="Consolidado",
        recommendation=None,
        changes=(change,),
        assumptions=(),
        risks=(),
        missing_information=(),
        sources=(_source(workspace_id),),
        confidence=Confidence.MEDIUM,
    ).data
    assert original.status is ProposalStatus.DRAFT
    assert generated.status is ProposalStatus.GENERATED
    assert generated.version == original.version + 1


def test_apply_requires_approved_and_explicit_confirmation():
    container = bootstrap_application()
    service = container.proposal_service
    workspace_id = container.workspace_service.active_workspace_id
    draft = service.create_draft(
        workspace_id=workspace_id,
        title="Proposal",
        objective="Objetivo",
    ).data
    assert not service.apply(draft.id).is_success
    approved = _approved(service, workspace_id)
    plan, _ = _confirm(service, approved)
    assert not service.apply(approved.id, plan).is_success


def test_apply_executes_supported_changes_and_is_idempotent():
    container = bootstrap_application()
    service = container.proposal_service
    workspace_id = container.workspace_service.active_workspace_id
    mission_change = ProposalChange(
        id=_id(),
        order=1,
        target_type="mission",
        target_id=None,
        action=ProposalAction.CREATE,
        summary="Criar missão",
        after={"workspace_id": workspace_id, "title": "Missão", "objective": "Objetivo"},
    )
    approved = _approved(service, workspace_id, (mission_change,))
    plan, confirmation = _confirm(service, approved)
    applied = service.apply(approved.id, plan, confirmation)
    assert applied.is_success
    assert applied.data.status is ProposalStatus.APPLIED
    report = service.get_apply_report(approved.id).data
    assert report.results[mission_change.id]["resource_type"] == "mission"
    duplicate = service.apply(approved.id, plan, confirmation)
    assert not duplicate.is_success


def test_apply_preserves_partial_failure_and_blocks_dependents():
    container = bootstrap_application()
    service = container.proposal_service
    workspace_id = container.workspace_service.active_workspace_id
    failed = ProposalChange(
        id=_id(), order=1, target_type="unknown", target_id=None,
        action=ProposalAction.CREATE, summary="Unsupported", after={"x": 1},
    )
    dependent = ProposalChange(
        id=_id(), order=2, target_type="memory", target_id=None,
        action=ProposalAction.CREATE, summary="Dependent", dependencies=(failed.id,),
        after={"workspace_id": workspace_id, "category": "test", "title": "T", "content": "C"},
    )
    independent = ProposalChange(
        id=_id(), order=3, target_type="memory", target_id=None,
        action=ProposalAction.CREATE, summary="Independent",
        after={"workspace_id": workspace_id, "category": "test", "title": "I", "content": "C"},
    )
    approved = _approved(service, workspace_id, (failed, dependent, independent))
    plan, confirmation = _confirm(service, approved)
    result = service.apply(approved.id, plan, confirmation)
    assert result.is_success
    assert result.data.status is ProposalStatus.APPLY_FAILED
    report = service.get_apply_report(approved.id).data
    assert report.statuses[failed.id].value == "failed"
    assert report.statuses[dependent.id].value == "skipped"
    assert report.statuses[independent.id].value == "applied"


def test_workspace_and_payload_validation_are_controlled_errors():
    container = bootstrap_application()
    service = container.proposal_service
    workspace_id = container.workspace_service.active_workspace_id
    change = ProposalChange(
        id=_id(), order=1, target_type="memory", target_id=None,
        action=ProposalAction.CREATE, summary="Cross workspace",
        after={"workspace_id": workspace_id, "category": "test", "title": "T"},
    )
    approved = _approved(service, workspace_id, (change,))
    plan, confirmation = _confirm(service, approved)
    result = service.apply(approved.id, plan, confirmation)
    assert result.is_success
    assert result.data.status is ProposalStatus.APPLY_FAILED
