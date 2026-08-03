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
    "missions": "Missões",
    "memory": "Memórias",
    "executions": "Execuções",
    "doctor": "Application Health",
    "settings": "Configurações",
}


def render_page(
    config: Configuration,
    result: Result | None = None,
    *,
    dashboard: CompanionDashboard | None = None,
    page: str = "dashboard",
    workspaces: tuple[Any, ...] = (),
    workspace: Any | None = None,
    missions: tuple[Any, ...] = (),
    memories: tuple[Any, ...] = (),
    executions: tuple[CompanionExecution, ...] = (),
    timeline: tuple[CompanionActivity, ...] = (),
    query: str = "",
    category: str = "",
) -> str:
    title = _PAGE_TITLES.get(page, "Dashboard")
    content = _page_content(
        page=page,
        result=result,
        dashboard=dashboard,
        workspaces=workspaces,
        workspace=workspace,
        missions=missions,
        memories=memories,
        executions=executions,
        timeline=timeline,
        query=query,
        category=category,
    )
    template = Template(
        (_ROOT / "templates" / "layout.html").read_text(encoding="utf-8")
    )
    return template.safe_substitute(
        title=escape(title),
        system_name=escape(config.system_name),
        version=escape(config.version),
        environment=escape(config.environment),
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
    return _render_dashboard(
        context["dashboard"],
        context["timeline"],
        context["result"],
    )


def _render_sidebar(active_page: str) -> str:
    items = (
        ("dashboard", "/", "◈", "Dashboard"),
        ("workspaces", "/workspaces", "▦", "Workspaces"),
        ("missions", "/missions", "◎", "Missões"),
        ("memory", "/memory", "◇", "Memórias"),
        ("executions", "/executions", "▶", "Execuções"),
        ("doctor", "/doctor", "✚", "Saúde dos Serviços"),
        ("settings", "/settings", "⚙", "Configurações"),
    )
    return "".join(
        f'<a class="nav-item{" active" if key == active_page else ""}" '
        f'href="{href}"><span>{icon}</span>{label}</a>'
        for key, href, icon, label in items
    )


def _page_subtitle(page: str) -> str:
    subtitles = {
        "dashboard": "Visão operacional do seu Genesis local",
        "workspaces": "Organize missões e memórias por contexto",
        "missions": "Crie, planeje e execute objetivos",
        "memory": "Consulte o conhecimento operacional do Workspace",
        "executions": "Acompanhe resultados e providers",
        "doctor": "Disponibilidade local dos Application Services",
        "settings": "Preferências da instância local",
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
    last_activity = (
        dashboard.last_activity.astimezone().strftime("%d/%m/%Y · %H:%M")
        if dashboard.last_activity is not None
        else "Nenhuma atividade"
    )
    metrics = (
        ("Workspace ativo", active_name, "workspace"),
        ("Missões", str(dashboard.mission_count), "missions"),
        ("Memórias", str(dashboard.memory_count), "memory"),
        ("Execuções", str(dashboard.execution_count), "executions"),
        ("Saúde dos Serviços", dashboard.application_health, "health"),
        ("Última atividade", last_activity, "activity"),
    )
    cards = "".join(
        f'<article class="metric-card {css}"><span>{escape(label)}</span>'
        f'<strong>{escape(value)}</strong></article>'
        for label, value, css in metrics
    )
    feedback = _render_feedback(result)
    result_content = _render_mission_result(result) if result else ""
    return f"""<section class="metric-grid">{cards}</section>
<section class="split-grid">
  <article class="panel">
    <div class="panel-heading"><div><span class="eyebrow">Ação rápida</span>
      <h2>Nova missão</h2></div><span class="status-dot">Local</span></div>
    {feedback}
    {_mission_form(active)}
  </article>
  <article class="panel">
    <div class="panel-heading"><div><span class="eyebrow">Atividade</span>
      <h2>Timeline</h2></div><a href="/executions">Ver execuções</a></div>
    {_render_timeline(timeline)}
  </article>
</section>{result_content}"""


def _mission_form(active: Any | None) -> str:
    workspace_field = (
        f'<input type="hidden" name="workspace_id" value="{escape(active.id)}">'
        if active is not None
        else ""
    )
    return f"""<form method="post" action="/missions" class="stack-form">
  {workspace_field}
  <label for="title">Título</label>
  <input id="title" name="title" required maxlength="160"
    placeholder="O que você quer realizar?">
  <label for="objective">Objetivo</label>
  <textarea id="objective" name="objective" required maxlength="2000"
    placeholder="Descreva o resultado esperado"></textarea>
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
      <label for="memory-category">Categoria</label>
      <input id="memory-category" name="category" required placeholder="decisão">
      <label for="memory-title">Título</label>
      <input id="memory-title" name="title" required>
      <label for="memory-content">Conteúdo</label>
      <textarea id="memory-content" name="content" required></textarea>
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
    return f"""<section class="panel doctor-card">
  <div class="health-ring"><strong>{available}/{service_count}</strong>
    <span>Serviços disponíveis</span></div>
  <div><span class="eyebrow">Application Health</span><h2>Saúde dos Serviços</h2>
  <p>Disponibilidade local de Workspace, Mission e Memory Services.</p>
  <span class="pill {css_class}">{status}</span>
  <p class="doctor-disclaimer">Este indicador não substitui o Genesis Doctor.</p></div>
</section>"""


def _render_settings() -> str:
    return """<section class="panel"><span class="eyebrow">Instância local</span>
  <h2>Configurações</h2><p class="muted">Configuração persistente, providers
  reais e autenticação permanecem fora do escopo desta versão.</p></section>"""


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
