from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    """Return a recursively immutable representation of a payload."""

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                _freeze(key): _freeze(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _normalize_text(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) else value


def _normalize_texts(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(
        normalized
        for value in values
        if (normalized := _normalize_text(value)) is not None
    )


class ProposalStatus(Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    APPLY_FAILED = "apply_failed"


class Confidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProposalAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    ASSOCIATE = "associate"
    ARCHIVE = "archive"


class ProposalCreator(Enum):
    USER = "user"
    GENESIS = "genesis"
    MANUAL_HANDOFF = "manual_handoff"


class ReviewDecision(Enum):
    COMMENTED = "commented"
    ACCEPTED = "accepted"
    REQUESTED_CHANGES = "requested_changes"
    REJECTED = "rejected"


class ApplyChangeStatus(Enum):
    PENDING = "pending"
    APPLIED = "applied"
    SKIPPED = "skipped"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class ProposalChange:
    id: str
    order: int
    target_type: str
    target_id: str | None
    action: ProposalAction
    summary: str
    before: Mapping[str, Any] | None = None
    after: Mapping[str, Any] | None = None
    reversible: bool = False
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_type", _normalize_text(self.target_type))
        object.__setattr__(self, "target_id", _normalize_text(self.target_id))
        object.__setattr__(self, "summary", _normalize_text(self.summary))
        object.__setattr__(self, "before", _freeze(self.before))
        object.__setattr__(self, "after", _freeze(self.after))
        object.__setattr__(self, "dependencies", _normalize_texts(self.dependencies))


@dataclass(frozen=True)
class ProposalSource:
    kind: str
    label: str
    reference: str
    captured_at: datetime
    workspace_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _normalize_text(self.kind))
        object.__setattr__(self, "label", _normalize_text(self.label))
        object.__setattr__(self, "reference", _normalize_text(self.reference))
        object.__setattr__(self, "workspace_id", _normalize_text(self.workspace_id))


@dataclass(frozen=True)
class Recommendation:
    direction: str
    reason: str
    benefits: tuple[str, ...] = ()
    concessions: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    confidence: Confidence = Confidence.MEDIUM
    confidence_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", _normalize_text(self.direction))
        object.__setattr__(self, "reason", _normalize_text(self.reason))
        object.__setattr__(self, "benefits", _normalize_texts(self.benefits))
        object.__setattr__(self, "concessions", _normalize_texts(self.concessions))
        object.__setattr__(self, "alternatives", _normalize_texts(self.alternatives))
        object.__setattr__(
            self,
            "confidence_reason",
            _normalize_text(self.confidence_reason),
        )


@dataclass(frozen=True)
class ProposalReview:
    id: str
    proposal_id: str
    proposal_version: int
    reviewer: str
    decision: ReviewDecision
    notes: str = ""
    changed_change_ids: tuple[str, ...] = ()
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "reviewer", _normalize_text(self.reviewer))
        object.__setattr__(self, "notes", _normalize_text(self.notes))
        object.__setattr__(
            self,
            "changed_change_ids",
            _normalize_texts(self.changed_change_ids),
        )


@dataclass(frozen=True)
class Proposal:
    id: str
    version: int
    created_at: datetime
    workspace_id: str
    project_id: str | None = None
    mission_id: str | None = None
    title: str = ""
    objective: str = ""
    summary: str | None = None
    status: ProposalStatus = ProposalStatus.DRAFT
    recommendation: Recommendation | None = None
    changes: tuple[ProposalChange, ...] = ()
    assumptions: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    sources: tuple[ProposalSource, ...] = ()
    confidence: Confidence | None = None
    confidence_reason: str | None = None
    created_by: ProposalCreator = ProposalCreator.GENESIS
    approved_at: datetime | None = None
    approved_by: str | None = None
    applied_at: datetime | None = None
    rejection_reason: str | None = None
    document_id: str | None = None
    reviews: tuple[ProposalReview, ...] = ()
    apply_reports: tuple[ProposalApplyReport, ...] = ()
    approval_notes: str = ""

    def __post_init__(self) -> None:
        for field in (
            "id",
            "workspace_id",
            "project_id",
            "mission_id",
            "title",
            "objective",
            "summary",
            "confidence_reason",
            "approved_by",
            "rejection_reason",
            "document_id",
            "approval_notes",
        ):
            object.__setattr__(self, field, _normalize_text(getattr(self, field)))
        object.__setattr__(self, "changes", tuple(self.changes))
        object.__setattr__(self, "assumptions", _normalize_texts(self.assumptions))
        object.__setattr__(self, "risks", _normalize_texts(self.risks))
        object.__setattr__(
            self,
            "missing_information",
            _normalize_texts(self.missing_information),
        )
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "reviews", tuple(self.reviews))
        object.__setattr__(self, "apply_reports", tuple(self.apply_reports))


@dataclass(frozen=True)
class ProposalApplyPlan:
    proposal_id: str
    proposal_version: int
    changes: tuple[ProposalChange, ...] = ()
    workspace_id: str | None = None
    idempotency_key: str | None = None
    statuses: Mapping[str, ApplyChangeStatus] = MappingProxyType({})
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", _normalize_text(self.proposal_id))
        object.__setattr__(self, "changes", tuple(self.changes))
        object.__setattr__(self, "workspace_id", _normalize_text(self.workspace_id))
        object.__setattr__(
            self,
            "idempotency_key",
            _normalize_text(self.idempotency_key),
        )
        object.__setattr__(self, "statuses", _freeze(self.statuses))


@dataclass(frozen=True)
class ProposalApplyReport:
    proposal_id: str
    proposal_version: int
    statuses: Mapping[str, ApplyChangeStatus] = MappingProxyType({})
    final_status: ProposalStatus = ProposalStatus.APPLY_FAILED
    reason: str = ""
    completed_at: datetime | None = None
    workspace_id: str | None = None
    idempotency_key: str | None = None
    reasons: Mapping[str, str] = MappingProxyType({})
    results: Mapping[str, Mapping[str, Any]] = MappingProxyType({})

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", _normalize_text(self.proposal_id))
        object.__setattr__(self, "statuses", _freeze(self.statuses))
        object.__setattr__(self, "reason", _normalize_text(self.reason))
        object.__setattr__(self, "workspace_id", _normalize_text(self.workspace_id))
        object.__setattr__(
            self,
            "idempotency_key",
            _normalize_text(self.idempotency_key),
        )
        object.__setattr__(self, "reasons", _freeze(self.reasons))
        object.__setattr__(self, "results", _freeze(self.results))


__all__ = [
    "ApplyChangeStatus",
    "Confidence",
    "Proposal",
    "ProposalAction",
    "ProposalApplyPlan",
    "ProposalApplyReport",
    "ProposalChange",
    "ProposalCreator",
    "ProposalReview",
    "ProposalSource",
    "ProposalStatus",
    "Recommendation",
    "ReviewDecision",
]
