from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from Core.result import Result
from Engines.Document.models import (
    BrandProfile,
    Document,
    DocumentSection,
    DocumentStatus,
    DocumentTemplate,
    DocumentVersion,
)
from Engines.Document.validation import (
    validate_brand_profile,
    validate_document,
    validate_metadata,
    validate_template,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentEngine:
    """Pure, in-memory-free foundation for structured editorial documents."""

    def create_draft(
        self,
        document_type: str,
        title: str,
        template: DocumentTemplate,
        brand: BrandProfile,
        metadata,
    ) -> Result:
        metadata_error = validate_metadata(metadata)
        if metadata_error:
            return Result.error(message=metadata_error)
        brand_error = validate_brand_profile(brand)
        if brand_error:
            return Result.error(message=brand_error)
        template_error = validate_template(template)
        if template_error:
            return Result.error(message=template_error)
        if document_type not in template.document_types:
            return Result.error(message="template incompatível com document_type")
        now = _now()
        document_id = str(uuid4())
        document = Document(
            id=document_id,
            workspace_id=metadata.workspace_id,
            document_type=document_type,
            title=title,
            status=DocumentStatus.DRAFT,
            metadata=metadata,
            sections=(),
            template_id=template.id,
            template_version=template.version,
            brand_profile_id=brand.id,
            brand_profile_version=brand.version,
            created_at=now,
            updated_at=now,
        )
        # A draft may start without sections; required sections are enforced
        # when a concrete section tree is validated against the template.
        error = validate_document(document)
        if error:
            return Result.error(message=error)
        return Result.success(message="Document DRAFT criado", data=document)

    def generate(
        self,
        document: Document,
        sections: Sequence[DocumentSection],
        generated_by: str | None = None,
    ) -> Result:
        if not isinstance(document, Document):
            return Result.error(message="document inválido")
        if document.status is not DocumentStatus.DRAFT:
            return Result.error(message="generate exige Document em DRAFT")
        generated = replace(
            document,
            status=DocumentStatus.GENERATED,
            sections=tuple(sections),
            updated_at=_now(),
        )
        error = validate_document(generated)
        if error:
            return Result.error(message=error)
        return Result.success(message="Document GENERATED registrado", data=generated)

    def validate(self, document: Document, template: DocumentTemplate | None = None) -> Result:
        error = validate_document(document, template)
        if error:
            return Result.error(message=error)
        return Result.success(message="Document válido", data=document)


__all__ = ["DocumentEngine"]
