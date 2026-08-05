from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class WorkflowStage(Enum):
    PROJECT_CREATED = "project_created"
    MISSION_CREATED = "mission_created"
    MISSION_COMPLETED = "mission_completed"
    PROPOSAL_PENDING = "proposal_pending"
    PROPOSAL_APPROVED = "proposal_approved"
    PLANNING_PENDING = "planning_pending"
    EXECUTION_PENDING = "execution_pending"
    COMPLETED = "completed"


@dataclass(frozen=True)
class WorkflowRecommendation:
    title: str
    description: str
    priority: str
    destination: str
    rationale: str


@dataclass(frozen=True)
class WorkflowState:
    project_id: str
    current_stage: WorkflowStage
    progress: int
    next_action: str
    recommendation: WorkflowRecommendation
    reason: str
    blockers: tuple[str, ...]
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "blockers", tuple(self.blockers))


@dataclass(frozen=True)
class WorkflowObservation:
    project_id: str
    project_title: str
    mission_ids: tuple[str, ...] = ()
    mission_copilot_completed: bool = False
    proposal_pending: bool = False
    proposal_approved: bool = False
    planning_ready: bool = False
    execution_pending: bool = False
    execution_completed: bool = False
    project_completed: bool = False
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "mission_ids", tuple(self.mission_ids))
        object.__setattr__(self, "blockers", tuple(self.blockers))
