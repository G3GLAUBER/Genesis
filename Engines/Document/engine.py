from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from Core.result import Result
from Engines.Document.models import (
    BrandProfile,
    Document,
    DocumentSection,
    DocumentReview,
    DocumentReviewDecision,
    DocumentStatus,
    DocumentTemplate,
    DocumentVersion,
)
from Engines.Document.validation import (
    validate_brand_profile,
    validate_document,
    validate_metadata,
    validate_review,
    validate_template,
    validate_version,
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

    @staticmethod
    def _hash(document: Document, sections: Sequence[DocumentSection]) -> str:
        def plain(value):
            if isinstance(value, dict):
                return {str(key): plain(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
            if hasattr(value, "items"):
                return {str(key): plain(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
            if isinstance(value, (tuple, list)):
                return [plain(item) for item in value]
            if hasattr(value, "value"):
                return value.value
            if hasattr(value, "__dict__") and not isinstance(value, type):
                return {key: plain(item) for key, item in value.__dict__.items()}
            return value

        payload = {
            "document_type": document.document_type,
            "sections": plain(tuple(sections)),
            "template_id": document.template_id,
            "template_version": document.template_version,
            "brand_profile_id": document.brand_profile_id,
            "brand_profile_version": document.brand_profile_version,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _snapshot(
        document: Document,
        *,
        status: DocumentStatus,
        sections: Sequence[DocumentSection] | None = None,
        template_id: str | None = None,
        template_version: int | None = None,
        brand_profile_id: str | None = None,
        brand_profile_version: int | None = None,
        reason: str | None = None,
        created_by: str | None = None,
        source_version: int | None = None,
        reviews: tuple[DocumentReview, ...] | None = None,
    ) -> Document:
        selected_sections = tuple(document.sections if sections is None else sections)
        next_version = document.current_version if not document.versions else document.current_version + 1
        version = DocumentVersion(
            document_id=document.id,
            version=next_version,
            status=status,
            sections=selected_sections,
            template_id=template_id or document.template_id,
            template_version=template_version or document.template_version,
            brand_profile_id=brand_profile_id or document.brand_profile_id,
            brand_profile_version=brand_profile_version or document.brand_profile_version,
            metadata=document.metadata,
            created_at=_now(),
            created_by=created_by,
            reason=reason,
            content_hash=DocumentEngine._hash(document, selected_sections),
            source_version=source_version,
        )
        return replace(
            document,
            status=status,
            sections=selected_sections,
            template_id=version.template_id,
            template_version=version.template_version,
            brand_profile_id=version.brand_profile_id,
            brand_profile_version=version.brand_profile_version,
            current_version=next_version,
            versions=(*document.versions, version),
            reviews=document.reviews if reviews is None else reviews,
            updated_at=version.created_at,
        )

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
        generated = self._snapshot(
            document, status=DocumentStatus.GENERATED, sections=sections,
            created_by=generated_by, reason="generation",
        )
        error = validate_document(generated)
        if error:
            return Result.error(message=error)
        return Result.success(message="Document GENERATED registrado", data=generated)

    def start_review(self, document: Document, reviewer: str) -> Result:
        if document.status not in (DocumentStatus.GENERATED, DocumentStatus.REVIEWED):
            return Result.error(message="start_review exige Document GENERATED ou REVIEWED")
        if not isinstance(reviewer, str) or not reviewer.strip():
            return Result.error(message="reviewer deve ser texto não vazio")
        reviewed = self._snapshot(document, status=DocumentStatus.IN_REVIEW, created_by=reviewer, reason="start_review")
        error = validate_document(reviewed)
        return Result.error(message=error) if error else Result.success(message="Document em IN_REVIEW", data=reviewed)

    def record_review(self, document: Document, review: DocumentReview) -> Result:
        if document.status is not DocumentStatus.IN_REVIEW:
            return Result.error(message="record_review exige Document em IN_REVIEW")
        error = validate_review(review)
        if error:
            return Result.error(message=error)
        if review.document_id != document.id or review.document_version != document.current_version:
            return Result.error(message="Review referencia versão incorreta")
        recorded = replace(review, created_at=review.created_at or _now())
        next_status = (
            DocumentStatus.REJECTED
            if recorded.decision is DocumentReviewDecision.REJECTED
            else DocumentStatus.REVIEWED
        )
        updated = self._snapshot(
            document, status=next_status, created_by=recorded.reviewer,
            reason="record_review", reviews=(*document.reviews, recorded),
        )
        error = validate_document(updated)
        return Result.error(message=error) if error else Result.success(message="Review editorial registrada", data=updated)

    def approve(self, document: Document, approver: str) -> Result:
        if document.status is not DocumentStatus.REVIEWED:
            return Result.error(message="approve exige Document em REVIEWED")
        if not isinstance(approver, str) or not approver.strip():
            return Result.error(message="approver deve ser texto não vazio")
        if not document.reviews or document.reviews[-1].decision is not DocumentReviewDecision.ACCEPTED:
            return Result.error(message="approve exige Review ACCEPTED")
        approved = self._snapshot(document, status=DocumentStatus.APPROVED, created_by=approver, reason="approve")
        error = validate_document(approved)
        return Result.error(message=error) if error else Result.success(message="Document APPROVED", data=approved)

    def reject(self, document: Document, reviewer: str, reason: str) -> Result:
        if document.status not in (DocumentStatus.DRAFT, DocumentStatus.GENERATED, DocumentStatus.IN_REVIEW, DocumentStatus.REVIEWED):
            return Result.error(message="reject exige Document em estado editorial aberto")
        if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(reason, str) or not reason.strip():
            return Result.error(message="reviewer e reason são obrigatórios")
        review = DocumentReview(
            id=str(uuid4()), document_id=document.id, document_version=document.current_version,
            reviewer=reviewer, decision=DocumentReviewDecision.REJECTED, notes=reason, created_at=_now(),
        )
        return self.record_review(replace(document, status=DocumentStatus.IN_REVIEW), review)

    def archive(self, document: Document) -> Result:
        if document.status not in (DocumentStatus.APPROVED, DocumentStatus.SUPERSEDED):
            return Result.error(message="archive exige Document APPROVED ou SUPERSEDED")
        archived = self._snapshot(document, status=DocumentStatus.ARCHIVED, reason="archive")
        error = validate_document(archived)
        return Result.error(message=error) if error else Result.success(message="Document ARCHIVED", data=archived)

    def supersede(self, document: Document, reason: str = "superseded") -> Result:
        if document.status is not DocumentStatus.APPROVED:
            return Result.error(message="supersede exige Document APPROVED")
        superseded = self._snapshot(document, status=DocumentStatus.SUPERSEDED, reason=reason)
        error = validate_document(superseded)
        return Result.error(message=error) if error else Result.success(message="Document SUPERSEDED", data=superseded)

    def derive_version(self, document: Document, reason: str, created_by: str | None = None) -> Result:
        if document.status in (DocumentStatus.ARCHIVED, DocumentStatus.SUPERSEDED):
            return Result.error(message="Document arquivado não pode gerar versão")
        if not isinstance(reason, str) or not reason.strip():
            return Result.error(message="reason deve ser texto não vazio")
        derived = self._snapshot(
            document, status=DocumentStatus.DRAFT, reason=reason,
            created_by=created_by, source_version=document.current_version,
        )
        error = validate_document(derived)
        return Result.error(message=error) if error else Result.success(message="Nova versão editorial criada", data=derived)

    def switch_template(self, document: Document, template: DocumentTemplate) -> Result:
        error = validate_template(template)
        if error:
            return Result.error(message=error)
        if document.status in (DocumentStatus.APPROVED, DocumentStatus.ARCHIVED, DocumentStatus.SUPERSEDED):
            return Result.error(message="Template não pode ser trocado neste estado")
        if document.document_type not in template.document_types:
            return Result.error(message="template incompatível com document_type")
        switched = self._snapshot(
            document, status=DocumentStatus.DRAFT, template_id=template.id,
            template_version=template.version, reason="switch_template",
        )
        error = validate_document(switched, template)
        return Result.error(message=error) if error else Result.success(message="Template editorial trocado", data=switched)

    def switch_brand(self, document: Document, brand: BrandProfile) -> Result:
        error = validate_brand_profile(brand)
        if error:
            return Result.error(message=error)
        if document.status in (DocumentStatus.APPROVED, DocumentStatus.ARCHIVED, DocumentStatus.SUPERSEDED):
            return Result.error(message="BrandProfile não pode ser trocado neste estado")
        switched = self._snapshot(
            document, status=DocumentStatus.DRAFT,
            brand_profile_id=brand.id, brand_profile_version=brand.version,
            reason="switch_brand",
        )
        error = validate_document(switched)
        return Result.error(message=error) if error else Result.success(message="BrandProfile editorial trocado", data=switched)

    def validate(self, document: Document, template: DocumentTemplate | None = None) -> Result:
        error = validate_document(document, template)
        if error:
            return Result.error(message=error)
        return Result.success(message="Document válido", data=document)


__all__ = ["DocumentEngine"]
