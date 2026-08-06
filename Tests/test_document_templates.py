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


def _id():
    return str(uuid4())


def _draft():
    engine = DocumentEngine()
    template = DocumentTemplate(
        id=_id(), name="Original", version=1, document_types=("proposal",),
        section_schema={"summary": {}}, required_sections=("summary",),
    )
    brand = BrandProfile(id=_id(), name="Original brand", version=1)
    draft = engine.create_draft(
        "proposal", "Title", template, brand, DocumentMetadata(workspace_id=_id()),
    ).data
    generated = engine.generate(draft, (DocumentSection(
        id=_id(), key="summary", section_type="text", title="Summary", order=1,
    ),)).data
    return engine, generated, template, brand


def test_switch_template_creates_new_version_and_fixes_snapshot():
    engine, generated, _, brand = _draft()
    replacement = DocumentTemplate(
        id=_id(), name="Replacement", version=3, document_types=("proposal",),
        section_schema={"summary": {}}, required_sections=("summary",),
    )
    switched = engine.switch_template(generated, replacement)
    assert switched.is_success
    document = switched.data
    assert document.status is DocumentStatus.DRAFT
    assert document.template_id == replacement.id
    assert document.template_version == replacement.version
    assert document.versions[-1].template_version == 3
    assert generated.template_id != document.template_id


def test_switch_brand_creates_new_version_without_changing_template():
    engine, generated, template, _ = _draft()
    replacement = BrandProfile(id=_id(), name="Replacement", version=4)
    switched = engine.switch_brand(generated, replacement)
    assert switched.is_success
    assert switched.data.brand_profile_id == replacement.id
    assert switched.data.brand_profile_version == 4
    assert switched.data.template_id == template.id
    assert switched.data.versions[-1].brand_profile_id == replacement.id


def test_template_and_brand_switch_reject_incompatible_or_invalid_inputs():
    engine, generated, _, _ = _draft()
    incompatible = DocumentTemplate(
        id=_id(), name="Contract", version=1, document_types=("contract",),
    )
    assert not engine.switch_template(generated, incompatible).is_success
    invalid_brand = BrandProfile(id="invalid", name="", version=0)
    assert not engine.switch_brand(generated, invalid_brand).is_success
