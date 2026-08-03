from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProjectStatus(Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Project:
    id: str
    workspace_id: str
    title: str
    client: str
    address: str
    description: str
    status: ProjectStatus
    created_at: datetime
    mission_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mission_ids", tuple(self.mission_ids))

