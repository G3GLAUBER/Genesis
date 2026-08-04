from dataclasses import FrozenInstanceError
from decimal import Decimal
from http import HTTPStatus
import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from Application import ApplicationContainer, bootstrap_application
from Engines.Intelligence import CostTier, RoutingMode
from Engines.Remodeling import ProposalStatus, RemodelingBrief
from Interfaces.Companion import CompanionApplication
from Interfaces.Companion.server import create_server


def proposal_payload() -> dict:
    return {
        "phases": [
            {
                "order": 2,
                "title": "Impermeabilização e revestimento",
                "description": "Impermeabilizar e instalar porcelanato.",
                "dependencies": [1],
                "capability": "general_assistance",
                "estimated_duration": "4 dias",
                "materials": ["porcelanato", "membrana impermeável"],
                "risks": ["humidade residual"],
            },
            {
                "order": 1,
                "title": "Visita técnica",
                "description": "Confirmar medidas, canalização e eletricidade.",
                "dependencies": [],
                "materials": [],
                "risks": ["infraestrutura oculta"],
            },
        ],
        "risks": ["humidade", "alterações hidráulicas imprevistas"],
        "missing_information": ["fotografias"],
        "suggested_missions": [
            {
                "title": "Executar remodelação aprovada",
                "objective": "Executar as fases aprovadas com testes finais.",
            }
        ],
        "suggested_memories": [
            {
                "category": "materiais",
                "title": "Porcelanato escolhido",
                "content": "Formato previsto: 1,20 m × 0,60 m.",
            }
        ],
        "preliminary_budget": {
            "currency": "EUR",
            "line_items": [
                {
                    "category": "materiais",
                    "description": "Porcelanato",
                    "quantity": 10,
                    "unit": "m2",
                    "unit_price": 25,
                    "total": 999,
                    "source": "estimativa manual",
                },
                {
                    "category": "resíduos",
                    "description": "Remoção de entulho",
                    "total": 100,
                    "source": "estimativa manual",
                },
            ],
            "contingency_rate": 0.10,
            "assumptions": ["sem impostos configurados"],
            "confidence_level": "low",
        },
        "assumptions": ["levantamento técnico ainda necessário"],
    }


@pytest.fixture
def remodeling_context():
    container = bootstrap_application()
    workspace = container.workspace_service.create(
        name="Empresa Remodelações", description="Caso-piloto"
    ).data
    project = container.project_service.create(
        workspace_id=workspace.id,
        title="Remodelação Casa de Banho",
        client="Cliente teste",
        address="Lisboa",
        description="Remodelação integral",
    ).data
    return container, workspace, project


def create_brief(container, workspace, project, **overrides):
    values = {
        "project_id": project.id,
        "workspace_id": workspace.id,
        "project_type": "Casa de banho",
        "room_length": "2.5",
        "room_width": "1.9",
        "room_height": "2.6",
        "current_condition": "Banheira, revestimento e pavimento existentes.",
        "desired_result": (
            "Retirar banheira, instalar base de duche, rever canalização, "
            "eletricidade e impermeabilização, móvel, lavatório, pintura e entulho."
        ),
        "known_materials": ("porcelanato 1,20 m × 0,60 m",),
        "client_preferences": ("acabamento completo",),
    }
    values.update(overrides)
    return container.remodeling_service.create_brief(**values)


def generated_proposal(container, workspace, project):
    brief = create_brief(container, workspace, project).data
    requested = container.remodeling_service.request_proposal(brief.id)
    handoff = requested.data.handoff
    completed = container.remodeling_service.complete_handoff(
        handoff.id, response=json.dumps(proposal_payload())
    )
    assert completed.is_success
    proposal = container.remodeling_service.build_proposal(handoff.id)
    assert proposal.is_success, proposal.message
    return brief, requested.data, proposal.data


def test_valid_brief_is_normalized_immutable_and_does_not_modify_input(
    remodeling_context,
):
    container, workspace, project = remodeling_context
    materials = ["porcelanato"]
    created = create_brief(
        container, workspace, project, known_materials=materials
    )
    materials.append("tinta")

    assert created.is_success
    assert created.data.room_length == Decimal("2.5")
    assert created.data.known_materials == ("porcelanato",)
    with pytest.raises(FrozenInstanceError):
        created.data.notes = "alterada"


@pytest.mark.parametrize("field,value", [("room_length", 0), ("room_width", -1)])
def test_brief_rejects_non_positive_dimensions(remodeling_context, field, value):
    container, workspace, project = remodeling_context
    result = create_brief(container, workspace, project, **{field: value})
    assert result.is_success is False
    assert "positivo" in result.message


def test_brief_requires_existing_related_project_and_workspace(remodeling_context):
    container, workspace, project = remodeling_context
    result = create_brief(container, workspace, project, project_id="missing")
    assert result.is_success is False
    assert result.message == "Projeto não encontrado"


def test_missing_information_is_explicit_but_does_not_block(remodeling_context):
    container, workspace, project = remodeling_context
    brief = create_brief(
        container,
        workspace,
        project,
        room_length=None,
        room_width=None,
        room_height=None,
        known_materials=(),
    ).data
    missing = container.remodeling_service.identify_missing_information(brief.id)
    assert missing.is_success
    assert "medidas completas do espaço" in missing.data
    assert "materiais escolhidos" in missing.data
    assert "limite orçamental" in missing.data


def test_request_uses_free_only_manual_provider_and_context(remodeling_context):
    container, workspace, project = remodeling_context
    brief = create_brief(container, workspace, project).data
    result = container.remodeling_service.request_proposal(brief.id)
    request = result.data
    profile = container.provider_catalog.get(
        request.decision.selected_provider_id
    ).data

    assert result.is_success
    assert request.status is ProposalStatus.DRAFT
    assert request.decision.routing_mode is RoutingMode.FREE_ONLY
    assert request.decision.requires_manual_handoff is True
    assert profile.cost_tier is not CostTier.PAID
    assert request.handoff.workspace_id == workspace.id
    assert request.handoff.project_id == project.id
    assert "2.5 x 1.9 x 2.6" in request.handoff.prompt
    assert "phases" in request.handoff.prompt
    assert "preliminary_budget" in request.handoff.prompt


def test_valid_json_preserves_raw_response_and_builds_ordered_proposal(
    remodeling_context,
):
    container, workspace, project = remodeling_context
    raw = json.dumps(proposal_payload())
    brief = create_brief(container, workspace, project).data
    request = container.remodeling_service.request_proposal(brief.id).data
    container.remodeling_service.complete_handoff(
        request.handoff.id, response=raw
    )
    result = container.remodeling_service.build_proposal(request.handoff.id)

    assert result.is_success
    assert result.data.raw_response == raw
    assert result.data.status is ProposalStatus.GENERATED
    assert [phase.order for phase in result.data.phases] == [1, 2]
    assert result.data.phases[1].dependencies == (result.data.phases[0].id,)
    assert "humidade" in result.data.risks
    with pytest.raises(FrozenInstanceError):
        result.data.status = ProposalStatus.APPROVED


def test_invalid_json_and_invalid_dependencies_are_controlled(remodeling_context):
    container, workspace, project = remodeling_context
    brief = create_brief(container, workspace, project).data
    request = container.remodeling_service.request_proposal(brief.id).data
    container.remodeling_service.complete_handoff(
        request.handoff.id, response="{invalid"
    )
    invalid = container.remodeling_service.build_proposal(request.handoff.id)
    assert invalid.is_success is False
    assert "JSON inválido" in invalid.message

    second = container.remodeling_service.request_proposal(brief.id).data
    payload = proposal_payload()
    payload["phases"][0]["dependencies"] = [99]
    container.remodeling_service.complete_handoff(
        second.handoff.id, response=json.dumps(payload)
    )
    dependency = container.remodeling_service.build_proposal(second.handoff.id)
    assert dependency.is_success is False
    assert "dependencies" in dependency.message


def test_budget_is_preliminary_estimated_and_recalculated(remodeling_context):
    container, workspace, project = remodeling_context
    _, _, proposal = generated_proposal(container, workspace, project)
    budget = proposal.preliminary_budget

    assert budget.currency == "EUR"
    assert budget.line_items[0].total == Decimal("250.00")
    assert budget.subtotal == Decimal("350.00")
    assert budget.contingency == Decimal("35.00")
    assert budget.total == Decimal("385.00")
    assert all(item.is_estimate for item in budget.line_items)
    assert "sem impostos configurados" in budget.assumptions


def test_proposal_requires_review_and_approval_before_idempotent_apply(
    remodeling_context,
):
    container, workspace, project = remodeling_context
    _, _, proposal = generated_proposal(container, workspace, project)

    assert container.remodeling_service.apply_proposal(proposal.id).is_success is False
    reviewed = container.remodeling_service.review_proposal(proposal.id)
    assert reviewed.data.status is ProposalStatus.REVIEWED
    approved = container.remodeling_service.approve_proposal(proposal.id)
    assert approved.data.status is ProposalStatus.APPROVED
    applied = container.remodeling_service.apply_proposal(proposal.id)
    assert applied.is_success
    assert len(applied.data.mission_ids) == 1
    assert len(applied.data.memory_ids) == 2
    assert container.remodeling_service.apply_proposal(proposal.id).is_success is False

    persisted_project = container.project_service.get(project.id).data
    assert applied.data.mission_ids[0] in persisted_project.mission_ids
    memories = container.memory_service.history(workspace_id=workspace.id).data
    assert {item.metadata["proposal_id"] for item in memories} == {proposal.id}


def test_rejected_proposal_cannot_be_applied(remodeling_context):
    container, workspace, project = remodeling_context
    _, _, proposal = generated_proposal(container, workspace, project)
    rejected = container.remodeling_service.reject_proposal(proposal.id)
    assert rejected.data.status is ProposalStatus.REJECTED
    assert container.remodeling_service.apply_proposal(proposal.id).is_success is False


def test_bootstrap_and_companion_public_apis_remain_additive():
    container = bootstrap_application()
    assert container.remodeling_service is not None
    assert container.remodeling_engine is not None
    parameters = __import__("inspect").signature(ApplicationContainer).parameters
    assert parameters["remodeling_service"].default is None
    assert CompanionApplication.default(persistent=False).list_workspaces().is_success


def test_implementation_has_no_external_access_credentials_or_unsafe_parser():
    sources = "".join(
        path.read_text(encoding="utf-8").casefold()
        for path in Path("Engines/Remodeling").glob("*.py")
    )
    forbidden = (
        "requests",
        "urlopen",
        "selenium",
        "playwright",
        "api_key",
        "password",
        "pickle",
        "eval(",
    )
    assert not any(item in sources for item in forbidden)


@pytest.fixture
def remodeling_server():
    app = CompanionApplication.default(persistent=False)
    workspace = app.create_workspace(
        name="Empresa Remodelações", description="HTTP"
    ).data
    app.create_project(
        workspace_id=workspace.id,
        title="Remodelação Casa de Banho",
        client="Cliente HTTP",
        address="Lisboa",
        description="Caso HTTP",
    )
    server = create_server(port=0, application=app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}", app
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def post(base: str, path: str, fields: dict[str, str]):
    request = Request(base + path, data=urlencode(fields).encode(), method="POST")
    try:
        with urlopen(request, timeout=3) as response:
            return response.status, response.read().decode()
    except HTTPError as error:
        return error.code, error.read().decode()


def test_remodeling_http_routes_and_previous_routes(remodeling_server):
    base, app = remodeling_server
    workspace = app.list_workspaces().data[-1]
    project = app.list_projects(workspace_id=workspace.id).data[0]
    with urlopen(base + "/remodeling", timeout=3) as response:
        page = response.read().decode()
    assert response.status == HTTPStatus.OK
    assert "Remodelação com aprovação humana" in page
    assert "Não constitui preço final" not in page

    status, created = post(
        base,
        "/remodeling/briefs",
        {
            "workspace_id": workspace.id,
            "project_id": project.id,
            "project_type": "Casa de banho",
            "room_length": "2.5",
            "room_width": "1.9",
            "room_height": "2.6",
            "current_condition": "Banheira existente",
            "desired_result": "Base de duche e acabamento completo",
        },
    )
    assert status == HTTPStatus.OK
    assert "Brief criado" in created
    brief = app.list_remodeling_briefs().data[-1]

    status, requested = post(
        base, "/remodeling/proposals", {"brief_id": brief.id}
    )
    assert status == HTTPStatus.OK
    assert "FREE ONLY · MANUAL" in requested
    handoff = app.list_manual_handoffs().data[-1]

    status, built = post(
        base,
        f"/remodeling/handoffs/{handoff.id}/complete",
        {"response": json.dumps(proposal_payload())},
    )
    assert status == HTTPStatus.OK
    assert "Estimativa preliminar" in built
    proposal = app.list_remodeling_proposals().data[-1]

    with urlopen(
        f"{base}/remodeling/proposals/{proposal.id}", timeout=3
    ) as response:
        assert response.status == HTTPStatus.OK
        assert "Revisão humana obrigatória" in response.read().decode()
    for action in ("review", "approve", "apply"):
        status, _ = post(
            base, f"/remodeling/proposals/{proposal.id}/{action}", {"confirm": "1"}
        )
        assert status == HTTPStatus.OK
    second_request = app.request_remodeling_proposal(brief.id).data
    app.complete_remodeling_handoff(
        second_request.handoff.id,
        response=json.dumps(proposal_payload()),
    )
    second_proposal = app.list_remodeling_proposals().data[-1]
    status, rejected = post(
        base,
        f"/remodeling/proposals/{second_proposal.id}/reject",
        {"confirm": "1"},
    )
    assert status == HTTPStatus.OK
    assert "Proposta rejeitada" in rejected
    for path in ("/", "/projects", "/missions", "/memory", "/intelligence"):
        with urlopen(base + path, timeout=3) as response:
            assert response.status == HTTPStatus.OK
