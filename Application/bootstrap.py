from __future__ import annotations

from dataclasses import dataclass

from Application.services import (
    MissionApplicationService,
    WorkspaceApplicationService,
)
from Core.registry import Registry
from Engines.AI import AIOrchestrator, FakeProvider
from Engines.Execution import MissionExecutionEngine
from Engines.Mission import MissionEngine
from Engines.Planning import Planner
from Engines.Workspace import WorkspaceEngine, WorkspaceManager


@dataclass(frozen=True)
class ApplicationContainer:
    registry: Registry
    provider: FakeProvider
    ai_orchestrator: AIOrchestrator
    mission_engine: MissionEngine
    planner: Planner
    execution_engine: MissionExecutionEngine
    workspace_engine: WorkspaceEngine
    workspace_manager: WorkspaceManager
    mission_service: MissionApplicationService
    workspace_service: WorkspaceApplicationService


def bootstrap_application() -> ApplicationContainer:
    registry = Registry()
    provider = FakeProvider()
    registry.register(provider.provider_id, provider)
    ai_orchestrator = AIOrchestrator(
        registry,
        provider_ids=(provider.provider_id,),
    )
    mission_engine = MissionEngine()
    planner = Planner()
    execution_engine = MissionExecutionEngine(ai_orchestrator)
    workspace_engine = WorkspaceEngine()
    workspace_manager = WorkspaceManager(workspace_engine)
    workspace_service = WorkspaceApplicationService(workspace_manager)
    initial_workspace = workspace_service.create(
        name="Workspace principal",
        description="Workspace inicial do Genesis Companion",
    )
    if not initial_workspace.is_success:
        raise RuntimeError("Falha ao criar o Workspace inicial")
    mission_service = MissionApplicationService(
        mission_engine,
        planner,
        execution_engine,
        provider_id=provider.provider_id,
        workspace_service=workspace_service,
    )
    return ApplicationContainer(
        registry=registry,
        provider=provider,
        ai_orchestrator=ai_orchestrator,
        mission_engine=mission_engine,
        planner=planner,
        execution_engine=execution_engine,
        workspace_engine=workspace_engine,
        workspace_manager=workspace_manager,
        mission_service=mission_service,
        workspace_service=workspace_service,
    )
