from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Application.services import (
    IntelligenceApplicationService,
    MemoryService,
    MissionApplicationService,
    ProjectService,
    WorkspaceApplicationService,
)
from Core.registry import Registry
from Engines.AI import AIOrchestrator, FakeProvider
from Engines.Execution import MissionExecutionEngine
from Engines.Memory import InMemoryRepository, MemoryEngine, MemoryRepository
from Engines.Intelligence import (
    AccessMode,
    CostTier,
    IntelligenceMetrics,
    IntelligenceRouter,
    ManualHandoffManager,
    ProviderCatalog,
    ProviderProfile,
)
from Engines.Mission import MissionEngine
from Engines.Planning import Planner
from Engines.Projects import (
    InMemoryProjectRepository,
    ProjectEngine,
    ProjectRepository,
)
from Engines.Workspace import (
    InMemoryWorkspaceRepository,
    WorkspaceEngine,
    WorkspaceManager,
)
from Infrastructure.Persistence import (
    SQLiteDatabase,
    SQLiteMemoryRepository,
    SQLiteProjectRepository,
    SQLiteWorkspaceRepository,
    migrate,
)


@dataclass(frozen=True)
class ApplicationContainer:
    persistence_mode: str
    database: SQLiteDatabase | None
    registry: Registry
    provider: FakeProvider
    ai_orchestrator: AIOrchestrator
    mission_engine: MissionEngine
    planner: Planner
    execution_engine: MissionExecutionEngine
    memory_repository: MemoryRepository
    memory_engine: MemoryEngine
    project_repository: ProjectRepository
    project_engine: ProjectEngine
    workspace_engine: WorkspaceEngine
    workspace_manager: WorkspaceManager
    mission_service: MissionApplicationService
    memory_service: MemoryService
    project_service: ProjectService
    workspace_service: WorkspaceApplicationService
    provider_catalog: ProviderCatalog | None = None
    intelligence_router: IntelligenceRouter | None = None
    manual_handoffs: ManualHandoffManager | None = None
    intelligence_metrics: IntelligenceMetrics | None = None
    intelligence_service: IntelligenceApplicationService | None = None


def bootstrap_application(
    *,
    persistent: bool = False,
    database_path: str | Path | None = None,
) -> ApplicationContainer:
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
    database = None
    use_sqlite = persistent or database_path is not None
    if use_sqlite:
        database = SQLiteDatabase(database_path or Path("Data/genesis.db"))
        migrate(database)
        memory_repository = SQLiteMemoryRepository(database)
        project_repository = SQLiteProjectRepository(database)
        workspace_repository = SQLiteWorkspaceRepository(database)
    else:
        memory_repository = InMemoryRepository()
        project_repository = InMemoryProjectRepository()
        workspace_repository = InMemoryWorkspaceRepository()
    memory_engine = MemoryEngine(memory_repository)
    memory_service = MemoryService(memory_engine)
    project_engine = ProjectEngine(project_repository)
    workspace_engine = WorkspaceEngine()
    workspace_manager = WorkspaceManager(
        workspace_engine,
        repository=workspace_repository,
    )
    workspace_service = WorkspaceApplicationService(workspace_manager)
    existing = workspace_service.list()
    if existing.data:
        workspace_service.set_active(existing.data[0].id)
    else:
        initial_workspace = workspace_service.create(
            name="Workspace principal",
            description="Workspace inicial do Genesis Companion",
        )
        if not initial_workspace.is_success:
            raise RuntimeError("Falha ao criar o Workspace inicial")
    project_service = ProjectService(
        project_engine,
        workspace_service=workspace_service,
    )
    mission_service = MissionApplicationService(
        mission_engine,
        planner,
        execution_engine,
        provider_id=provider.provider_id,
        workspace_service=workspace_service,
    )
    provider_catalog = ProviderCatalog()
    for profile in _initial_provider_profiles():
        registered = provider_catalog.register(profile)
        if not registered.is_success:
            raise RuntimeError("Falha ao configurar ProviderProfile inicial")
    intelligence_router = IntelligenceRouter(provider_catalog)
    manual_handoffs = ManualHandoffManager()
    intelligence_metrics = IntelligenceMetrics()
    intelligence_service = IntelligenceApplicationService(
        provider_catalog,
        intelligence_router,
        manual_handoffs,
        intelligence_metrics,
        orchestrator=ai_orchestrator,
        memory_service=memory_service,
        workspace_service=workspace_service,
        project_service=project_service,
    )
    return ApplicationContainer(
        persistence_mode="sqlite" if use_sqlite else "memory",
        database=database,
        registry=registry,
        provider=provider,
        ai_orchestrator=ai_orchestrator,
        mission_engine=mission_engine,
        planner=planner,
        execution_engine=execution_engine,
        provider_catalog=provider_catalog,
        intelligence_router=intelligence_router,
        manual_handoffs=manual_handoffs,
        intelligence_metrics=intelligence_metrics,
        memory_repository=memory_repository,
        memory_engine=memory_engine,
        project_repository=project_repository,
        project_engine=project_engine,
        workspace_engine=workspace_engine,
        workspace_manager=workspace_manager,
        mission_service=mission_service,
        intelligence_service=intelligence_service,
        memory_service=memory_service,
        project_service=project_service,
        workspace_service=workspace_service,
    )


def _initial_provider_profiles() -> tuple[ProviderProfile, ...]:
    return (
        ProviderProfile(
            provider_id="manual-general",
            display_name="Manual General Provider",
            capabilities=("general_assistance", "text_generation"),
            access_mode=AccessMode.MANUAL,
            cost_tier=CostTier.FREE,
            enabled=True,
            priority=20,
            notes="Disponibilidade depende de ação manual do usuário.",
        ),
        ProviderProfile(
            provider_id="manual-coding",
            display_name="Manual Coding Provider",
            capabilities=("code_generation",),
            access_mode=AccessMode.MANUAL,
            cost_tier=CostTier.FREE,
            enabled=True,
            priority=10,
            notes="Disponibilidade depende de ação manual do usuário.",
        ),
        ProviderProfile(
            provider_id="local-provider",
            display_name="Local Provider",
            capabilities=("text_generation",),
            access_mode=AccessMode.LOCAL,
            cost_tier=CostTier.LOCAL,
            enabled=False,
            priority=10,
            notes="Perfil demonstrativo; executor não configurado.",
        ),
        ProviderProfile(
            provider_id="api-provider",
            display_name="API Provider",
            capabilities=("text_generation",),
            access_mode=AccessMode.API,
            cost_tier=CostTier.LIMITED_FREE,
            enabled=False,
            priority=30,
            notes="Perfil demonstrativo; API não configurada.",
        ),
        ProviderProfile(
            provider_id="paid-provider",
            display_name="Paid Provider",
            capabilities=("text_generation",),
            access_mode=AccessMode.API,
            cost_tier=CostTier.PAID,
            enabled=False,
            priority=5,
            notes="Perfil demonstrativo; cobrança não configurada.",
        ),
        ProviderProfile(
            provider_id="fake",
            display_name="Development Fake Provider",
            capabilities=("text_generation",),
            access_mode=AccessMode.LOCAL,
            cost_tier=CostTier.LOCAL,
            enabled=True,
            priority=50,
            notes="Provider determinístico local para desenvolvimento.",
        ),
    )
