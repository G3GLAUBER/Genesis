from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from Core.result import Result
from Engines.Proposal import (
    Confidence,
    Proposal,
    ProposalAction,
    ProposalChange,
    ProposalEngine,
    ProposalSource,
    Recommendation,
)
from Engines.Proposal.validation import (
    validate_proposal,
    validate_proposal_change,
    validate_proposal_source,
    validate_recommendation,
)


def _id() -> str:
    return str(uuid4())


def test_create_draft_returns_normalized_immutable_draft():
    workspace_id = _id()
    project_id = _id()
    mission_id = _id()
    result = ProposalEngine().create_draft(
        workspace_id=workspace_id,
        project_id=project_id,
        mission_id=mission_id,
        title="  Proposta inicial  ",
        objective="  Organizar o próximo resultado  ",
    )

    assert result.is_success
    proposal = result.data
    assert proposal.workspace_id == workspace_id
    assert proposal.project_id == project_id
    assert proposal.mission_id == mission_id
    assert proposal.title == "Proposta inicial"
    assert proposal.objective == "Organizar o próximo resultado"
    assert proposal.version == 1
    assert proposal.status.value == "draft"
    assert proposal.created_at.tzinfo is not None
    assert proposal.changes == ()


def test_create_draft_rejects_invalid_required_fields_with_result_error():
    engine = ProposalEngine()

    for values in (
        {"workspace_id": "not-a-uuid", "title": "Título", "objective": "Objetivo"},
        {"workspace_id": _id(), "title": "  ", "objective": "Objetivo"},
        {"workspace_id": _id(), "title": "Título", "objective": "  "},
        {"workspace_id": _id(), "title": "Título", "objective": "Objetivo", "project_id": "bad"},
    ):
        result = engine.create_draft(**values)
        assert isinstance(result, Result)
        assert not result.is_success
        assert result.message


def test_change_validation_rejects_duplicate_missing_and_cyclic_dependencies():
    first_id = _id()
    second_id = _id()
    first = ProposalChange(
        id=first_id,
        order=1,
        target_type="mission",
        target_id=None,
        action=ProposalAction.CREATE,
        summary="Criar Mission",
        after={"title": "Mission"},
        dependencies=(second_id,),
    )
    second = ProposalChange(
        id=second_id,
        order=2,
        target_type="project",
        target_id=None,
        action=ProposalAction.CREATE,
        summary="Criar Project",
        after={"title": "Project"},
        dependencies=(first_id,),
    )
    assert validate_proposal_change(first) is None
    assert validate_proposal(
        Proposal(
            id=_id(),
            version=1,
            created_at=datetime.now(timezone.utc),
            workspace_id=_id(),
            title="Título",
            objective="Objetivo",
            changes=(first, second),
        )
    ) == "changes não pode conter dependências cíclicas"


def test_change_validation_enforces_action_payload_and_ids():
    invalid_update = ProposalChange(
        id=_id(),
        order=1,
        target_type="mission",
        target_id=None,
        action=ProposalAction.UPDATE,
        summary="Atualizar Mission",
    )
    invalid_create = ProposalChange(
        id=_id(),
        order=1,
        target_type="mission",
        target_id=_id(),
        action=ProposalAction.CREATE,
        summary="Criar Mission",
    )

    assert validate_proposal_change(invalid_update) == "UPDATE exige target_id"
    assert validate_proposal_change(invalid_create) == "CREATE não pode declarar target_id"


def test_source_validation_rejects_cross_workspace_and_sensitive_reference():
    workspace_id = _id()
    source = ProposalSource(
        kind="manual",
        label="Fonte manual",
        reference="https://example.test/?token=secret",
        captured_at=datetime.now(timezone.utc),
        workspace_id=workspace_id,
    )
    assert "segredos" in validate_proposal_source(source, workspace_id)
    clean = ProposalSource(
        kind="manual",
        label="Fonte manual",
        reference="manual-handoff-1",
        captured_at=datetime.now(timezone.utc),
        workspace_id=workspace_id,
    )
    assert "outro Workspace" in validate_proposal_source(clean, _id())


def test_high_confidence_requires_reason_and_engine_has_no_application_imports():
    recommendation = Recommendation(
        direction="Avançar",
        reason="Evidência suficiente",
        confidence=Confidence.HIGH,
    )
    assert validate_recommendation(recommendation) == (
        "Confidence HIGH exige justificativa"
    )
    source = Path("Engines/Proposal")
    contents = "\n".join(path.read_text(encoding="utf-8") for path in source.glob("*.py"))
    assert "Application" not in contents
    assert "Interfaces" not in contents
    assert "http" not in contents.lower()
    assert "requests" not in contents
