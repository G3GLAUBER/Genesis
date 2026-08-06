from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({
            _freeze(key): _freeze(item) for key, item in value.items()
        })
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _text(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) else value


def _texts(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(normalized for value in values if (normalized := _text(value)))


class DocumentType(str, Enum):
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    BUDGET = "budget"
    INSPECTION_REPORT = "inspection_report"
    COMPLETION_REPORT = "completion_report"
    WARRANTY = "warranty"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    IN_REVIEW = "in_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class DocumentTemplateStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DocumentReviewDecision(str, Enum):
    COMMENTED = "commented"
    ACCEPTED = "accepted"
    REQUESTED_CHANGES = "requested_changes"
    REJECTED = "rejected"


@dataclass(frozen=True)
class DocumentMetadata:
    workspace_id: str
    project_id: str | None = None
    mission_id: str | None = None
    author_id: str | None = None
    created_by: str | None = None
    locale: str | None = None
    source_refs: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    custom_fields: Mapping[str, Any] = MappingProxyType({})
    trace_id: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "workspace_id", "project_id", "mission_id", "author_id",
            "created_by", "locale", "trace_id",
        ):
            object.__setattr__(self, field, _text(getattr(self, field)))
        object.__setattr__(self, "source_refs", _texts(self.source_refs))
        object.__setattr__(self, "tags", _texts(self.tags))
        object.__setattr__(self, "custom_fields", _freeze(self.custom_fields))


@dataclass(frozen=True)
class DocumentSection:
    id: str
    key: str
    section_type: str
    title: str
    order: int
    content: Any = MappingProxyType({})
    children: tuple["DocumentSection", ...] = ()
    required: bool = False
    visible: bool = True
    reusable_section_id: str | None = None
    metadata: Mapping[str, Any] = MappingProxyType({})
    provenance: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for field in ("id", "key", "section_type", "title", "reusable_section_id"):
            object.__setattr__(self, field, _text(getattr(self, field)))
        object.__setattr__(self, "content", _freeze(self.content))
        object.__setattr__(self, "children", tuple(self.children))
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        object.__setattr__(self, "provenance", _freeze(self.provenance))


@dataclass(frozen=True)
class DocumentTemplate:
    id: str
    name: str
    version: int
    document_types: tuple[str, ...]
    section_schema: Mapping[str, Any] = MappingProxyType({})
    required_sections: tuple[str, ...] = ()
    default_sections: tuple[str, ...] = ()
    placeholder_schema: Mapping[str, Any] = MappingProxyType({})
    locale: str | None = None
    metadata: Mapping[str, Any] = MappingProxyType({})
    status: DocumentTemplateStatus = DocumentTemplateStatus.ACTIVE
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _text(self.id))
        object.__setattr__(self, "name", _text(self.name))
        object.__setattr__(self, "document_types", _texts(self.document_types))
        object.__setattr__(self, "required_sections", _texts(self.required_sections))
        object.__setattr__(self, "default_sections", _texts(self.default_sections))
        object.__setattr__(self, "locale", _text(self.locale))
        for field in ("section_schema", "placeholder_schema", "metadata"):
            object.__setattr__(self, field, _freeze(getattr(self, field)))


@dataclass(frozen=True)
class BrandProfile:
    id: str
    name: str
    version: int
    colors: Mapping[str, Any] = MappingProxyType({})
    typography: Mapping[str, Any] = MappingProxyType({})
    logo_ref: str | None = None
    watermark_ref: str | None = None
    tone: str | None = None
    contact_fields: Mapping[str, Any] = MappingProxyType({})
    header_footer: Mapping[str, Any] = MappingProxyType({})
    locale: str | None = None
    metadata: Mapping[str, Any] = MappingProxyType({})

    def __post_init__(self) -> None:
        for field in ("id", "name", "logo_ref", "watermark_ref", "tone", "locale"):
            object.__setattr__(self, field, _text(getattr(self, field)))
        for field in ("colors", "typography", "contact_fields", "header_footer", "metadata"):
            object.__setattr__(self, field, _freeze(getattr(self, field)))

    @property
    def palette_tokens(self) -> Mapping[str, Any]:
        return self.colors

    @property
    def typography_tokens(self) -> Mapping[str, Any]:
        return self.typography


@dataclass(frozen=True)
class DocumentVersion:
    document_id: str
    version: int
    status: DocumentStatus
    sections: tuple[DocumentSection, ...]
    template_id: str
    template_version: int
    brand_profile_id: str
    brand_profile_version: int
    metadata: DocumentMetadata | None = None
    created_at: datetime | None = None
    created_by: str | None = None
    reason: str | None = None
    content_hash: str | None = None
    source_version: int | None = None
    source_proposal_id: str | None = None
    source_proposal_version: int | None = None

    def __post_init__(self) -> None:
        for field in ("document_id", "template_id", "brand_profile_id", "created_by", "reason", "content_hash", "source_proposal_id"):
            object.__setattr__(self, field, _text(getattr(self, field)))
        object.__setattr__(self, "sections", tuple(self.sections))


@dataclass(frozen=True)
class DocumentReview:
    id: str
    document_id: str
    document_version: int
    reviewer: str
    decision: DocumentReviewDecision
    notes: str = ""
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        for field in ("id", "document_id", "reviewer", "notes"):
            object.__setattr__(self, field, _text(getattr(self, field)))


@dataclass(frozen=True)
class Document:
    id: str
    workspace_id: str
    document_type: str
    title: str
    status: DocumentStatus
    metadata: DocumentMetadata
    sections: tuple[DocumentSection, ...]
    template_id: str
    template_version: int
    brand_profile_id: str
    brand_profile_version: int
    current_version: int = 1
    versions: tuple[DocumentVersion, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source_document_id: str | None = None
    reviews: tuple[DocumentReview, ...] = ()

    def __post_init__(self) -> None:
        for field in ("id", "workspace_id", "document_type", "title", "template_id", "brand_profile_id", "source_document_id"):
            object.__setattr__(self, field, _text(getattr(self, field)))
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "versions", tuple(self.versions))
        object.__setattr__(self, "reviews", tuple(self.reviews))


__all__ = [
    "BrandProfile", "Document", "DocumentMetadata", "DocumentSection",
    "DocumentReview", "DocumentReviewDecision", "DocumentStatus",
    "DocumentTemplate", "DocumentTemplateStatus", "DocumentType",
    "DocumentVersion",
]
