from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from Application.adapters import ProposalDocumentAdapter
from Engines.Document import BrandProfile, DocumentStatus, DocumentTemplate
from Engines.Proposal import (
    Confidence,
    ProposalAction,
    ProposalChange,
    ProposalEngine,
    ProposalStatus,
    ProposalSource,
)


def _id() -> str:
    return str(uuid4())


def _template() -> DocumentTemplate:
    return DocumentTemplate(
        id=_id(), name="Proposal template", version=4,
        document_types=("proposal",),
        section_schema={
            "executive_summary": {}, "objective": {},
            "proposed_changes": {}, "recommendation": {},
            "risks": {}, "assumptions": {}, "sources": {}, "observations": {},
        },
    )


def _proposal():
    engine = ProposalEngine()
    workspace_id = _id()
    draft = engine.create_draft(
        workspace_id=workspace_id, title="Proposal", objective="Objetivo comercial",
    ).data
    source = ProposalSource(
        kind="manual", label="Fonte", reference="contexto",
        captured_at=datetime.now(timezone.utc), workspace_id=workspace_id,
    )
    change = ProposalChange(
        id=_id(), order=1, target_type="mission", target_id=None,
        action=ProposalAction.CREATE, summary="Criar missão",
        after={"title": "Missão", "objective": "Executar"},
    )
    generated = engine.record_generation(
        draft, "Resumo", None, (change,), ("Premissa",), ("Risco",),
        ("Observação",), (source,), Confidence.MEDIUM,
    )
    assert generated.is_success
    return generated.data, workspace_id


def test_adapter_creates_draft_and_first_version_without_mutating_proposal():
    proposal, workspace_id = _proposal()
    original_document_id = proposal.document_id
    result = ProposalDocumentAdapter().create_document(
        proposal, _template(), BrandProfile(id=_id(), name="Brand", version=2),
    )
    assert result.is_success
    document = result.data
    assert document.status is DocumentStatus.DRAFT
    assert document.workspace_id == workspace_id
    assert document.metadata.project_id == proposal.project_id
    assert document.current_version == 1
    assert len(document.versions) == 1
    assert proposal.document_id == original_document_id
    assert document.versions[0].source_proposal_id == proposal.id
    assert document.versions[0].source_proposal_version == proposal.version


def test_adapter_maps_only_existing_content_in_deterministic_order():
    proposal, _ = _proposal()
    result = ProposalDocumentAdapter().create_document(
        proposal, _template(), BrandProfile(id=_id(), name="Brand", version=1),
    )
    assert result.is_success
    sections = result.data.sections
    assert tuple(section.order for section in sections) == tuple(range(1, len(sections) + 1))
    assert [section.key for section in sections] == [
        "executive_summary", "objective", "proposed_changes", "risks",
        "assumptions", "sources", "observations",
    ]
    assert all(section.content for section in sections)


def test_adapter_rejects_ineligible_proposal_incompatible_template_and_brand():
    proposal, _ = _proposal()
    rejected = proposal.__class__(**{**proposal.__dict__, "status": ProposalStatus.REJECTED})
    adapter = ProposalDocumentAdapter()
    assert not adapter.create_document(rejected, _template(), BrandProfile(id=_id(), name="Brand", version=1)).is_success
    incompatible = DocumentTemplate(id=_id(), name="Contract", version=1, document_types=("contract",))
    assert not adapter.create_document(proposal, incompatible, BrandProfile(id=_id(), name="Brand", version=1)).is_success
    assert not adapter.create_document(proposal, _template(), BrandProfile(id="invalid", name="", version=0)).is_success


def test_adapter_is_one_way_and_does_not_import_renderers():
    import Application.adapters.proposal_document as module

    assert "ProposalDocumentAdapter" in module.__dict__
    assert "PDF" not in module.__dict__
    assert "DOCX" not in module.__dict__
    assert "HTML" not in module.__dict__
