from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class WorkspaceStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Workspace:
    id: str
    name: str
    description: str
    created_at: datetime
    status: WorkspaceStatus
    mission_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mission_ids", tuple(self.mission_ids))
