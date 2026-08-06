from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID

from Engines.Document.models import (
    BrandProfile,
    Document,
    DocumentMetadata,
    DocumentSection,
    DocumentStatus,
    DocumentTemplate,
    DocumentVersion,
)


def _uuid(value: object) -> bool:
    try:
        UUID(str(value))
        return isinstance(value, str)
    except (ValueError, AttributeError, TypeError):
        return False


def _utc(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _json(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _json(item) for key, item in value.items())
    if isinstance(value, (tuple, list)):
        return all(_json(item) for item in value)
    return False


def validate_metadata(metadata: object) -> str | None:
    if not isinstance(metadata, DocumentMetadata):
        return "metadata inválido"
    if not _uuid(metadata.workspace_id):
        return "metadata.workspace_id deve ser UUID"
    for field in ("project_id", "mission_id", "author_id"):
        value = getattr(metadata, field)
        if value is not None and not _uuid(value):
            return f"metadata.{field} deve ser UUID"
    if not _json(metadata.custom_fields):
        return "metadata.custom_fields inválido"
    return None


def validate_section(section: object) -> str | None:
    if not isinstance(section, DocumentSection):
        return "section inválida"
    for field in ("id", "key", "section_type", "title"):
        if not _text(getattr(section, field)):
            return f"section.{field} deve ser texto não vazio"
    if not isinstance(section.order, int) or section.order <= 0:
        return "section.order deve ser inteiro positivo"
    if not _json(section.content) or not _json(section.metadata) or not _json(section.provenance):
        return "section contém conteúdo não serializável"
    for child in section.children:
        error = validate_section(child)
        if error:
            return error
    return None


def validate_template(template: object) -> str | None:
    if not isinstance(template, DocumentTemplate):
        return "template inválido"
    if not _uuid(template.id) or not _text(template.name):
        return "template.id e name são obrigatórios"
    if not isinstance(template.version, int) or template.version <= 0:
        return "template.version deve ser positivo"
    if not template.document_types or len(set(template.document_types)) != len(template.document_types):
        return "template.document_types inválido"
    if len(set(template.required_sections)) != len(template.required_sections):
        return "template.required_sections duplicado"
    if not set(template.required_sections).issubset(template.section_schema):
        return "template.required_sections não definido no schema"
    if not _json(template.section_schema) or not _json(template.placeholder_schema) or not _json(template.metadata):
        return "template contém dados não serializáveis"
    if template.created_at is not None and not _utc(template.created_at):
        return "template.created_at deve ser UTC"
    return None


def validate_brand_profile(brand: object) -> str | None:
    if not isinstance(brand, BrandProfile):
        return "brand profile inválido"
    if not _uuid(brand.id) or not _text(brand.name):
        return "brand.id e name são obrigatórios"
    if not isinstance(brand.version, int) or brand.version <= 0:
        return "brand.version deve ser positivo"
    for field in ("colors", "typography", "contact_fields", "header_footer", "metadata"):
        if not _json(getattr(brand, field)):
            return f"brand.{field} inválido"
    return None


def validate_version(version: object, *, expected_version: int | None = None) -> str | None:
    if not isinstance(version, DocumentVersion):
        return "document version inválida"
    if not _uuid(version.document_id) or not _uuid(version.template_id) or not _uuid(version.brand_profile_id):
        return "document version contém ID inválido"
    if not isinstance(version.version, int) or version.version <= 0:
        return "document version.version deve ser positivo"
    if expected_version is not None and version.version != expected_version:
        return "document version não é sequencial"
    if version.template_version <= 0 or version.brand_profile_version <= 0:
        return "snapshot exige versões positivas de template e brand"
    if version.source_proposal_id is not None and not _uuid(version.source_proposal_id):
        return "source_proposal_id inválido"
    if version.source_proposal_version is not None and version.source_proposal_version <= 0:
        return "source_proposal_version deve ser positivo"
    if version.metadata is not None and validate_metadata(version.metadata):
        return validate_metadata(version.metadata)
    for section in version.sections:
        if validate_section(section):
            return validate_section(section)
    return None


def validate_document(document: object, template: DocumentTemplate | None = None) -> str | None:
    if not isinstance(document, Document):
        return "document inválido"
    for field in ("id", "workspace_id", "template_id", "brand_profile_id"):
        if not _uuid(getattr(document, field)):
            return f"document.{field} deve ser UUID"
    if not _text(document.document_type) or not _text(document.title):
        return "document_type e title são obrigatórios"
    if not isinstance(document.status, DocumentStatus):
        return "document.status inválido"
    if not isinstance(document.current_version, int) or document.current_version <= 0:
        return "current_version deve ser positivo"
    if document.template_version <= 0 or document.brand_profile_version <= 0:
        return "document exige versões fixas de template e brand"
    metadata_error = validate_metadata(document.metadata)
    if metadata_error:
        return metadata_error
    if document.metadata.workspace_id != document.workspace_id:
        return "metadata.workspace_id deve coincidir com document.workspace_id"
    section_ids: set[str] = set()
    orders: set[int] = set()
    keys: set[str] = set()
    for section in document.sections:
        error = validate_section(section)
        if error:
            return error
        if section.id in section_ids or section.key in keys:
            return "sections possuem IDs ou keys duplicados"
        if section.order in orders:
            return "sections possuem order duplicado"
        section_ids.add(section.id)
        keys.add(section.key)
        orders.add(section.order)
        nested_ids: set[str] = set()
        nested_keys: set[str] = set()
        stack = list(section.children)
        while stack:
            child = stack.pop()
            if child.id in section_ids or child.id in nested_ids:
                return "sections possuem IDs duplicados"
            if child.key in keys or child.key in nested_keys:
                return "sections possuem keys duplicadas"
            nested_ids.add(child.id)
            nested_keys.add(child.key)
            stack.extend(child.children)
        section_ids.update(nested_ids)
        keys.update(nested_keys)
    if template is not None:
        template_error = validate_template(template)
        if template_error:
            return template_error
        if document.document_type not in template.document_types:
            return "template incompatível com document_type"
        if document.template_id != template.id or document.template_version != template.version:
            return "document não corresponde ao snapshot do template"
        if not set(template.required_sections).issubset(keys):
            return "seções obrigatórias ausentes"
    if len(document.versions) != 0:
        for expected, version in enumerate(document.versions, start=1):
            error = validate_version(version, expected_version=expected)
            if error:
                return error
        if document.versions[-1].version != document.current_version:
            return "current_version não corresponde ao snapshot atual"
    if document.created_at is not None and not _utc(document.created_at):
        return "created_at deve ser UTC"
    if document.updated_at is not None and not _utc(document.updated_at):
        return "updated_at deve ser UTC"
    return None


__all__ = [
    "validate_brand_profile", "validate_document", "validate_metadata",
    "validate_section", "validate_template", "validate_version",
]
