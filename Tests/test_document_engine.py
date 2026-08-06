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


def _id() -> str:
    return str(uuid4())


def _template(version: int = 1) -> DocumentTemplate:
    return DocumentTemplate(
        id=_id(), name="Editorial template", version=version,
        document_types=("proposal",),
        section_schema={"summary": {"type": "text"}},
        required_sections=("summary",),
    )


def _brand(version: int = 1) -> BrandProfile:
    return BrandProfile(id=_id(), name="Genesis", version=version)


def _draft():
    engine = DocumentEngine()
    template = _template()
    result = engine.create_draft(
        "proposal", "Editorial proposal", template, _brand(),
        DocumentMetadata(workspace_id=_id()),
    )
    assert result.is_success
    return engine, result.data, template


def _generated():
    engine, draft, template = _draft()
    result = engine.generate(
        draft,
        (DocumentSection(
            id=_id(), key="summary", section_type="text", title="Summary",
            order=1, content={"text": "Structured content"},
        ),),
        generated_by="Genesis",
    )
    assert result.is_success
    return engine, result.data, template


def test_generate_creates_immutable_editorial_snapshot():
    engine, generated, _ = _generated()
    assert generated.status is DocumentStatus.GENERATED
    assert generated.current_version == 1
    assert len(generated.versions) == 1
    assert generated.versions[0].content_hash
    assert generated.versions[0].sections == generated.sections
    assert generated is not engine


def test_review_approve_and_archive_follow_editorial_lifecycle():
    engine, generated, _ = _generated()
    in_review = engine.start_review(generated, "reviewer")
    assert in_review.is_success
    assert in_review.data.status is DocumentStatus.IN_REVIEW
    review = DocumentReview(
        id=_id(), document_id=generated.id,
        document_version=in_review.data.current_version,
        reviewer="reviewer", decision=DocumentReviewDecision.ACCEPTED,
    )
    reviewed = engine.record_review(in_review.data, review)
    assert reviewed.is_success
    approved = engine.approve(reviewed.data, "approver")
    assert approved.is_success
    assert approved.data.status is DocumentStatus.APPROVED
    archived = engine.archive(approved.data)
    assert archived.is_success
    assert archived.data.status is DocumentStatus.ARCHIVED
    assert len(archived.data.versions) == 5


def test_invalid_transitions_and_stale_reviews_return_results_errors():
    engine, draft, _ = _draft()
    assert not engine.approve(draft, "approver").is_success
    assert not engine.archive(draft).is_success
    generated = engine.generate(draft, ()).data
    in_review = engine.start_review(generated, "reviewer").data
    stale = DocumentReview(
        id=_id(), document_id=in_review.id,
        document_version=in_review.current_version - 1,
        reviewer="reviewer", decision=DocumentReviewDecision.ACCEPTED,
    )
    assert not engine.record_review(in_review, stale).is_success


def test_reject_preserves_history_and_approved_snapshots_are_not_mutated():
    engine, generated, _ = _generated()
    rejected = engine.reject(generated, "reviewer", "Conteúdo insuficiente")
    assert rejected.is_success
    assert rejected.data.status is DocumentStatus.REJECTED
    assert rejected.data.reviews[-1].decision is DocumentReviewDecision.REJECTED
    assert generated.status is DocumentStatus.GENERATED
    assert len(rejected.data.versions) == 2
