from __future__ import annotations

from dataclasses import dataclass

from Engines.Execution import MissionExecutionReport
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
