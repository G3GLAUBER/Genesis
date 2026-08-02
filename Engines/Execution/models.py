from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class StepExecutionResult:
    step_id: str
    status: ExecutionStatus
    provider_id: str | None
    content: str | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime


@dataclass(frozen=True)
class MissionExecutionReport:
    mission_id: str
    plan_id: str
    status: ExecutionStatus
    step_results: tuple[StepExecutionResult, ...]
    started_at: datetime
    completed_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_results", tuple(self.step_results))


@dataclass(frozen=True)
class MissionExecutionFailure:
    code: str
    message: str
    mission_id: str | None = None
    plan_id: str | None = None
