from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from types import MappingProxyType
from uuid import UUID, uuid4

import pytest

from Engines.Proposal import (
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


def _id() -> str:
    return str(uuid4())


def test_proposal_models_are_constructible_and_immutable():
    workspace_id = _id()
    change_id = _id()
    now = datetime.now(timezone.utc)
    change = ProposalChange(
        id=change_id,
        order=1,
        target_type="mission",
        target_id=None,
        action=ProposalAction.CREATE,
        summary="Criar uma Mission",
        after={"title": "Primeira Mission", "tags": ["initial"]},
    )
    source = ProposalSource(
        kind="workspace",
        label="Contexto local",
        reference="workspace-context",
        captured_at=now,
        workspace_id=workspace_id,
    )
    recommendation = Recommendation(
        direction="Começar pela Mission",
        reason="É o próximo resultado observável.",
        benefits=("Mantém o foco",),
        concessions=("Não cobre execução ainda",),
        alternatives=("Rever o Project",),
        confidence=Confidence.MEDIUM,
    )
    proposal = Proposal(
        id=_id(),
        version=1,
        created_at=now,
        workspace_id=workspace_id,
        title="Plano inicial",
        objective="Dar continuidade ao Project",
        recommendation=recommendation,
        changes=(change,),
        assumptions=("O objetivo permanece válido",),
        risks=("Informação incompleta",),
        missing_information=("Prazo preferido",),
        sources=(source,),
        confidence=Confidence.MEDIUM,
        created_by=ProposalCreator.GENESIS,
    )
    review = ProposalReview(
        id=_id(),
        proposal_id=proposal.id,
        proposal_version=1,
        reviewer="Ana",
        decision=ReviewDecision.COMMENTED,
        notes="Rever antes de avançar",
        changed_change_ids=(change_id,),
        created_at=now,
    )
    plan = ProposalApplyPlan(
        proposal_id=proposal.id,
        proposal_version=1,
        changes=(change,),
    )
    report = ProposalApplyReport(
        proposal_id=proposal.id,
        proposal_version=1,
        statuses={change_id: ApplyChangeStatus.SKIPPED},
        final_status=ProposalStatus.APPLY_FAILED,
        reason="Aguardando confirmação",
        completed_at=now,
    )

    assert proposal.status is ProposalStatus.DRAFT
    assert proposal.created_at.tzinfo is not None
    assert isinstance(change.after, MappingProxyType)
    assert change.after["tags"] == ("initial",)
    assert review.proposal_id == proposal.id
    assert plan.changes == (change,)
    assert report.statuses[change_id] is ApplyChangeStatus.SKIPPED
    UUID(proposal.id)

    with pytest.raises(FrozenInstanceError):
        proposal.title = "Outro título"
    with pytest.raises(TypeError):
        change.after["new"] = "value"


def test_models_normalize_texts_and_collections_without_mutating_inputs():
    assumptions = ["  uma premissa  "]
    dependencies = ["  " + _id() + "  "]
    change = ProposalChange(
        id=_id(),
        order=1,
        target_type="  project  ",
        target_id=None,
        action=ProposalAction.CREATE,
        summary="  criar  ",
        after={"nested": {"items": ["a", "b"]}},
        dependencies=dependencies,
    )

    assert change.target_type == "project"
    assert change.summary == "criar"
    assert change.dependencies == (dependencies[0].strip(),)
    assert change.after["nested"]["items"] == ("a", "b")
    assert assumptions == ["  uma premissa  "]
