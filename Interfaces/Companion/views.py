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
    "dashboard": "Command Center",
    "workspaces": "Workspaces",
    "projects": "Projects",
    "missions": "Missões",
    "memory": "Memory",
    "executions": "Execuções",
    "doctor": "Application Health",
    "settings": "Settings",
    "intelligence": "Intelligence",
    "remodeling": "Remodeling",
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
    remodeling_briefs: tuple[Any, ...] = (),
    remodeling_proposals: tuple[Any, ...] = (),
    remodeling_proposal: Any | None = None,
) -> str:
    title = _PAGE_TITLES.get(page, "Command Center")
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
        remodeling_briefs=remodeling_briefs,
        remodeling_proposals=remodeling_proposals,
        remodeling_proposal=remodeling_proposal,
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
        context_label=_context_label(page, dashboard),
        page_title=escape(title),
        page_subtitle=_page_subtitle(page),
        page_action=_page_action(page, dashboard),
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
    if page == "remodeling":
        return _render_remodeling(
            context["workspaces"],
            context["projects"],
            context["remodeling_briefs"],
            context["remodeling_proposals"],
            context["manual_handoffs"],
            context["remodeling_proposal"],
            context["result"],
            context["dashboard"],
        )
    return _render_dashboard(
        context["dashboard"],
        context["timeline"],
        context["result"],
    )


def _render_sidebar(active_page: str) -> str:
    items = (
        ("dashboard", "/", "dashboard", "Command Center"),
        ("projects", "/projects", "projects", "Projects"),
        ("intelligence", "/intelligence", "intelligence", "Intelligence"),
        ("memory", "/memory", "memory", "Memory"),
        ("remodeling", "/remodeling", "remodeling", "Remodeling"),
        ("settings", "/settings", "settings", "Settings"),
        ("doctor", "/doctor", "health", "Application Health"),
    )
    return "".join(
        f'<a class="nav-item{" active" if key == active_page else ""}" '
        f'href="{href}"{_aria_current(key, active_page)}>'
        f'{_icon(icon)}<span>{label}</span></a>'
        for key, href, icon, label in items
    )


def _aria_current(item: str, active_page: str) -> str:
    return ' aria-current="page"' if item == active_page else ""


def _context_label(
    page: str,
    dashboard: CompanionDashboard | None,
) -> str:
    title = escape(_PAGE_TITLES.get(page, "Command Center"))
    return f"Genesis / {title}"


def _page_action(
    page: str,
    dashboard: CompanionDashboard | None = None,
) -> str:
    if (
        page == "dashboard"
        and dashboard is not None
        and dashboard.command_center is not None
    ):
        command_center = dashboard.command_center
        return (
            f'<a class="button-link primary-button" '
            f'href="{escape(command_center.primary_action_href)}">'
            f'{escape(command_center.primary_action_label)}</a>'
        )
    actions = {
        "dashboard": ("/projects#new-project", "Começar agora"),
        "workspaces": ("#workspaces", "Novo Workspace"),
        "projects": ("#new-project", "Criar Project"),
        "missions": ("#new-mission", "Criar Mission"),
        "memory": ("#new-memory", "Guardar Memory"),
        "executions": ("/missions", "Nova Mission"),
        "intelligence": ("#new-intelligence", "Novo pedido"),
        "remodeling": ("#new-brief", "Novo Brief"),
        "settings": ("/", "Voltar ao trabalho"),
        "doctor": ("/doctor", "Atualizar estado"),
    }
    href, label = actions.get(page, ("/", "Ir ao Command Center"))
    return f'<a class="button-link primary-button" href="{href}">{label}</a>'


def _icon(name: str) -> str:
    paths = {
        "dashboard": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
        "workspaces": '<path d="M4 5h6l2 2h8v12H4z"/>',
        "projects": '<path d="M4 7h16v13H4zM8 7V4h8v3M8 12h8"/>',
        "missions": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="m15 9 5-5"/>',
        "memory": '<path d="M8 4h8a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3zM9 9h6M9 13h6"/>',
        "executions": '<path d="m9 7 8 5-8 5z"/><circle cx="12" cy="12" r="10"/>',
        "intelligence": '<path d="M12 3a6 6 0 0 0-3 11.2V18h6v-3.8A6 6 0 0 0 12 3zM9 21h6M12 3V1M4.2 5.2 2.8 3.8M19.8 5.2l1.4-1.4"/>',
        "remodeling": '<path d="M3 21h18M5 21V9l7-6 7 6v12M9 21v-6h6v6M8 11h2M14 11h2"/>',
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
        "dashboard": "O que precisa da sua atenção agora",
        "workspaces": "Organize missões e memórias por contexto",
        "projects": "Organize obras, clientes e missões reais",
        "missions": "Crie, planeje e execute objetivos",
        "memory": "Consulte o conhecimento operacional do Workspace",
        "executions": "Acompanhe resultados e providers",
        "doctor": "Disponibilidade local dos Application Services",
        "settings": "Preferências da instância local",
        "intelligence": "Roteamento explicável com recursos gratuitos primeiro",
        "remodeling": "Propostas preliminares com revisão humana obrigatória",
    }
    return escape(subtitles.get(page, "Genesis Companion"))


def _render_dashboard(
    dashboard: CompanionDashboard | None,
    timeline: tuple[CompanionActivity, ...],
    result: Result | None,
) -> str:
    if dashboard is None:
        return '<section class="panel error">Command Center indisponível.</section>'
    command_center = dashboard.command_center
    if command_center is None:
        return '<section class="panel error">Orientação indisponível.</section>'
    feedback = _render_feedback(result)
    result_content = _render_mission_result(result) if result else ""
    health = ""
    if dashboard.application_health == "DEGRADADO":
        health = f"""<aside class="command-health state-degraded" role="status">
  <div><strong>Application Health degradado</strong>
    <p>{dashboard.available_service_count}/{dashboard.service_count} serviços disponíveis. Indicador operacional; não substitui o Doctor oficial.</p></div>
  <a href="/doctor">Ver estado</a>
</aside>"""
    return f"""<section class="command-welcome" aria-labelledby="command-greeting">
  <div><span class="eyebrow">Command Center</span>
    <h2 id="command-greeting">{escape(command_center.greeting)}</h2>
    <p>Veja o que merece sua atenção agora.</p></div>
  <nav class="secondary-actions" aria-label="Atalhos secundários">
    <a href="/workspaces">Workspace</a><a href="/projects">Projeto</a>
    <a href="/memory">Memória</a></nav>
</section>
{feedback}{health}
<section class="attention-section" aria-labelledby="attention-title">
  <div class="section-heading"><div><span class="eyebrow">Prioridade</span>
    <h2 id="attention-title">Atenção agora</h2></div>
    <small>Até 3 itens, ordenados por impacto</small></div>
  <div class="priority-list">{_render_priorities(command_center.priorities)}</div>
</section>
{_render_onboarding(command_center)}
<section class="action-overview" aria-label="Continuidade do trabalho">
  {_action_card("Projects", dashboard.active_project_count + dashboard.completed_project_count, "Nenhum projeto ativo." if dashboard.active_project_count == 0 else f"{dashboard.active_project_count} projeto(s) em andamento.", "Criar primeiro projeto" if dashboard.active_project_count == 0 else "Continuar projetos", "/projects", "projects")}
  {_action_card("Missões", dashboard.mission_count, "Nenhuma missão registrada." if dashboard.mission_count == 0 else f"{dashboard.mission_count} missão(ões) preservam o progresso.", "Criar primeira missão" if dashboard.mission_count == 0 else "Ver missões", "/missions", "missions")}
  {_action_card("Memory", dashboard.memory_count, "Nenhuma memória registrada." if dashboard.memory_count == 0 else f"{dashboard.memory_count} memória(s) mantêm o contexto.", "Registrar primeira memória" if dashboard.memory_count == 0 else "Explorar Memory", "/memory", "memory")}
</section>
<section class="dashboard-grid command-continuity">
  <article class="panel intelligence-focus">
    <div class="panel-heading"><div><span class="eyebrow">Capacidade central</span>
      <h2>Genesis Intelligence</h2></div><span class="pill">Free First</span></div>
    <strong>{escape(command_center.intelligence_state)}</strong>
    <p>{escape(command_center.intelligence_description)}</p>
    <a class="text-action" href="/intelligence">Abrir Intelligence <span aria-hidden="true">→</span></a>
  </article>
  <aside class="panel activity-panel">
    <div class="panel-heading"><div><span class="eyebrow">Continuidade</span>
      <h2>Timeline</h2></div><a href="/executions">Ver atividades</a></div>
    {_render_command_timeline(timeline, command_center.primary_action_href)}
  </aside>
</section>{result_content}"""


def _render_priorities(priorities) -> str:
    return "".join(
        f'<article class="priority-item priority-{escape(item.level)}">'
        f'<div class="priority-signal" aria-hidden="true"></div><div>'
        f'<span class="priority-level">{escape(item.level)}</span>'
        f'<h3>{escape(item.title)}</h3><p>{escape(item.reason)}</p></div>'
        f'<a class="text-action" href="{escape(item.href)}">'
        f'{escape(item.action_label)} <span aria-hidden="true">→</span></a></article>'
        for item in priorities
    )


def _render_onboarding(command_center) -> str:
    if not command_center.show_onboarding:
        return ""
    completed = sum(step.complete for step in command_center.onboarding_steps)
    steps = "".join(
        f'<li class="onboarding-step{" complete" if step.complete else ""}">'
        f'<span aria-hidden="true">{"✓" if step.complete else index}</span><div>'
        f'<strong>{escape(step.title)}</strong><p>{escape(step.description)}</p></div>'
        f'<a href="{escape(step.href)}">Abrir</a></li>'
        for index, step in enumerate(command_center.onboarding_steps, 1)
    )
    return f"""<section class="panel onboarding" aria-labelledby="onboarding-title">
  <div class="panel-heading"><div><span class="eyebrow">Primeiros passos</span>
    <h2 id="onboarding-title">Construa seu primeiro fluxo</h2></div>
    <span class="onboarding-progress">{completed}/3</span></div>
  <progress max="3" value="{completed}">{completed} de 3</progress>
  <ol>{steps}</ol>
</section>"""


def _action_card(
    label: str,
    count: int,
    state: str,
    action: str,
    href: str,
    icon: str,
) -> str:
    return f"""<article class="action-card">
  <div class="action-card-icon">{_icon(icon)}</div><div class="action-card-copy">
    <div><h3>{escape(label)}</h3><span>{count}</span></div>
    <p>{escape(state)}</p><a href="{href}">{escape(action)} <span aria-hidden="true">→</span></a>
  </div></article>"""


def _render_command_timeline(
    activities: tuple[CompanionActivity, ...],
    start_href: str,
) -> str:
    if activities:
        return _render_timeline(activities[:6])
    return f"""<div class="timeline-empty empty-state">
  <div class="metric-icon">{_icon("executions")}</div>
  <strong>Seu contexto começa aqui.</strong>
  <p>O Genesis registra decisões, missões, memórias e projetos para que você nunca perca contexto.</p>
  <a class="text-action" href="{escape(start_href)}">Começar agora <span aria-hidden="true">→</span></a>
</div>"""


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
  <article class="panel" id="new-project"><span class="eyebrow">Nova obra</span>
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
  <article class="panel" id="new-mission"><span class="eyebrow">Novo objetivo</span>
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
  <article class="panel" id="new-memory"><span class="eyebrow">Registro local</span>
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
  <article class="panel" id="new-intelligence"><span class="eyebrow">Novo pedido</span>
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


def _render_remodeling(
    workspaces: tuple[Any, ...],
    projects: tuple[Any, ...],
    briefs: tuple[Any, ...],
    proposals: tuple[Any, ...],
    handoffs: tuple[Any, ...],
    selected: Any | None,
    result: Result | None,
    dashboard: CompanionDashboard | None,
) -> str:
    active = dashboard.active_workspace if dashboard else None
    workspace_options = "".join(
        f'<option value="{escape(item.id)}"'
        f'{" selected" if active and item.id == active.id else ""}>'
        f'{escape(item.name)}</option>' for item in workspaces
    )
    project_options = "".join(
        f'<option value="{escape(item.id)}">{escape(item.title)}</option>'
        for item in projects
    )
    brief_cards = "".join(_remodeling_brief_card(item) for item in briefs)
    proposal_cards = "".join(
        _remodeling_proposal_link(item) for item in reversed(proposals)
    )
    pending = tuple(
        item for item in handoffs
        if item.project_id and item.status.value == "pending"
    )
    handoff_cards = "".join(_remodeling_handoff_card(item) for item in pending)
    detail = _remodeling_proposal_detail(selected) if selected else ""
    return f"""<section class="panel remodeling-hero">
  <div><span class="eyebrow">Copilot especializado</span>
    <h2>Remodelação com aprovação humana</h2>
    <p>Brief → Free First → proposta → revisão → aprovação → aplicação.</p></div>
  <span class="status-dot">Dados voláteis · orçamento preliminar</span>
</section>
{_render_feedback(result)}
<section class="split-grid remodeling-layout">
  <article class="panel" id="new-brief"><span class="eyebrow">Etapa 1</span><h2>Novo brief</h2>
    <form method="post" action="/remodeling/briefs" class="stack-form">
      <div class="field"><label for="remodel-workspace">Workspace</label>
        <select id="remodel-workspace" name="workspace_id" required>{workspace_options}</select></div>
      <div class="field"><label for="remodel-project">Projeto</label>
        <select id="remodel-project" name="project_id" required>{project_options}</select></div>
      <div class="field form-span"><label for="project-type">Tipo de obra</label>
        <input id="project-type" name="project_type" value="Casa de banho" required></div>
      <div class="field"><label for="room-length">Comprimento (m)</label>
        <input id="room-length" name="room_length" type="number" min="0.01" step="0.01"></div>
      <div class="field"><label for="room-width">Largura (m)</label>
        <input id="room-width" name="room_width" type="number" min="0.01" step="0.01"></div>
      <div class="field"><label for="room-height">Altura (m)</label>
        <input id="room-height" name="room_height" type="number" min="0.01" step="0.01"></div>
      <div class="field"><label for="budget-limit">Limite orçamental EUR</label>
        <input id="budget-limit" name="budget_limit" type="number" min="0" step="0.01"></div>
      <div class="field form-span"><label for="current-condition">Estado atual</label>
        <textarea id="current-condition" name="current_condition" required></textarea></div>
      <div class="field form-span"><label for="desired-result">Resultado desejado</label>
        <textarea id="desired-result" name="desired_result" required></textarea></div>
      <div class="field"><label for="deadline">Prazo</label>
        <input id="deadline" name="deadline" type="date"></div>
      <div class="field"><label for="known-materials">Materiais, separados por vírgula</label>
        <input id="known-materials" name="known_materials"></div>
      <div class="field"><label for="constraints">Restrições</label>
        <input id="constraints" name="constraints"></div>
      <div class="field"><label for="client-preferences">Preferências</label>
        <input id="client-preferences" name="client_preferences"></div>
      <div class="field form-span"><label for="remodel-notes">Notas</label>
        <textarea id="remodel-notes" name="notes"></textarea></div>
      <button type="submit">Criar brief para revisão</button>
    </form>
  </article>
  <aside class="panel"><span class="eyebrow">Etapa 2</span><h2>Briefs</h2>
    <div class="card-list">{brief_cards or _empty_state('Nenhum brief criado.')}</div>
  </aside>
</section>
<section class="split-grid remodeling-flow">
  <article class="panel"><span class="eyebrow">Handoff manual</span>
    <h2>Respostas JSON pendentes</h2>
    <div class="card-list">{handoff_cards or _empty_state('Nenhum handoff pendente.')}</div>
  </article>
  <article class="panel"><span class="eyebrow">Revisão</span><h2>Propostas</h2>
    <div class="card-list">{proposal_cards or _empty_state('Nenhuma proposta gerada.')}</div>
  </article>
</section>{detail}"""


def _remodeling_brief_card(brief: Any) -> str:
    missing = []
    if brief.budget_limit is None:
        missing.append("orçamento")
    if brief.deadline is None:
        missing.append("prazo")
    gap = ", ".join(missing) or "dados essenciais preenchidos"
    return f"""<article class="data-card"><div><span class="pill">DRAFT</span>
      <h3>{escape(brief.project_type)}</h3><p>Lacunas visíveis: {escape(gap)}</p>
      <form method="post" action="/remodeling/proposals">
        <input type="hidden" name="brief_id" value="{escape(brief.id)}">
        <button type="submit">Gerar handoff Free First</button></form></div></article>"""


def _remodeling_handoff_card(handoff: Any) -> str:
    return f"""<article class="data-card handoff-card"><div>
      <span class="pill">FREE ONLY · MANUAL</span><h3>{escape(handoff.provider_id)}</h3>
      <label for="prompt-{escape(handoff.id)}">Prompt para copiar manualmente</label>
      <textarea id="prompt-{escape(handoff.id)}" readonly>{escape(handoff.prompt)}</textarea>
      <form method="post" action="/remodeling/handoffs/{escape(handoff.id)}/complete">
        <label for="remodel-response-{escape(handoff.id)}">Resposta JSON</label>
        <textarea id="remodel-response-{escape(handoff.id)}" name="response" required></textarea>
        <button type="submit">Validar e criar proposta</button></form></div></article>"""


def _remodeling_proposal_link(proposal: Any) -> str:
    return f"""<a class="data-card proposal-link"
      href="/remodeling/proposals/{escape(proposal.id)}"><div>
      <span class="pill status-{escape(proposal.status.value)}">{escape(proposal.status.value.upper())}</span>
      <h3>{len(proposal.phases)} fases</h3>
      <p>Total preliminar: {proposal.preliminary_budget.total} EUR</p></div></a>"""


def _remodeling_proposal_detail(proposal: Any) -> str:
    phases = "".join(
        f"<li><strong>{phase.order}. {escape(phase.title)}</strong>"
        f"<p>{escape(phase.description)}</p></li>" for phase in proposal.phases
    )
    risks = "".join(f"<li>{escape(item)}</li>" for item in proposal.risks)
    lines = "".join(
        f"<tr><td>{escape(item.category)}</td><td>{escape(item.description)}</td>"
        f"<td>{item.quantity or '—'} {escape(item.unit or '')}</td>"
        f"<td>{item.total if item.total is not None else '—'}</td>"
        f"<td>ESTIMATIVA</td></tr>" for item in proposal.preliminary_budget.line_items
    )
    actions = {
        "generated": (("review", "Marcar como revisada"), ("reject", "Rejeitar")),
        "reviewed": (("approve", "Aprovar explicitamente"), ("reject", "Rejeitar")),
        "approved": (("apply", "Aplicar proposta"), ("reject", "Rejeitar")),
    }.get(proposal.status.value, ())
    forms = "".join(
        f'<form method="post" action="/remodeling/proposals/{escape(proposal.id)}/{action}">'
        f'<button type="submit">{escape(label)}</button></form>'
        for action, label in actions
    )
    budget = proposal.preliminary_budget
    return f"""<section class="panel proposal-detail">
      <div class="panel-heading"><div><span class="eyebrow">Proposta preliminar</span>
        <h2>Revisão humana obrigatória</h2></div>
        <span class="pill">{escape(proposal.status.value.upper())}</span></div>
      <p class="notice">Estimativa preliminar. Não constitui preço final nem proposta comercial.</p>
      <h3>Fases</h3><ol class="phase-list">{phases}</ol>
      <h3>Riscos</h3><ul>{risks}</ul>
      <h3>Orçamento preliminar</h3>
      <div class="table-scroll"><table class="projects-table"><thead><tr>
        <th>Categoria</th><th>Descrição</th><th>Quantidade</th><th>Total EUR</th><th>Natureza</th>
        </tr></thead><tbody>{lines}</tbody></table></div>
      <p>Subtotal: <strong>{budget.subtotal} EUR</strong> · Contingência:
        <strong>{budget.contingency} EUR</strong> · Total preliminar:
        <strong>{budget.total} EUR</strong></p>
      <div class="proposal-actions">{forms}</div>
    </section>"""


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
