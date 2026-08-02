from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MissionStatus(Enum):
    DRAFT = "draft"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Mission:
    id: str
    title: str
    objective: str
    status: MissionStatus
    created_at: datetime
    constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    source: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(
            self,
            "success_criteria",
            tuple(self.success_criteria),
        )
