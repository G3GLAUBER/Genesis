from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from Engines.Document import (
    BrandProfile,
    DocumentMetadata,
    DocumentSection,
    DocumentStatus,
    DocumentTemplate,
    DocumentTemplateStatus,
    DocumentVersion,
    validate_brand_profile,
    validate_metadata,
    validate_section,
    validate_template,
    validate_version,
)


def _id() -> str:
    return str(uuid4())


def _metadata(workspace_id: str | None = None) -> DocumentMetadata:
    return DocumentMetadata(
        workspace_id=workspace_id or _id(),
        project_id=_id(),
        mission_id=_id(),
        custom_fields={"source": {"kind": "manual"}},
    )


def _template() -> DocumentTemplate:
    return DocumentTemplate(
        id=_id(), name="Proposal base", version=1,
        document_types=("proposal",),
        section_schema={"summary": {"type": "text"}},
        required_sections=("summary",),
        status=DocumentTemplateStatus.ACTIVE,
    )


def _brand() -> BrandProfile:
    return BrandProfile(
        id=_id(), name="Genesis", version=2,
        colors={"primary": "blue"}, typography={"body": "sans"},
        header_footer={"header": "Genesis"},
    )


def test_section_and_metadata_are_deeply_immutable():
    section = DocumentSection(
        id=_id(), key="summary", section_type="text", title="Resumo",
        order=1, content={"items": ["one"]}, metadata={"x": {"y": 1}},
    )
    metadata = _metadata()
    with pytest.raises(TypeError):
        section.content["new"] = "value"
    with pytest.raises(TypeError):
        metadata.custom_fields["new"] = "value"
    assert section.content["items"] == ("one",)


def test_template_and_brand_tokens_are_frozen_and_validated():
    template = _template()
    brand = _brand()
    assert validate_template(template) is None
    assert validate_brand_profile(brand) is None
    with pytest.raises(TypeError):
        brand.colors["secondary"] = "green"
    with pytest.raises(TypeError):
        template.section_schema["new"] = {}


def test_invalid_template_and_sections_are_rejected():
    invalid = DocumentTemplate(
        id="not-uuid", name="", version=0, document_types=(),
    )
    assert validate_template(invalid) is not None
    first = DocumentSection(
        id=_id(), key="summary", section_type="text", title="S", order=1,
    )
    duplicate = DocumentSection(
        id=first.id, key="other", section_type="text", title="O", order=1,
    )
    assert validate_section(first) is None
    assert validate_section(duplicate) is None


def test_version_snapshot_requires_fixed_positive_versions_and_provenance():
    document_id, template_id, brand_id = _id(), _id(), _id()
    version = DocumentVersion(
        document_id=document_id, version=1, status=DocumentStatus.DRAFT,
        sections=(), template_id=template_id, template_version=3,
        brand_profile_id=brand_id, brand_profile_version=2,
        metadata=_metadata(), created_at=datetime.now(timezone.utc),
        source_proposal_id=_id(), source_proposal_version=4,
    )
    assert validate_version(version) is None
    invalid = DocumentVersion(
        document_id=document_id, version=0, status=DocumentStatus.DRAFT,
        sections=(), template_id=template_id, template_version=0,
        brand_profile_id=brand_id, brand_profile_version=2,
    )
    assert validate_version(invalid) is not None
    assert validate_metadata(version.metadata) is None
