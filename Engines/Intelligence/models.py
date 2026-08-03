from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class AccessMode(str, Enum):
    MANUAL = "manual"
    API = "api"
    LOCAL = "local"


class CostTier(str, Enum):
    FREE = "free"
    LIMITED_FREE = "limited_free"
    PAID = "paid"
    LOCAL = "local"


class RoutingMode(str, Enum):
    FREE_ONLY = "free_only"
    LOCAL_FIRST = "local_first"
    ECONOMY = "economy"
    BALANCED = "balanced"
    MAX_QUALITY = "max_quality"


class HandoffStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass(frozen=True)
class ProviderProfile:
    provider_id: str
    display_name: str
    capabilities: tuple[str, ...]
    access_mode: AccessMode
    cost_tier: CostTier
    enabled: bool = False
    priority: int = 100
    notes: str | None = None

    def __post_init__(self) -> None:
        capabilities = (
            (self.capabilities,)
            if isinstance(self.capabilities, str)
            else tuple(self.capabilities)
        )
        object.__setattr__(self, "capabilities", capabilities)


@dataclass(frozen=True)
class RoutingDecision:
    request_capability: str
    prompt: str
    selected_provider_id: str
    routing_mode: RoutingMode
    access_mode: AccessMode
    reason: str
    alternatives: tuple[str, ...] = ()
    requires_manual_handoff: bool = False


@dataclass(frozen=True)
class ManualHandoff:
    id: str
    provider_id: str
    prompt: str
    status: HandoffStatus
    created_at: datetime
    completed_at: datetime | None = None
    response: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    mission_id: str | None = None


@dataclass(frozen=True)
class IntelligenceMetricsSnapshot:
    selections: int
    successes: int
    failures: int
    by_mode: Mapping[str, int] = field(default_factory=dict)
    by_provider: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "by_mode",
            MappingProxyType(dict(self.by_mode)),
        )
        object.__setattr__(
            self,
            "by_provider",
            MappingProxyType(dict(self.by_provider)),
        )
