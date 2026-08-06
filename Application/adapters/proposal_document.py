from __future__ import annotations

from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from Core.result import Result
from Engines.Document import (
    BrandProfile,
    Document,
    DocumentEngine,
    DocumentMetadata,
    DocumentSection,
    DocumentStatus,
    DocumentTemplate,
    validate_brand_profile,
    validate_template,
)
from Engines.Proposal import Proposal, ProposalStatus


_ELIGIBLE_STATUSES = {
    ProposalStatus.GENERATED,
    ProposalStatus.REVIEWED,
    ProposalStatus.APPROVED,
}


class ProposalDocumentAdapter:
    """One-way mapper from the commercial Proposal to an editorial Document."""

    def __init__(self, document_engine: DocumentEngine | None = None) -> None:
        self._documents = document_engine or DocumentEngine()

    def create_document(
        self,
        proposal: Proposal,
        template: DocumentTemplate,
        brand: BrandProfile,
    ) -> Result:
        proposal_error = self._validate_proposal(proposal)
        if proposal_error:
            return Result.error(message=proposal_error)
        template_error = validate_template(template)
        if template_error:
            return Result.error(message=template_error)
        brand_error = validate_brand_profile(brand)
        if brand_error:
            return Result.error(message=brand_error)
        if "proposal" not in template.document_types:
            return Result.error(message="template incompatível com PROPOSAL")

        metadata = DocumentMetadata(
            workspace_id=proposal.workspace_id,
            project_id=proposal.project_id,
            mission_id=proposal.mission_id,
            created_by=proposal.created_by.value,
            source_refs=tuple(source.reference for source in proposal.sources),
            tags=("proposal",),
            custom_fields={
                "source_proposal_id": proposal.id,
                "source_proposal_version": proposal.version,
            },
        )
        created = self._documents.create_draft(
            "proposal", proposal.title, template, brand, metadata,
        )
        if not created.is_success:
            return created
        sections = self._sections(proposal)
        versioned = self._documents.create_version(
            created.data,
            sections,
            status=DocumentStatus.DRAFT,
            created_by=proposal.created_by.value,
            reason="proposal_source",
            source_proposal_id=proposal.id,
            source_proposal_version=proposal.version,
        )
        if not versioned.is_success:
            return versioned
        validated = self._documents.validate(versioned.data, template)
        if not validated.is_success:
            return validated
        return Result.success(message="Document DRAFT criado a partir da Proposal", data=validated.data)

    @staticmethod
    def _validate_proposal(proposal: object) -> str | None:
        if not isinstance(proposal, Proposal):
            return "proposal inválida"
        if proposal.status not in _ELIGIBLE_STATUSES:
            return "Proposal não é elegível para representação documental"
        if not isinstance(proposal.id, str) or not proposal.id.strip():
            return "Proposal.id inválido"
        if not isinstance(proposal.version, int) or proposal.version <= 0:
            return "Proposal.version inválida"
        if not isinstance(proposal.workspace_id, str) or not proposal.workspace_id.strip():
            return "Proposal.workspace_id inválido"
        if any(source.workspace_id != proposal.workspace_id for source in proposal.sources):
            return "Proposal possui Source de outro Workspace"
        return None

    @staticmethod
    def _section_id(proposal: Proposal, key: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"genesis:proposal:{proposal.id}:{key}"))

    @classmethod
    def _section(cls, proposal: Proposal, key: str, title: str, content: object, order: int) -> DocumentSection:
        return DocumentSection(
            id=cls._section_id(proposal, key),
            key=key,
            section_type=key,
            title=title,
            order=order,
            content=content,
        )

    @classmethod
    def _sections(cls, proposal: Proposal) -> tuple[DocumentSection, ...]:
        candidates: list[tuple[str, str, object]] = [
            ("executive_summary", "Resumo executivo", proposal.summary),
            ("objective", "Objetivo", proposal.objective),
        ]
        if proposal.changes:
            candidates.append((
                "proposed_changes", "Escopo e mudanças propostas",
                {"items": tuple({
                    "id": change.id,
                    "order": change.order,
                    "target_type": change.target_type,
                    "target_id": change.target_id,
                    "action": change.action.value,
                    "summary": change.summary,
                    "before": change.before,
                    "after": change.after,
                    "reversible": change.reversible,
                    "dependencies": change.dependencies,
                } for change in proposal.changes)},
            ))
        if proposal.recommendation is not None:
            recommendation = proposal.recommendation
            candidates.append((
                "recommendation", "Recomendação",
                {"direction": recommendation.direction, "reason": recommendation.reason,
                 "benefits": recommendation.benefits, "concessions": recommendation.concessions,
                 "alternatives": recommendation.alternatives,
                 "confidence": recommendation.confidence.value,
                 "confidence_reason": recommendation.confidence_reason},
            ))
        if proposal.risks:
            candidates.append(("risks", "Riscos", {"items": proposal.risks}))
        if proposal.assumptions:
            candidates.append(("assumptions", "Premissas", {"items": proposal.assumptions}))
        if proposal.sources:
            candidates.append((
                "sources", "Fontes",
                {"items": tuple({"kind": source.kind, "label": source.label,
                                  "reference": source.reference,
                                  "captured_at": source.captured_at.isoformat()}
                                 for source in proposal.sources)},
            ))
        if proposal.missing_information:
            candidates.append(("observations", "Observações", {"items": proposal.missing_information}))
        return tuple(
            cls._section(proposal, key, title, content, order)
            for order, (key, title, content) in enumerate(candidates, start=1)
            if content is not None
        )


__all__ = ["ProposalDocumentAdapter"]
