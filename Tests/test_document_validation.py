from __future__ import annotations

from uuid import uuid4

from Engines.Document import (
    BrandProfile,
    DocumentEngine,
    DocumentMetadata,
    DocumentSection,
    DocumentStatus,
    DocumentTemplate,
)


def _id() -> str:
    return str(uuid4())


def _template(*types: str) -> DocumentTemplate:
    return DocumentTemplate(
        id=_id(), name="Template", version=1,
        document_types=types or ("proposal",),
        section_schema={"summary": {"type": "text"}},
        required_sections=("summary",),
    )


def _brand() -> BrandProfile:
    return BrandProfile(id=_id(), name="Brand", version=1)


def test_document_creation_requires_workspace_and_template_compatibility():
    engine = DocumentEngine()
    workspace_id = _id()
    metadata = DocumentMetadata(workspace_id=workspace_id)
    created = engine.create_draft("proposal", "Proposal", _template(), _brand(), metadata)
    assert created.is_success
    document = created.data
    assert document.status is DocumentStatus.DRAFT
    assert document.workspace_id == workspace_id
    incompatible = engine.create_draft(
        "contract", "Contract", _template("proposal"), _brand(), metadata,
    )
    assert not incompatible.is_success


def test_document_generation_validates_unique_order_and_required_sections():
    engine = DocumentEngine()
    metadata = DocumentMetadata(workspace_id=_id())
    created = engine.create_draft("proposal", "Proposal", _template(), _brand(), metadata).data
    missing = engine.generate(
        created,
        (DocumentSection(
            id=_id(), key="other", section_type="text", title="Other", order=1,
        ),),
    )
    assert missing.is_success
    assert engine.validate(missing.data, _template()).is_success is False

    first = DocumentSection(
        id=_id(), key="summary", section_type="text", title="Summary", order=1,
    )
    second = DocumentSection(
        id=_id(), key="other", section_type="text", title="Other", order=1,
    )
    duplicate_order = engine.generate(created, (first, second))
    assert duplicate_order.is_success is False


def test_document_domain_has_editorial_statuses_only():
    assert not hasattr(DocumentStatus, "APPLIED")
    assert DocumentStatus.APPROVED.value == "approved"
    assert not any("Proposal" in name for name in DocumentStatus.__members__)


def test_document_engine_has_no_external_or_renderer_contracts():
    import Engines.Document.engine as module

    names = set(module.__dict__)
    assert "Application" not in names
    assert "ProposalEngine" not in names
    assert "PDF" not in names
    assert "DOCX" not in names
    assert "HTML" not in names
