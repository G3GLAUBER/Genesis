from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from Engines.Execution import MissionExecutionReport
from Engines.Intelligence import RoutingDecision, RoutingMode
from Engines.Memory import MemoryRecord
from Engines.Mission import Mission
from Engines.Planning import Plan
from Engines.Workspace import Workspace


@dataclass(frozen=True)
class MissionApplicationExecution:
    mission: Mission
    plan: Plan
    report: MissionExecutionReport
    provider_id: str
    workspace: Workspace | None = None


@dataclass(frozen=True)
class MissionCopilotContext:
    workspace_id: str
    workspace_name: str
    project_id: str | None = None
    project_title: str | None = None
    project_client: str | None = None
    project_address: str | None = None
    project_description: str | None = None
    constraints: tuple[str, ...] = ()
    memories: tuple[MemoryRecord, ...] = ()
    expected_result: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "memories", tuple(self.memories))


@dataclass(frozen=True)
class MissionCopilotRequest:
    mission: Mission
    context: MissionCopilotContext
    prompt: str
    decision: RoutingDecision
    created_at: datetime


@dataclass(frozen=True)
class MissionCopilotResult:
    id: str
    mission_id: str
    workspace_id: str
    project_id: str | None
    provider_id: str
    routing_mode: RoutingMode
    prompt: str
    raw_response: str
    summary: str | None
    suggested_actions: tuple[str, ...] | None
    risks: tuple[str, ...] | None
    assumptions: tuple[str, ...] | None
    created_at: datetime

    def __post_init__(self) -> None:
        for field in ("suggested_actions", "risks", "assumptions"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, tuple(value))
