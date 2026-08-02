from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4


class StepStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class PlanStatus(Enum):
    READY = "ready"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PlanStep:
    id: str
    title: str
    description: str
    order: int
    status: StepStatus = StepStatus.PENDING
    dependencies: tuple[str, ...] = ()
    capability: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependencies", tuple(self.dependencies))

    @classmethod
    def create(
        cls,
        *,
        title: str,
        description: str,
        order: int,
        dependencies: tuple[str, ...] = (),
        capability: str | None = None,
    ) -> PlanStep:
        return cls(
            id=str(uuid4()),
            title=title.strip() if isinstance(title, str) else title,
            description=(
                description.strip()
                if isinstance(description, str)
                else description
            ),
            order=order,
            dependencies=tuple(dependencies),
            capability=(
                capability.strip()
                if isinstance(capability, str)
                else capability
            ),
        )


@dataclass(frozen=True)
class Plan:
    id: str
    mission_id: str
    status: PlanStatus
    created_at: datetime
    steps: tuple[PlanStep, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", tuple(self.steps))
