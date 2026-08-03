from dataclasses import FrozenInstanceError
from http import HTTPStatus
import inspect
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from Application import ApplicationContainer, bootstrap_application
from Engines.AI import AIRequest, AIResponse
from Engines.Intelligence import (
    AccessMode,
    CostTier,
    HandoffStatus,
    IntelligenceRouter,
    ManualHandoffManager,
    ProviderCatalog,
    ProviderProfile,
    RoutingMode,
)
from Interfaces.Companion import CompanionApplication
from Interfaces.Companion.server import create_server


def profile(
    provider_id: str,
    *,
    access: AccessMode = AccessMode.MANUAL,
    cost: CostTier = CostTier.FREE,
    enabled: bool = True,
    priority: int = 10,
    capabilities: tuple[str, ...] = ("text_generation",),
) -> ProviderProfile:
    return ProviderProfile(
        provider_id=provider_id,
        display_name=provider_id.title(),
        capabilities=capabilities,
        access_mode=access,
        cost_tier=cost,
        enabled=enabled,
        priority=priority,
    )


def route_profiles(
    *profiles: ProviderProfile,
    mode: RoutingMode = RoutingMode.FREE_ONLY,
    capability: str = "text_generation",
):
    catalog = ProviderCatalog()
    for item in profiles:
        assert catalog.register(item).is_success
    return IntelligenceRouter(catalog).route(
        AIRequest("Pedido", capability),
        mode=mode,
    )


def test_catalog_registers_and_lists_provider_profile():
    catalog = ProviderCatalog()
    item = profile("manual")

    assert catalog.register(item).data is item
    assert catalog.list() == (item,)
    assert catalog.register(item).is_success is False


def test_provider_profile_is_deeply_immutable():
    item = profile("manual")
    with pytest.raises(FrozenInstanceError):
        item.enabled = False
    assert isinstance(item.capabilities, tuple)


def test_router_selects_compatible_enabled_provider():
    result = route_profiles(
        profile("wrong", capabilities=("vision",)),
        profile("disabled", enabled=False),
        profile("compatible"),
    )
    assert result.data.selected_provider_id == "compatible"


def test_free_only_never_selects_paid_provider():
    result = route_profiles(
        profile("paid", cost=CostTier.PAID, priority=0),
        profile("free", cost=CostTier.FREE, priority=50),
        mode=RoutingMode.FREE_ONLY,
    )
    assert result.data.selected_provider_id == "free"
    assert "paid" not in result.data.alternatives


def test_local_first_prioritizes_local_access():
    result = route_profiles(
        profile("manual", priority=0),
        profile("local", access=AccessMode.LOCAL, cost=CostTier.LOCAL),
        mode=RoutingMode.LOCAL_FIRST,
    )
    assert result.data.selected_provider_id == "local"


def test_priority_and_provider_id_make_order_deterministic():
    result = route_profiles(
        profile("zeta", priority=5),
        profile("alpha", priority=5),
        mode=RoutingMode.BALANCED,
    )
    assert result.data.selected_provider_id == "alpha"
    assert result.data.alternatives == ("zeta",)


def test_no_compatible_provider_returns_controlled_result():
    result = route_profiles(profile("vision", capabilities=("vision",)))
    assert result.is_success is False
    assert "Nenhum provider compatível" in result.message


def test_decision_is_explainable_and_marks_manual_handoff():
    result = route_profiles(profile("manual"))
    assert result.data.reason
    assert result.data.prompt == "Pedido"
    assert result.data.requires_manual_handoff is True


def test_manual_handoff_creation_completion_and_immutability():
    manager = ManualHandoffManager()
    created = manager.create(provider_id="manual", prompt="Copiar isto").data
    completed = manager.complete(created.id, response="Resposta preservada").data

    assert created.status is HandoffStatus.PENDING
    assert completed.status is HandoffStatus.COMPLETED
    assert completed.response == "Resposta preservada"
    assert completed.completed_at is not None
    with pytest.raises(FrozenInstanceError):
        completed.response = "alterada"


def test_application_integrates_workspace_project_and_memory():
    container = bootstrap_application()
    workspace = container.workspace_service.get_active().data
    project = container.project_service.create(
        workspace_id=workspace.id,
        title="Projeto Intelligence",
        client="Cliente",
        address="Local",
    ).data
    handoff = container.intelligence_service.create_manual_handoff(
        provider_id="manual-general",
        prompt="Pedido manual",
        workspace_id=workspace.id,
        project_id=project.id,
    ).data

    completed = container.intelligence_service.complete_manual_handoff(
        handoff.id,
        response="Resultado útil",
        save_as_memory=True,
    )
    memories = container.memory_service.history(workspace_id=workspace.id).data

    assert completed.is_success
    assert memories[0].content == "Resultado útil"
    assert memories[0].metadata["project_id"] == project.id


def test_project_must_belong_to_handoff_workspace():
    container = bootstrap_application()
    first = container.workspace_service.get_active().data
    project = container.project_service.create(
        workspace_id=first.id, title="P", client="C", address="A"
    ).data
    second = container.workspace_service.create(name="Outro").data

    result = container.intelligence_service.create_manual_handoff(
        provider_id="manual-general",
        prompt="Pedido",
        workspace_id=second.id,
        project_id=project.id,
    )
    assert result.is_success is False
    assert "não pertence" in result.message


def test_automatic_provider_is_executed_by_existing_ai_orchestrator():
    container = bootstrap_application()
    result = container.intelligence_service.execute_automatic(
        prompt="Executar localmente",
        capability="text_generation",
        mode=RoutingMode.LOCAL_FIRST,
    )
    assert result.is_success
    assert isinstance(result.data, AIResponse)
    assert result.data.provider_id == "fake"


def test_manual_selection_is_not_sent_to_ai_orchestrator():
    container = bootstrap_application()
    result = container.intelligence_service.execute_automatic(
        prompt="Usar manual",
        capability="general_assistance",
        mode=RoutingMode.FREE_ONLY,
    )
    assert result.is_success is False
    assert result.data.requires_manual_handoff is True


def test_metrics_track_selection_success_and_failure_locally():
    container = bootstrap_application()
    container.intelligence_service.execute_automatic(
        prompt="Sucesso", mode=RoutingMode.LOCAL_FIRST
    )
    container.intelligence_service.route(
        prompt="", mode=RoutingMode.FREE_ONLY
    )
    snapshot = container.intelligence_service.metrics().data
    assert snapshot.selections == 1
    assert snapshot.successes == 1
    assert snapshot.failures == 1


def test_initial_profiles_do_not_claim_unconfigured_availability():
    profiles = bootstrap_application().intelligence_service.list_provider_profiles().data
    configured = {item.provider_id: item for item in profiles}
    assert configured["local-provider"].enabled is False
    assert configured["api-provider"].enabled is False
    assert configured["paid-provider"].enabled is False
    assert all("token" not in (item.notes or "").casefold() for item in profiles)


def test_application_container_preserves_the_legacy_constructor_contract():
    parameters = inspect.signature(ApplicationContainer).parameters

    assert tuple(parameters)[:18] == (
        "persistence_mode",
        "database",
        "registry",
        "provider",
        "ai_orchestrator",
        "mission_engine",
        "planner",
        "execution_engine",
        "memory_repository",
        "memory_engine",
        "project_repository",
        "project_engine",
        "workspace_engine",
        "workspace_manager",
        "mission_service",
        "memory_service",
        "project_service",
        "workspace_service",
    )
    assert parameters["provider_catalog"].default is None
    assert parameters["intelligence_service"].default is None


def test_intelligence_implementation_has_no_external_access_or_credentials():
    forbidden = (
        "requests",
        "selenium",
        "playwright",
        "cookie",
        "openai",
        "anthropic",
        "api_key",
        "password",
    )
    sources = "".join(
        path.read_text(encoding="utf-8").casefold()
        for path in __import__("pathlib").Path("Engines/Intelligence").glob("*.py")
    )
    assert not any(item in sources for item in forbidden)


@pytest.fixture
def intelligence_server():
    server = create_server(
        port=0,
        application=CompanionApplication.default(persistent=False),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def post(base: str, path: str, fields: dict[str, str]):
    request = Request(
        base + path,
        data=urlencode(fields).encode(),
        method="POST",
    )
    with urlopen(request, timeout=2) as response:
        return response.status, response.read().decode("utf-8")


def test_intelligence_http_route_and_manual_handoff_flow(intelligence_server):
    with urlopen(f"{intelligence_server}/intelligence", timeout=2) as response:
        page = response.read().decode("utf-8")
    assert response.status == HTTPStatus.OK
    assert "Intelligence Router" in page
    assert "Manual General Provider" in page

    status, routed = post(
        intelligence_server,
        "/intelligence/route",
        {
            "prompt": "Preparar análise",
            "capability": "general_assistance",
            "routing_mode": "free_only",
        },
    )
    assert status == HTTPStatus.OK
    assert "manual-general" in routed
    assert "Preparar análise" in routed
    assert "Provider recomendado" in routed

    status, created = post(
        intelligence_server,
        "/intelligence/handoffs",
        {"provider_id": "manual-general", "prompt": "Preparar análise"},
    )
    assert status == HTTPStatus.OK
    assert "ManualHandoff criado" in created
    handoff_id = created.split("/intelligence/handoffs/")[1].split(
        "/complete", 1
    )[0]

    status, completed = post(
        intelligence_server,
        f"/intelligence/handoffs/{handoff_id}/complete",
        {"response": "Análise concluída"},
    )
    assert status == HTTPStatus.OK
    assert "ManualHandoff concluído" in completed
    assert "Análise concluída" in completed


def test_existing_companion_routes_remain_compatible(intelligence_server):
    for path in ("/", "/workspaces", "/projects", "/missions", "/memory"):
        with urlopen(intelligence_server + path, timeout=2) as response:
            assert response.status == HTTPStatus.OK
