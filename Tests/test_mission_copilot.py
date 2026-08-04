from dataclasses import FrozenInstanceError
from http import HTTPStatus
import json
from pathlib import Path
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from Application import MissionCopilotResult
from Engines.Intelligence import HandoffStatus, RoutingMode
from Interfaces.Companion import CompanionApplication
from Interfaces.Companion.server import create_server


ACCEPTANCE_RESPONSE = {
    "summary": (
        "Plano inicial para substituição da banheira por base de duche."
    ),
    "suggested_actions": [
        "Confirmar medidas e posição do ralo",
        "Verificar canalização existente",
        "Remover banheira",
        "Regularizar e impermeabilizar a área",
        "Instalar e testar a base de duche",
    ],
    "risks": [
        "Incompatibilidade entre ralo existente e nova base",
        "Humidade oculta após remoção da banheira",
    ],
    "assumptions": [
        "A estrutura existente está em condições de receber a nova base"
    ],
}


def _acceptance_context(application: CompanionApplication):
    workspace = application.create_workspace(
        name="Empresa Remodelações",
        description="Operação de remodelações",
    ).data
    project = application.create_project(
        workspace_id=workspace.id,
        title="Remodelação Casa de Banho",
        client="Cliente Casa",
        address="Lisboa",
        description="Substituição da banheira por base de duche",
    ).data
    application.store_memory(
        workspace_id=workspace.id,
        category="levantamento",
        title="Canalização existente",
        content="O ralo precisa de confirmação no local.",
    )
    return workspace, project


def _create_acceptance_request(application: CompanionApplication):
    workspace, project = _acceptance_context(application)
    created = application.create_mission_copilot_request(
        workspace_id=workspace.id,
        project_id=project.id,
        title="Planejar a substituição da banheira por uma base de duche.",
        objective=(
            "Gerar sequência inicial de trabalho, riscos e informações que "
            "precisam ser verificadas."
        ),
        constraints=("Não executar ações automaticamente",),
        expected_result="Sequência inicial, riscos e verificações necessárias",
    )
    return workspace, project, created


def test_creates_mission_with_real_workspace_project_and_memory_context():
    application = CompanionApplication.default(persistent=False)
    workspace, project, created = _create_acceptance_request(application)

    assert created.is_success is True
    request = created.data
    assert request.mission.title.startswith("Planejar a substituição")
    assert request.context.workspace_id == workspace.id
    assert request.context.workspace_name == "Empresa Remodelações"
    assert request.context.project_id == project.id
    assert request.context.project_title == "Remodelação Casa de Banho"
    assert request.context.constraints == (
        "Não executar ações automaticamente",
    )
    assert request.context.memories[0].title == "Canalização existente"
    assert "O ralo precisa de confirmação no local." in request.prompt
    assert "Resultado esperado:" in request.prompt


def test_routes_free_only_and_never_selects_paid_provider():
    application = CompanionApplication.default(persistent=False)
    _, _, created = _create_acceptance_request(application)

    decision = created.data.decision

    assert decision.routing_mode is RoutingMode.FREE_ONLY
    assert decision.selected_provider_id == "manual-general"
    assert decision.selected_provider_id != "paid-provider"
    assert "paid-provider" not in decision.alternatives
    assert decision.requires_manual_handoff is True


def test_creates_handoff_and_preserves_prompt_and_relations():
    application = CompanionApplication.default(persistent=False)
    workspace, project, created = _create_acceptance_request(application)
    request = created.data

    handoff = application.create_mission_copilot_handoff(request.mission.id)

    assert handoff.is_success is True
    assert handoff.data.status is HandoffStatus.PENDING
    assert handoff.data.prompt == request.prompt
    assert handoff.data.workspace_id == workspace.id
    assert handoff.data.project_id == project.id
    assert handoff.data.mission_id == request.mission.id


def test_valid_json_builds_immutable_structured_result_and_preserves_raw():
    application = CompanionApplication.default(persistent=False)
    _, _, created = _create_acceptance_request(application)
    mission_id = created.data.mission.id
    handoff = application.create_mission_copilot_handoff(mission_id).data
    raw = "\n" + json.dumps(ACCEPTANCE_RESPONSE, ensure_ascii=False) + "\n"

    completed = application.complete_mission_copilot_handoff(
        mission_id,
        handoff.id,
        response=raw,
    )
    built = application.build_mission_copilot_result(
        mission_id,
        handoff.id,
    )

    assert completed.is_success is True
    assert built.is_success is True
    assert isinstance(built.data, MissionCopilotResult)
    assert built.data.raw_response == raw
    assert built.data.summary == ACCEPTANCE_RESPONSE["summary"]
    assert built.data.suggested_actions == tuple(
        ACCEPTANCE_RESPONSE["suggested_actions"]
    )
    assert built.data.risks == tuple(ACCEPTANCE_RESPONSE["risks"])
    assert built.data.assumptions == tuple(ACCEPTANCE_RESPONSE["assumptions"])
    with pytest.raises(FrozenInstanceError):
        built.data.summary = "alterado"


@pytest.mark.parametrize(
    ("response", "message"),
    (
        ("{invalid", "Resposta JSON inválida"),
        ("[]", "deve ser um objeto"),
        ('{"suggested_actions": "executar"}', "deve ser uma lista"),
    ),
)
def test_invalid_json_is_rejected_without_completing_handoff(
    response,
    message,
):
    application = CompanionApplication.default(persistent=False)
    _, _, created = _create_acceptance_request(application)
    mission_id = created.data.mission.id
    handoff = application.create_mission_copilot_handoff(mission_id).data

    completed = application.complete_mission_copilot_handoff(
        mission_id,
        handoff.id,
        response=response,
    )

    assert completed.is_success is False
    assert message in completed.message
    assert application.get_mission_copilot_handoff(
        mission_id
    ).data.status is HandoffStatus.PENDING


def test_missing_result_values_remain_absent():
    application = CompanionApplication.default(persistent=False)
    _, _, created = _create_acceptance_request(application)
    mission_id = created.data.mission.id
    handoff = application.create_mission_copilot_handoff(mission_id).data
    application.complete_mission_copilot_handoff(
        mission_id,
        handoff.id,
        response="{}",
    )

    result = application.build_mission_copilot_result(
        mission_id,
        handoff.id,
    ).data

    assert result.summary is None
    assert result.suggested_actions is None
    assert result.risks is None
    assert result.assumptions is None


def test_suggested_actions_are_not_executed_and_memory_is_explicit():
    application = CompanionApplication.default(persistent=False)
    workspace, project, created = _create_acceptance_request(application)
    mission_id = created.data.mission.id
    handoff = application.create_mission_copilot_handoff(mission_id).data
    application.complete_mission_copilot_handoff(
        mission_id,
        handoff.id,
        response=json.dumps(ACCEPTANCE_RESPONSE),
    )
    result = application.build_mission_copilot_result(
        mission_id,
        handoff.id,
    ).data

    before = application.list_memories(workspace_id=workspace.id).data
    stored = application.save_mission_copilot_result_as_memory(result.id)
    after = application.list_memories(workspace_id=workspace.id).data
    related_project = application.get_project(project.id).data

    assert len(before) == 1
    assert stored.is_success is True
    assert len(after) == 2
    assert after[0].mission_id == mission_id
    assert after[0].metadata["project_id"] == project.id
    assert related_project.mission_ids == (mission_id,)
    assert len(application.list_missions(workspace_id=workspace.id).data) == 1


def test_flow_works_without_project_or_memories():
    application = CompanionApplication.default(persistent=False)
    workspace = application.dashboard().active_workspace

    created = application.create_mission_copilot_request(
        workspace_id=workspace.id,
        title="Missão independente",
        objective="Produzir orientação sem inventar contexto",
    )

    assert created.is_success is True
    assert created.data.context.project_id is None
    assert created.data.context.memories == ()
    assert "Project:" not in created.data.prompt
    assert "Memories relevantes:" not in created.data.prompt


def test_new_service_contains_no_external_client_or_unsafe_evaluation():
    source = Path(
        "Application/services/mission_copilot_service.py"
    ).read_text(encoding="utf-8")

    assert "eval(" not in source
    assert "exec(" not in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urlopen(" not in source
    assert "import http.client" not in source
    assert "json.loads" in source


@pytest.fixture
def mission_copilot_server():
    application = CompanionApplication.default(persistent=False)
    workspace, project = _acceptance_context(application)
    server = create_server(port=0, application=application)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}", application, workspace, project
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _post(base: str, path: str, fields: dict[str, str]):
    request = Request(
        base + path,
        data=urlencode(fields).encode(),
        method="POST",
    )
    with urlopen(request, timeout=2) as response:
        return response.status, response.read().decode("utf-8")


def test_complete_acceptance_flow_over_http(mission_copilot_server):
    base, application, workspace, project = mission_copilot_server
    status, created = _post(
        base,
        "/missions",
        {
            "experience": "mission_copilot",
            "workspace_id": workspace.id,
            "project_id": project.id,
            "title": (
                "Planejar a substituição da banheira por uma base de duche."
            ),
            "objective": (
                "Gerar sequência inicial de trabalho, riscos e informações "
                "que precisam ser verificadas."
            ),
            "expected_result": "Sequência, riscos e verificações",
        },
    )
    mission_id = created.split("/missions/")[1].split("/copilot", 1)[0]

    status_handoff, handoff_page = _post(
        base,
        f"/missions/{mission_id}/copilot",
        {"confirm": "yes"},
    )
    handoff_id = handoff_page.split("/handoffs/")[1].split("/complete", 1)[0]
    status_result, result_page = _post(
        base,
        f"/missions/{mission_id}/handoffs/{handoff_id}/complete",
        {"response": json.dumps(ACCEPTANCE_RESPONSE, ensure_ascii=False)},
    )
    result_id = result_page.split("/results/")[1].split("/memory", 1)[0]
    status_memory, memory_page = _post(
        base,
        f"/missions/{mission_id}/results/{result_id}/memory",
        {"confirm": "yes"},
    )
    with urlopen(f"{base}/missions/{mission_id}", timeout=2) as response:
        detail = response.read().decode("utf-8")

    assert status == status_handoff == status_result == status_memory == 200
    assert "FREE ONLY" in created
    assert "manual-general" in created
    assert "Paid Provider" not in created
    assert "Prompt preservado" in handoff_page
    assert ACCEPTANCE_RESPONSE["summary"] in result_page
    assert "Nada foi executado automaticamente." in result_page
    assert "Resultado salvo na Memory" in memory_page
    assert "Remodelação Casa de Banho" in detail
    assert application.get_project(project.id).data.mission_ids == (mission_id,)


def test_home_and_legacy_mission_route_remain_compatible(
    mission_copilot_server,
):
    base, _, _, _ = mission_copilot_server
    with urlopen(base + "/", timeout=2) as response:
        home = response.read().decode("utf-8")
    status, legacy = _post(
        base,
        "/missions",
        {"title": "Fluxo legado", "objective": "Preservar execução atual"},
    )

    assert "Criar missão com Intelligence" in home
    assert 'name="experience" value="mission_copilot"' in home
    assert status == HTTPStatus.OK
    assert "Relatório final" in legacy
