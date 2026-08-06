from __future__ import annotations

from uuid import uuid4

from Engines.Document import (
    BrandProfile,
    DocumentEngine,
    DocumentMetadata,
    DocumentSection,
    DocumentStatus,
    DocumentTemplate,
    DocumentReview,
    DocumentReviewDecision,
)


def _id():
    return str(uuid4())


def _approved():
    engine = DocumentEngine()
    template = DocumentTemplate(
        id=_id(), name="Template", version=1, document_types=("proposal",),
        section_schema={"summary": {}}, required_sections=("summary",),
    )
    draft = engine.create_draft(
        "proposal", "Title", template, BrandProfile(id=_id(), name="Brand", version=1),
        DocumentMetadata(workspace_id=_id()),
    ).data
    section = DocumentSection(
        id=_id(), key="summary", section_type="text", title="Summary", order=1,
    )
    generated = engine.generate(draft, (section,)).data
    reviewing = engine.start_review(generated, "reviewer").data
    reviewed = engine.record_review(reviewing, DocumentReview(
        id=_id(), document_id=reviewing.id, document_version=reviewing.current_version,
        reviewer="reviewer", decision=DocumentReviewDecision.ACCEPTED,
    )).data
    return engine, engine.approve(reviewed, "approver").data, template


def test_derive_version_preserves_prior_snapshots():
    engine, approved, _ = _approved()
    derived = engine.derive_version(approved, "Correção editorial", "editor")
    assert derived.is_success
    assert derived.data.status is DocumentStatus.DRAFT
    assert derived.data.current_version == approved.current_version + 1
    assert len(derived.data.versions) == len(approved.versions) + 1
    assert derived.data.versions[-1].source_version == approved.current_version
    assert approved.status is DocumentStatus.APPROVED


def test_archive_is_terminal_for_template_and_brand_switching():
    engine, approved, _ = _approved()
    archived = engine.archive(approved).data
    template = DocumentTemplate(id=_id(), name="New", version=1, document_types=("proposal",))
    brand = BrandProfile(id=_id(), name="New brand", version=1)
    assert not engine.switch_template(archived, template).is_success
    assert not engine.switch_brand(archived, brand).is_success
    assert not engine.derive_version(archived, "retry").is_success


def test_document_has_no_commercial_apply_state():
    assert "APPLIED" not in DocumentStatus.__members__
    assert "APPLY_FAILED" not in DocumentStatus.__members__
