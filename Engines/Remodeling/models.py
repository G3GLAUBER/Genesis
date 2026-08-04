from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"


@dataclass(frozen=True)
class RemodelingBrief:
    id: str
    project_id: str
    workspace_id: str
    project_type: str
    room_length: Decimal | None
    room_width: Decimal | None
    room_height: Decimal | None
    current_condition: str
    desired_result: str
    budget_limit: Decimal | None = None
    deadline: date | None = None
    constraints: tuple[str, ...] = ()
    client_preferences: tuple[str, ...] = ()
    known_materials: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(
            self, "client_preferences", tuple(self.client_preferences)
        )
        object.__setattr__(self, "known_materials", tuple(self.known_materials))


@dataclass(frozen=True)
class RemodelingPhase:
    id: str
    order: int
    title: str
    description: str
    dependencies: tuple[str, ...] = ()
    capability: str = "general_assistance"
    estimated_duration: str | None = None
    materials: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "materials", tuple(self.materials))
        object.__setattr__(self, "risks", tuple(self.risks))


@dataclass(frozen=True)
class BudgetLineItem:
    category: str
    description: str
    quantity: Decimal | None
    unit: str | None
    unit_price: Decimal | None
    total: Decimal | None
    source: str
    is_estimate: bool = True


@dataclass(frozen=True)
class PreliminaryBudget:
    currency: str
    line_items: tuple[BudgetLineItem, ...]
    subtotal: Decimal
    contingency: Decimal
    total: Decimal
    assumptions: tuple[str, ...]
    confidence_level: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "line_items", tuple(self.line_items))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))


@dataclass(frozen=True)
class SuggestedMission:
    title: str
    objective: str


@dataclass(frozen=True)
class SuggestedMemory:
    category: str
    title: str
    content: str


@dataclass(frozen=True)
class RemodelingProposal:
    id: str
    brief_id: str
    status: ProposalStatus
    phases: tuple[RemodelingPhase, ...]
    risks: tuple[str, ...]
    missing_information: tuple[str, ...]
    suggested_missions: tuple[SuggestedMission, ...]
    suggested_memories: tuple[SuggestedMemory, ...]
    preliminary_budget: PreliminaryBudget
    assumptions: tuple[str, ...]
    created_at: datetime
    raw_response: str
    provider_id: str
    routing_reason: str
    alternatives: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in (
            "phases",
            "risks",
            "missing_information",
            "suggested_missions",
            "suggested_memories",
            "assumptions",
            "alternatives",
        ):
            object.__setattr__(self, field, tuple(getattr(self, field)))
