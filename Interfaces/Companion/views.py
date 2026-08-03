from __future__ import annotations

from html import escape
from pathlib import Path
from string import Template
from typing import Any

from Core.configuration import Configuration
from Core.result import Result
from Interfaces.Companion.application import (
    CompanionActivity,
    CompanionDashboard,
    CompanionExecution,
)
from Interfaces.Workspace import render_workspace_page


_ROOT = Path(__file__).resolve().parent
_PAGE_TITLES = {
    "dashboard": "Dashboard",
    "workspaces": "Workspaces",
    "projects": "Projetos",
    "missions": "Missões",
    "memory": "Memórias",
    "executions": "Execuções",
    "doctor": "Application Health",
    "settings": "Configurações",
    "intelligence": "Intelligence",
}


def render_page(
    config: Configuration,
    result: Result | None = None,
    *,
    dashboard: CompanionDashboard | None = None,
    page: str = "dashboard",
    workspaces: tuple[Any, ...] = (),
    projects: tuple[Any, ...] = (),
    workspace: Any | None = None,
    missions: tuple[Any, ...] = (),
    memories: tuple[Any, ...] = (),
    executions: tuple[CompanionExecution, ...] = (),
    timeline: tuple[CompanionActivity, ...] = (),
    query: str = "",
    category: str = "",
    provider_profiles: tuple[Any, ...] = (),
    manual_handoffs: tuple[Any, ...] = (),
) -> str:
    title = _PAGE_TITLES.get(page, "Dashboard")
    content = _page_content(
        page=page,
        result=result,
        dashboard=dashboard,
        workspaces=workspaces,
        projects=projects,
        workspace=workspace,
        missions=missions,
        memories=memories,
        executions=executions,
        timeline=timeline,
        query=query,
        category=category,
        provider_profiles=provider_profiles,
        manual_handoffs=manual_handoffs,
    )
    template = Template(
        (_ROOT / "templates" / "layout.html").read_text(encoding="utf-8")
    )
    return template.safe_substitute(
        title=escape(title),
        system_name=escape(config.system_name),
        version=escape(config.version),
        environment=escape(config.environment),
        active_workspace=escape(_active_workspace_name(dashboard)),
        storage_mode=escape(_storage_mode(dashboard)),
        services_available=_services_available(dashboard),
        health_class=_health_class(dashboard),
        sidebar=_render_sidebar(page),
        page_title=escape(title),
        page_subtitle=_page_subtitle(page),
        content=content,
    )


def stylesheet() -> bytes:
    return (_ROOT / "static" / "styles.css").read_bytes()


def _page_content(**context) -> str:
    page = context["page"]
    if page == "workspaces":
        return render_workspace_page(
            context["workspaces"],
            selected=context["workspace"],
            result=context["result"],
        )
    if page == "missions":
        return _render_missions(
            context["missions"],
            context["executions"],
            context["result"],
            context["dashboard"],
        )
    if page == "projects":
        return _render_projects(
            context["projects"],
            context["result"],
            context["dashboard"],
        )
    if page == "memory":
        return _render_memory(
            context["memories"],
            context["result"],
            context["dashboard"],
            query=context["query"],
            category=context["category"],
        )
    if page == "executions":
        return _render_executions(context["executions"])
    if page == "doctor":
        return _render_doctor(context["dashboard"])
    if page == "settings":
        return _render_settings()
    if page == "intelligence":
        return _render_intelligence(
            context["provider_profiles"],
            context["manual_handoffs"],
            context["result"],
            context["dashboard"],
            context["projects"],
        )
    return _render_dashboard(
        context["dashboard"],
        context["timeline"],
        context["result"],
    )


def _render_sidebar(active_page: str) -> str:
    items = (
        ("dashboard", "/", "dashboard", "Dashboard"),
        ("workspaces", "/workspaces", "workspaces", "Workspaces"),
        ("projects", "/projects", "projects", "Projetos"),
        ("missions", "/missions", "missions", "Missões"),
        ("memory", "/memory", "memory", "Memórias"),
        ("executions", "/executions", "executions", "Execuções"),
        ("intelligence", "/intelligence", "intelligence", "Intelligence"),
        ("doctor", "/doctor", "health", "Saúde dos Serviços"),
        ("settings", "/settings", "settings", "Configurações"),
    )
    return "".join(
        f'<a class="nav-item{" active" if key == active_page else ""}" '
        f'href="{href}"{_aria_current(key, active_page)}>'
        f'{_icon(icon)}<span>{label}</span></a>'
        for key, href, icon, label in items
    )


def _aria_current(item: str, active_page: str) -> str:
    return ' aria-current="page"' if item == active_page else ""


def _icon(name: str) -> str:
    paths = {
        "dashboard": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
        "workspaces": '<path d="M4 5h6l2 2h8v12H4z"/>',
        "projects": '<path d="M4 7h16v13H4zM8 7V4h8v3M8 12h8"/>',
        "missions": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="m15 9 5-5"/>',
        "memory": '<path d="M8 4h8a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3zM9 9h6M9 13h6"/>',
        "executions": '<path d="m9 7 8 5-8 5z"/><circle cx="12" cy="12" r="10"/>',
        "intelligence": '<path d="M12 3a6 6 0 0 0-3 11.2V18h6v-3.8A6 6 0 0 0 12 3zM9 21h6M12 3V1M4.2 5.2 2.8 3.8M19.8 5.2l1.4-1.4"/>',
        "health": '<path d="M3 12h4l2-5 4 10 2-5h6"/>',
        "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
        "storage": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>',
    }
    return (
        '<svg class="icon" aria-hidden="true" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{paths[name]}</svg>'
    )


def _active_workspace_name(dashboard: CompanionDashboard | None) -> str:
    if dashboard is None or dashboard.active_workspace is None:
        return "Nenhum Workspace"
    return dashboard.active_workspace.name


def _storage_mode(dashboard: CompanionDashboard | None) -> str:
    return dashboard.storage_label if dashboard else "Indisponível"


def _services_available(dashboard: CompanionDashboard | None) -> str:
    if dashboard is None:
        return "0/3"
    return f"{dashboard.available_service_count}/{dashboard.service_count}"


def _health_class(dashboard: CompanionDashboard | None) -> str:
    if dashboard and dashboard.application_health == "DISPONÍVEL":
        return "service-dot available"
    return "service-dot degraded"


def _page_subtitle(page: str) -> str:
    subtitles = {
        "dashboard": "Visão operacional do seu Genesis local",
        "workspaces": "Organize missões e memórias por contexto",
        "projects": "Organize obras, clientes e missões reais",
        "missions": "Crie, planeje e execute objetivos",
        "memory": "Consulte o conhecimento operacional do Workspace",
        "executions": "Acompanhe resultados e providers",
        "doctor": "Disponibilidade local dos Application Services",
        "settings": "Preferências da instância local",
        "intelligence": "Roteamento explicável com recursos gratuitos primeiro",
    }
    return escape(subtitles.get(page, "Genesis Companion"))


def _render_dashboard(
    dashboard: CompanionDashboard | None,
    timeline: tuple[CompanionActivity, ...],
    result: Result | None,
) -> str:
    if dashboard is None:
        return '<section class="panel error">Dashboard indisponível.</section>'
    active = dashboard.active_workspace
    active_name = active.name if active is not None else "Nenhum Workspace"
    metrics = (
        (
            "Projetos",
            str(
                dashboard.active_project_count
                + dashboard.completed_project_count
            ),
            "projects",
            f"Projetos ativos: {dashboard.active_project_count} · "
            f"Projetos concluídos: {dashboard.completed_project_count}",
        ),
        ("Missões", str(dashboard.mission_count), "missions", "No Workspace ativo"),
        ("Memórias", str(dashboard.memory_count), "memory", "Registros disponíveis"),
        ("Execuções", str(dashboard.execution_count), "executions", "Processamentos locais"),
        ("Workspaces", str(dashboard.workspace_count), "workspaces", active_name),
        (
            "Application Health",
            dashboard.application_health,
            "health",
            f"{dashboard.available_service_count}/{dashboard.service_count} services",
        ),
    )
    cards = "".join(
        f'<article class="metric-card {css}"><div class="metric-icon">'
        f'{_icon(css)}</div><div><span>{escape(label)}</span>'
        f'<strong>{escape(value)}</strong><small>{escape(description)}</small>'
        f'</div></article>'
        for label, value, css, description in metrics
    )
    feedback = _render_feedback(result)
    result_content = _render_mission_result(result) if result else ""
    return f"""<section class="dashboard-actions" aria-label="Ações rápidas">
  <div><span class="eyebrow">Workspace atual</span><strong>{escape(active_name)}</strong></div>
  <nav><a class="quick-link" href="/workspaces">+ Workspace</a>
    <a class="quick-link" href="/projects">+ Projeto</a>
    <a class="quick-link" href="/memory">+ Memória</a>
    <a class="primary-action" href="#new-mission">Nova missão</a></nav>
</section>
<section class="metric-grid" aria-label="Resumo operacional">{cards}</section>
<section class="dashboard-grid">
  <article class="panel mission-composer" id="new-mission">
    <div class="panel-heading"><div><span class="eyebrow">Executar agora</span>
      <h2>Nova missão</h2></div><span class="status-dot">Local</span></div>
    {feedback}
    {_mission_form(active)}
  </article>
  <aside class="panel activity-panel">
    <div class="panel-heading"><div><span class="eyebrow">Timeline</span>
      <h2>Últimas atividades</h2></div><a href="/executions">Ver execuções</a></div>
    {_render_timeline(timeline)}
  </aside>
</section>{_render_recent_projects(dashboard.recent_projects)}{result_content}"""


def _render_recent_projects(projects: tuple[Any, ...]) -> str:
    rows = "".join(_project_row(project) for project in projects)
    rows = rows or (
        '<tr class="table-empty"><td colspan="4">'
        "Nenhum projeto recente neste Workspace.</td></tr>"
    )
    return f"""<section class="panel recent-projects">
  <div class="panel-heading"><div><span class="eyebrow">Portfólio</span>
    <h2>Últimos projetos</h2></div><a href="/projects">Ver projetos</a></div>
  <div class="table-scroll"><table class="projects-table compact-table">
    <thead><tr><th>Projeto</th><th>Cliente</th><th>Status</th><th>Criado</th></tr></thead>
    <tbody>{rows}</tbody></table></div>
</section>"""


def _render_projects(
    projects: tuple[Any, ...],
    result: Result | None,
    dashboard: CompanionDashboard | None,
) -> str:
    active = dashboard.active_workspace if dashboard else None
    workspace_id = active.id if active else ""
    rows = "".join(_project_row(project) for project in reversed(projects))
    rows = rows or (
        '<tr class="table-empty"><td colspan="4">'
        "Nenhum projeto neste Workspace.</td></tr>"
    )
    table = f"""<div class="table-scroll"><table class="projects-table">
      <thead><tr><th>Projeto</th><th>Cliente</th><th>Status</th>
      <th>Criado</th></tr></thead><tbody>{rows}</tbody></table></div>"""
    return f"""<section class="split-grid projects-layout">
  <article class="panel"><span class="eyebrow">Nova obra</span>
    <h2>Criar projeto</h2>{_render_feedback(result)}
    <form method="post" action="/projects" class="stack-form">
      <input type="hidden" name="workspace_id" value="{escape(workspace_id)}">
      <div class="field"><label for="project-title">Título</label>
        <input id="project-title" name="title" required maxlength="160"></div>
      <div class="field"><label for="project-client">Cliente</label>
        <input id="project-client" name="client" required maxlength="160"></div>
      <div class="field form-span"><label for="project-address">Morada</label>
        <input id="project-address" name="address" required maxlength="240"></div>
      <div class="field form-span"><label for="project-description">Descrição</label>
        <textarea id="project-description" name="description" maxlength="2000"></textarea></div>
      <button type="submit">Criar projeto <span>→</span></button>
    </form>
  </article>
  <article class="panel projects-panel"><span class="eyebrow">Workspace</span>
    <h2>{escape(active.name if active else 'Nenhum')}</h2>{table}
  </article>
</section>"""


def _project_row(project: Any) -> str:
    status = escape(project.status.value.upper())
    return f"""<tr>
      <td><strong>{escape(project.title)}</strong>
        <small>{escape(project.address)}</small></td>
      <td>{escape(project.client)}</td>
      <td><span class="pill status-{escape(project.status.value)}">{status}</span></td>
      <td><time>{project.created_at.astimezone().strftime('%d/%m/%Y')}</time></td>
    </tr>"""


def _project_card(project: Any) -> str:
    return f"""<article class="data-card project-card">
  <div><span class="pill">{escape(project.status.value.upper())}</span>
    <h3>{escape(project.title)}</h3>
    <p>{escape(project.client)} · {escape(project.address)}</p>
    <small>{len(project.mission_ids)} missão(ões)</small></div>
  <time>{project.created_at.astimezone().strftime('%d/%m · %H:%M')}</time>
</article>"""


def _mission_form(active: Any | None) -> str:
    workspace_field = (
        f'<input type="hidden" name="workspace_id" value="{escape(active.id)}">'
        if active is not None
        else ""
    )
    return f"""<form method="post" action="/missions" class="stack-form mission-form">
  {workspace_field}
  <div class="field"><label for="title">Título</label>
    <input id="title" name="title" required maxlength="160"
      placeholder="O que você quer realizar?"></div>
  <div class="field"><label for="objective">Objetivo</label>
    <textarea id="objective" name="objective" required maxlength="2000"
      placeholder="Descreva o resultado esperado"></textarea></div>
  <button type="submit">Criar e executar missão <span>→</span></button>
</form>"""


def _render_missions(
    missions: tuple[Any, ...],
    executions: tuple[CompanionExecution, ...],
    result: Result | None,
    dashboard: CompanionDashboard | None,
) -> str:
    active = dashboard.active_workspace if dashboard else None
    execution_by_mission = {
        item.mission.id: item for item in executions
    }
    cards = "".join(
        _mission_card(mission, execution_by_mission.get(mission.id))
        for mission in missions
    ) or _empty_state("Nenhuma missão neste Workspace.")
    return f"""<section class="split-grid missions-layout">
  <article class="panel"><span class="eyebrow">Novo objetivo</span>
    <h2>Criar missão</h2>{_render_feedback(result)}{_mission_form(active)}</article>
  <article class="panel"><span class="eyebrow">Histórico local</span>
    <h2>Missões</h2><div class="card-list">{cards}</div></article>
</section>{_render_mission_result(result)}"""


def _mission_card(
    mission: Any,
    execution: CompanionExecution | None,
) -> str:
    status = execution.report.status.value if execution else mission.status.value
    return f"""<article class="data-card">
  <div><span class="pill">{escape(status.upper())}</span>
    <h3>{escape(mission.title)}</h3><p>{escape(mission.objective)}</p></div>
  <time>{mission.created_at.astimezone().strftime('%d/%m · %H:%M')}</time>
</article>"""


def _render_memory(
    memories: tuple[Any, ...],
    result: Result | None,
    dashboard: CompanionDashboard | None,
    *,
    query: str,
    category: str,
) -> str:
    active = dashboard.active_workspace if dashboard else None
    workspace_id = active.id if active else ""
    cards = "".join(_memory_card(memory) for memory in memories)
    cards = cards or _empty_state("Nenhuma memória encontrada.")
    return f"""<section class="panel search-panel">
  <form method="get" action="/memory" class="search-form">
    <input name="q" value="{escape(query)}" placeholder="Pesquisar memórias">
    <input name="category" value="{escape(category)}" placeholder="Categoria">
    <button type="submit">Pesquisar</button>
  </form>
</section>
<section class="split-grid memory-layout">
  <article class="panel"><span class="eyebrow">Registro local</span>
    <h2>Nova memória</h2>{_render_feedback(result)}
    <form method="post" action="/memory" class="stack-form">
      <input type="hidden" name="workspace_id" value="{escape(workspace_id)}">
      <div class="field"><label for="memory-category">Categoria</label>
        <input id="memory-category" name="category" required placeholder="decisão"></div>
      <div class="field"><label for="memory-title">Título</label>
        <input id="memory-title" name="title" required></div>
      <div class="field form-span"><label for="memory-content">Conteúdo</label>
        <textarea id="memory-content" name="content" required></textarea></div>
      <button type="submit">Registrar memória <span>→</span></button>
    </form>
  </article>
  <article class="panel"><span class="eyebrow">Workspace</span>
    <h2>{escape(active.name if active else 'Nenhum')}</h2>
    <div class="card-list">{cards}</div>
  </article>
</section>"""


def _memory_card(memory: Any) -> str:
    return f"""<article class="data-card memory-card">
  <div><span class="pill">{escape(memory.category)}</span>
    <h3>{escape(memory.title)}</h3><p>{escape(memory.content)}</p>
    <small>Workspace: {escape(memory.workspace_id)}</small></div>
  <time>{memory.created_at.astimezone().strftime('%d/%m · %H:%M')}</time>
</article>"""


def _render_executions(executions: tuple[CompanionExecution, ...]) -> str:
    cards = "".join(
        f"""<article class="data-card execution-card"><div>
          <span class="pill">{escape(item.report.status.value.upper())}</span>
          <h3>{escape(item.mission.title)}</h3>
          <p>{len(item.report.step_results)} etapas · Provider: {escape(item.provider_id)}</p>
          </div><time>{item.report.completed_at.astimezone().strftime('%d/%m · %H:%M')}</time>
        </article>"""
        for item in executions
    ) or _empty_state("Nenhuma execução registrada.")
    return f'<section class="panel"><div class="card-list">{cards}</div></section>'


def _render_doctor(dashboard: CompanionDashboard | None) -> str:
    status = dashboard.application_health if dashboard else "DEGRADADO"
    available = dashboard.available_service_count if dashboard else 0
    service_count = dashboard.service_count if dashboard else 3
    css_class = "success" if status == "DISPONÍVEL" else "degraded"
    storage = dashboard.storage_label if dashboard else "Indisponível"
    sqlite_connected = "SIM" if storage == "SQLite local" else "NÃO"
    persistent_mode = "ATIVO" if storage == "SQLite local" else "INATIVO"
    return f"""<section class="panel health-panel">
  <div class="doctor-card">
  <div class="health-ring"><strong>{available}/{service_count}</strong>
    <span>Serviços disponíveis</span></div>
  <div><span class="eyebrow">Application Health</span><h2>Saúde dos Serviços</h2>
  <p>Disponibilidade local de Workspace, Mission e Memory Services.</p>
  <span class="pill {css_class}">{status}</span>
  </div></div>
  <div class="health-facts">
    <div>{_icon('storage')}<span>SQLite conectado</span><strong>{sqlite_connected}</strong></div>
    <div>{_icon('health')}<span>Modo persistente</span><strong>{persistent_mode}</strong></div>
    <div>{_icon('workspaces')}<span>Armazenamento</span><strong>{escape(storage)}</strong></div>
  </div>
  <p class="doctor-disclaimer">Indicador operacional. Não substitui o Genesis Doctor.</p>
</section>"""


def _render_settings() -> str:
    return """<section class="panel"><span class="eyebrow">Instância local</span>
  <h2>Configurações</h2><p class="muted">Configuração persistente, providers
  reais e autenticação permanecem fora do escopo desta versão.</p></section>"""


def _render_intelligence(
    profiles: tuple[Any, ...],
    handoffs: tuple[Any, ...],
    result: Result | None,
    dashboard: CompanionDashboard | None,
    projects: tuple[Any, ...],
) -> str:
    active = dashboard.active_workspace if dashboard else None
    decision = (
        result.data
        if result is not None
        and result.is_success
        and hasattr(result.data, "selected_provider_id")
        else None
    )
    profile_rows = "".join(_provider_profile_row(item) for item in profiles)
    profile_rows = profile_rows or (
        '<tr class="table-empty"><td colspan="5">'
        "Nenhum provider configurado.</td></tr>"
    )
    handoff_cards = "".join(
        _manual_handoff_card(item) for item in reversed(handoffs)
    ) or _empty_state("Nenhum handoff manual criado.")
    recommendation = _routing_recommendation(decision, active, projects)
    return f"""<section class="intelligence-hero panel">
  <div><span class="eyebrow">Free First</span><h2>Intelligence Router</h2>
    <p>Recomendações configuradas, sem acessar serviços externos.</p></div>
  <span class="status-dot">Padrão · Somente gratuito</span>
</section>
<section class="split-grid intelligence-layout">
  <article class="panel"><span class="eyebrow">Novo pedido</span>
    <h2>Encontrar provider</h2>{_render_feedback(result)}
    <form method="post" action="/intelligence/route"
      class="stack-form intelligence-form">
      <div class="field form-span"><label for="intelligence-prompt">Pedido</label>
        <textarea id="intelligence-prompt" name="prompt" required
          placeholder="Descreva o resultado que precisa"></textarea></div>
      <div class="field"><label for="intelligence-capability">Capability</label>
        <select id="intelligence-capability" name="capability">
          <option value="general_assistance">Assistência geral</option>
          <option value="text_generation">Geração de texto</option>
          <option value="code_generation">Programação</option>
        </select></div>
      <div class="field"><label for="routing-mode">Modo</label>
        <select id="routing-mode" name="routing_mode">
          <option value="free_only">Somente gratuito</option>
          <option value="local_first">Local primeiro</option>
          <option value="economy">Economia</option>
          <option value="balanced">Balanceado</option>
          <option value="max_quality">Máxima qualidade</option>
        </select></div>
      <button type="submit">Recomendar provider <span>→</span></button>
    </form>
  </article>{recommendation}
</section>
<section class="panel intelligence-providers">
  <div class="panel-heading"><div><span class="eyebrow">Configuração local</span>
    <h2>Providers cadastrados</h2></div>
    <small>Disponibilidade configurada, não verificada externamente</small></div>
  <div class="table-scroll"><table class="projects-table provider-table">
    <thead><tr><th>Provider</th><th>Acesso</th><th>Custo</th>
      <th>Capabilities</th><th>Estado</th></tr></thead>
    <tbody>{profile_rows}</tbody></table></div>
</section>
<section class="panel handoff-list">
  <div class="panel-heading"><div><span class="eyebrow">Fluxo manual</span>
    <h2>Manual Handoffs</h2></div>
    <small>Sem automação, scraping ou login</small></div>
  <div class="card-list">{handoff_cards}</div>
</section>"""


def _provider_profile_row(profile: Any) -> str:
    state = "HABILITADO" if profile.enabled else "DESABILITADO"
    css_class = "success" if profile.enabled else ""
    return f"""<tr><td><strong>{escape(profile.display_name)}</strong>
      <small>{escape(profile.provider_id)}</small></td>
      <td>{escape(profile.access_mode.value.upper())}</td>
      <td>{escape(profile.cost_tier.value.upper())}</td>
      <td>{escape(', '.join(profile.capabilities))}</td>
      <td><span class="pill {css_class}">{state}</span></td></tr>"""


def _routing_recommendation(
    decision: Any | None,
    active: Any | None,
    projects: tuple[Any, ...],
) -> str:
    if decision is None:
        return f"""<aside class="panel recommendation-empty">
          {_empty_state('Envie um pedido para receber uma recomendação explicável.')}
        </aside>"""
    alternatives = ", ".join(decision.alternatives) or "Nenhuma"
    handoff_form = ""
    if decision.requires_manual_handoff:
        project_options = '<option value="">Sem projeto</option>' + "".join(
            f'<option value="{escape(item.id)}">{escape(item.title)}</option>'
            for item in projects
        )
        workspace_field = (
            f'<input type="hidden" name="workspace_id" value="{escape(active.id)}">'
            if active else ""
        )
        handoff_form = f"""<form method="post"
          action="/intelligence/handoffs" class="stack-form handoff-create-form">
          {workspace_field}<input type="hidden" name="provider_id"
            value="{escape(decision.selected_provider_id)}">
          <div class="field form-span"><label for="handoff-prompt">Prompt para copiar</label>
            <textarea id="handoff-prompt" name="prompt"
              required>{escape(decision.prompt)}</textarea></div>
          <div class="field form-span"><label for="handoff-project">Associar ao Projeto</label>
            <select id="handoff-project" name="project_id">{project_options}</select></div>
          <button type="submit">Criar handoff manual</button></form>"""
    return f"""<aside class="panel recommendation-card">
      <span class="eyebrow">Provider recomendado</span>
      <h2>{escape(decision.selected_provider_id)}</h2>
      <p>{escape(decision.reason)}</p>
      <dl><div><dt>Acesso</dt><dd>{escape(decision.access_mode.value.upper())}</dd></div>
        <div><dt>Modo</dt><dd>{escape(decision.routing_mode.value.upper())}</dd></div>
        <div><dt>Alternativas</dt><dd>{escape(alternatives)}</dd></div></dl>
      {handoff_form}</aside>"""


def _manual_handoff_card(handoff: Any) -> str:
    completed = handoff.status.value == "completed"
    response = (
        f'<p class="handoff-response">{escape(handoff.response)}</p>'
        if completed and handoff.response else ""
    )
    form = "" if completed else f"""<form method="post"
      action="/intelligence/handoffs/{escape(handoff.id)}/complete"
      class="handoff-complete-form">
      <label for="response-{escape(handoff.id)}">Resposta manual</label>
      <textarea id="response-{escape(handoff.id)}" name="response" required
        placeholder="Cole aqui a resposta obtida manualmente"></textarea>
      <label class="checkbox"><input type="checkbox" name="save_as_memory">
        Salvar também como Memory</label>
      <button type="submit">Concluir handoff</button></form>"""
    css_class = "success" if completed else ""
    return f"""<article class="data-card handoff-card"><div>
      <span class="pill {css_class}">{escape(handoff.status.value.upper())}</span>
      <h3>{escape(handoff.provider_id)}</h3><p>{escape(handoff.prompt)}</p>
      {response}{form}</div></article>"""


def _render_timeline(activities: tuple[CompanionActivity, ...]) -> str:
    if not activities:
        return _empty_state("Crie uma missão ou memória para iniciar a timeline.")
    return '<div class="timeline">' + "".join(
        f"""<article class="timeline-item {escape(item.kind)}">
          <span class="timeline-marker"></span><div><strong>{escape(item.title)}</strong>
          <p>{escape(item.description)}</p></div>
          <time>{item.occurred_at.astimezone().strftime('%H:%M')}</time></article>"""
        for item in activities[:8]
    ) + "</div>"


def _render_mission_result(result: Result | None) -> str:
    if result is None:
        return ""
    if not result.is_success or not isinstance(result.data, CompanionExecution):
        return (
            '<section class="panel error"><h2>Não foi possível executar</h2><p>'
            f"{escape(result.message)}</p></section>"
        )
    execution = result.data
    step_results = {item.step_id: item for item in execution.report.step_results}
    steps = "".join(
        _render_step(step, step_results[step.id]) for step in execution.plan.steps
    )
    return f"""<section class="panel result-panel" id="mission">
  <span class="eyebrow">Missão criada</span><h2>{escape(execution.mission.title)}</h2>
  <p>{escape(execution.mission.objective)}</p>
  <p class="meta">Workspace:
    {escape(execution.workspace.name if execution.workspace else '—')}</p>
  <h3>Plano demonstrativo</h3>
  <p>Provider: <strong>{escape(execution.provider_id)}</strong></p>
  <ol class="step-list">{steps}</ol>
  <h3>Relatório final</h3>
  <p>Status: <span class="pill success">{escape(execution.report.status.value.upper())}</span></p>
</section>"""


def _render_step(step, result) -> str:
    output = result.content or result.error or "Sem conteúdo"
    provider = result.provider_id or "—"
    return f"""<li><div><strong>{escape(step.title)}</strong>
  <p>{escape(step.description)}</p><small>Provider: {escape(provider)}</small></div>
  <span class="pill">{escape(result.status.value.upper())}</span>
  <pre>{escape(output)}</pre></li>"""


def _render_feedback(result: Result | None) -> str:
    if result is None:
        return ""
    css_class = "notice" if result.is_success else "notice error"
    return f'<p class="{css_class}">{escape(result.message)}</p>'


def _empty_state(message: str) -> str:
    return f'<div class="empty-state"><span>◇</span><p>{escape(message)}</p></div>'
