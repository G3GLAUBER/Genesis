from http import HTTPStatus
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from Interfaces.Companion import CompanionApplication
from Interfaces.Companion.server import create_server


@pytest.fixture
def companion_server():
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
        assert thread.is_alive() is False


def test_home_page_loads_orientation_and_environment(companion_server):
    with urlopen(f"{companion_server}/", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert "Gênesis" in content
    assert "Ambiente:" in content
    assert "Veja o que merece sua atenção agora." in content
    assert 'href="/projects#new-project">Criar primeiro projeto</a>' in content
    assert "Workspace ativo" in content
    assert "Genesis 0.1" in content
    assert "SQLite local" not in content
    assert "Memória local" in content
    assert content.count('<svg class="icon"') >= 7


def test_command_center_has_attention_intelligence_and_timeline(
    companion_server,
):
    with urlopen(f"{companion_server}/", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    for label in (
        "Command Center",
        "Projects",
        "Intelligence",
        "Memory",
        "Remodeling",
        "Application Health",
        "Settings",
    ):
        assert label in content
    assert 'id="attention-title">Atenção agora</h2>' in content
    assert 'class="action-overview"' in content
    assert "Genesis Intelligence" in content
    assert "Timeline" in content


def test_command_center_exposes_secondary_actions_and_accessibility(
    companion_server,
):
    with urlopen(f"{companion_server}/", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert 'class="skip-link" href="#main-content"' in content
    assert 'id="main-content"' in content
    assert 'aria-current="page"' in content
    assert "Serviços disponíveis" in content
    assert 'class="secondary-actions"' in content
    assert 'href="/workspaces">Workspace</a>' in content
    assert 'href="/projects">Projeto</a>' in content
    assert 'href="/memory">Memória</a>' in content
    assert content.count('class="button-link primary-button"') == 1
    assert content.count("<small>Workspace ativo</small>") == 1
    assert 'aria-labelledby="attention-title"' in content


def test_empty_projects_page_keeps_table_structure(companion_server):
    with urlopen(f"{companion_server}/projects", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert 'class="projects-table"' in content
    assert 'class="table-empty"' in content
    assert "Nenhum projeto neste Workspace." in content


def test_post_executes_mission_and_renders_report(companion_server):
    payload = urlencode(
        {
            "title": "Validar Companion",
            "objective": "Executar uma missão pela interface web",
        }
    ).encode()
    request = Request(
        f"{companion_server}/missions",
        data=payload,
        method="POST",
    )

    with urlopen(request, timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert "Validar Companion" in content
    assert "Plano demonstrativo" in content
    assert "Provider: <strong>fake</strong>" in content
    assert content.count("Provider: fake") == 3
    assert "COMPLETED" in content
    assert "Relatório final" in content


def test_invalid_form_returns_bad_request(companion_server):
    payload = urlencode({"title": "", "objective": "Objetivo"}).encode()
    request = Request(
        f"{companion_server}/missions",
        data=payload,
        method="POST",
    )

    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=2)

    assert error.value.code == HTTPStatus.BAD_REQUEST


def test_unknown_route_returns_not_found(companion_server):
    with pytest.raises(HTTPError) as error:
        urlopen(f"{companion_server}/missing", timeout=2)

    assert error.value.code == HTTPStatus.NOT_FOUND


def test_workspace_page_lists_default_workspace(companion_server):
    with urlopen(f"{companion_server}/workspaces", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert "Workspaces ativos" in content
    assert "Workspace principal" in content
    assert 'action="/workspaces"' in content


def test_http_flow_creates_opens_workspace_and_associates_mission(
    companion_server,
):
    create_payload = urlencode(
        {"name": "Workspace HTTP", "description": "Integração"}
    ).encode()
    create_request = Request(
        f"{companion_server}/workspaces",
        data=create_payload,
        method="POST",
    )
    with urlopen(create_request, timeout=2) as response:
        created_content = response.read().decode("utf-8")

    workspace_path = created_content.split(
        'href="/workspaces/',
    )[-1].split('"', 1)[0]
    mission_payload = urlencode(
        {
            "title": "Missão no Workspace",
            "objective": "Validar associação HTTP",
            "workspace_id": workspace_path,
        }
    ).encode()
    mission_request = Request(
        f"{companion_server}/missions",
        data=mission_payload,
        method="POST",
    )
    with urlopen(mission_request, timeout=2) as response:
        mission_content = response.read().decode("utf-8")
    with urlopen(
        f"{companion_server}/workspaces/{workspace_path}",
        timeout=2,
    ) as response:
        workspace_content = response.read().decode("utf-8")

    assert "Workspace HTTP" in created_content
    assert "Workspace:\n    Workspace HTTP" in mission_content
    assert "Missão no Workspace" in mission_content
    assert "Workspace aberto" in workspace_content
    assert "Nenhuma missão associada" not in workspace_content


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        ("/", "Command Center"),
        ("/workspaces", "Workspaces ativos"),
        ("/projects", "Criar projeto"),
        ("/missions", "Criar missão"),
        ("/memory", "Nova memória"),
        ("/executions", "Nenhuma execução registrada"),
        ("/doctor", "Application Health"),
        ("/settings", "Configurações"),
    ),
)
def test_operational_pages_are_available(companion_server, path, expected):
    with urlopen(f"{companion_server}{path}", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert expected in content
    assert "Command Center" in content
    assert "Memory" in content
    assert "Projects" in content
    assert "Application Health" in content


def test_stylesheet_is_served_separately(companion_server):
    with urlopen(
        f"{companion_server}/static/styles.css",
        timeout=2,
    ) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert response.headers["Content-Type"] == "text/css; charset=utf-8"
    assert ".sidebar" in content
    assert "--color-focus" in content
    assert "--space-4" in content
    assert "--radius-card" in content
    assert "--motion-base" in content
    assert "--z-sticky" in content


@pytest.mark.parametrize(
    "path",
    (
        "/",
        "/projects",
        "/intelligence",
        "/memory",
        "/remodeling",
        "/settings",
        "/doctor",
    ),
)
def test_app_shell_v1_is_shared_by_primary_routes(companion_server, path):
    with urlopen(f"{companion_server}{path}", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert 'class="app-shell"' in content
    assert 'aria-label="Navegação principal"' in content
    assert 'class="header-context"' in content
    assert 'class="header-actions"' in content
    assert 'class="skip-link" href="#main-content"' in content
    assert 'id="page-title"' in content
    assert "Workspace ativo" in content
    assert "Serviços disponíveis" in content
    assert "Genesis 0.1" in content
    for destination in (
        "Command Center",
        "Projects",
        "Intelligence",
        "Memory",
        "Remodeling",
        "Settings",
        "Application Health",
    ):
        assert destination in content


def test_app_shell_v1_exposes_reusable_states_and_responsive_tokens(
    companion_server,
):
    with urlopen(
        f"{companion_server}/static/styles.css",
        timeout=2,
    ) as response:
        content = response.read().decode("utf-8")

    for selector in (
        ".state-loading",
        ".empty-state",
        ".state-error",
        ".state-success",
        ".state-degraded",
        ".is-disabled",
        ".timeline-item",
        ".metric-card",
        ".projects-table",
    ):
        assert selector in content
    assert "@media (max-width: 1180px)" in content
    assert "@media (max-width: 860px)" in content
    assert "@media (max-width: 620px)" in content
    assert "@media (prefers-reduced-motion: reduce)" in content


def test_empty_command_center_explains_timeline_and_onboarding(
    companion_server,
):
    with urlopen(f"{companion_server}/", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert "Construa seu primeiro fluxo" in content
    assert "Crie um Workspace." in content
    assert "Crie um Projeto." in content
    assert "Registre sua primeira missão ou memória." in content
    assert (
        "O Genesis registra decisões, missões, memórias e projetos para que "
        "você nunca perca contexto."
    ) in content
    assert "Genesis Intelligence" in content


def test_command_center_is_structurally_responsive_and_has_one_primary_cta(
    companion_server,
):
    with urlopen(f"{companion_server}/", timeout=2) as response:
        content = response.read().decode("utf-8")
    with urlopen(f"{companion_server}/static/styles.css", timeout=2) as response:
        css = response.read().decode("utf-8")

    assert content.count('class="button-link primary-button"') == 1
    assert 'aria-label="Atalhos secundários"' in content
    assert '<main class="main-content" id="main-content">' in content
    assert ".priority-item .text-action" in css
    assert ".action-overview, .onboarding ol" in css


def test_http_memory_flow_stores_searches_and_filters(companion_server):
    payload = urlencode(
        {
            "category": "decisão",
            "title": "Interface operacional",
            "content": "Dashboard sem frameworks",
        }
    ).encode()
    request = Request(
        f"{companion_server}/memory",
        data=payload,
        method="POST",
    )
    with urlopen(request, timeout=2) as response:
        stored = response.read().decode("utf-8")
    with urlopen(
        f"{companion_server}/memory?q=dashboard&category=decis%C3%A3o",
        timeout=2,
    ) as response:
        searched = response.read().decode("utf-8")

    assert "Memória armazenada" in stored
    assert "Interface operacional" in stored
    assert "Interface operacional" in searched
    assert "Workspace:" in searched


def test_mission_page_lists_execution_after_post(companion_server):
    payload = urlencode(
        {"title": "Missão listada", "objective": "Aparecer na página"}
    ).encode()
    request = Request(
        f"{companion_server}/missions",
        data=payload,
        method="POST",
    )
    with urlopen(request, timeout=2) as response:
        posted = response.read().decode("utf-8")
    with urlopen(f"{companion_server}/missions", timeout=2) as response:
        listed = response.read().decode("utf-8")

    assert "Missão listada" in posted
    assert "Missão listada" in listed
    assert "COMPLETED" in listed


def test_application_health_is_distinct_from_genesis_doctor(companion_server):
    with urlopen(f"{companion_server}/doctor", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert "Application Health" in content
    assert "Saúde dos Serviços" in content
    assert "Serviços disponíveis" in content
    assert "DISPONÍVEL" in content
    assert "SAUDÁVEL" not in content
    assert "Health Score" not in content
    assert "Indicador operacional. Não substitui o Genesis Doctor." in content
    assert "SQLite conectado" in content
    assert "Modo persistente" in content


def test_http_project_flow_creates_lists_and_updates_dashboard(companion_server):
    payload = urlencode(
        {
            "title": "Empresa Remodelações",
            "client": "Cliente HTTP",
            "address": "Rua da Obra, 10",
            "description": "Remodelação integral",
        }
    ).encode()
    request = Request(
        f"{companion_server}/projects",
        data=payload,
        method="POST",
    )

    with urlopen(request, timeout=2) as response:
        created = response.read().decode("utf-8")
    with urlopen(f"{companion_server}/projects", timeout=2) as response:
        listed = response.read().decode("utf-8")
    with urlopen(f"{companion_server}/", timeout=2) as response:
        dashboard = response.read().decode("utf-8")

    assert "Projeto criado" in created
    assert "Empresa Remodelações" in created
    assert "Cliente HTTP" in listed
    assert 'class="projects-table"' in listed
    assert "<th>Projeto</th>" in listed
    assert "<th>Cliente</th>" in listed
    assert "<th>Status</th>" in listed
    assert "<th>Criado</th>" in listed
    assert "1 projeto(s) em andamento." in dashboard
    assert "Este projeto ainda não tem atividade." in dashboard
    assert "Empresa Remodelações" in dashboard


def test_http_project_validation_returns_bad_request(companion_server):
    payload = urlencode(
        {"title": "", "client": "Cliente", "address": "Morada"}
    ).encode()
    request = Request(
        f"{companion_server}/projects",
        data=payload,
        method="POST",
    )

    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=2)

    assert error.value.code == HTTPStatus.BAD_REQUEST
