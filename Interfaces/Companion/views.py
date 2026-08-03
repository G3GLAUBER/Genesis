from __future__ import annotations

from html import escape

from Core.configuration import Configuration
from Core.result import Result
from Engines.Workspace import Workspace
from Interfaces.Companion.application import (
    CompanionDashboard,
    CompanionExecution,
)
from Interfaces.Workspace import render_workspace_page


def render_page(
    config: Configuration,
    result: Result | None = None,
    *,
    dashboard: CompanionDashboard | None = None,
    page: str = "home",
    workspaces: tuple[Workspace, ...] = (),
    workspace: Workspace | None = None,
) -> str:
    if page == "workspaces":
        content = render_workspace_page(
            workspaces,
            selected=workspace,
            result=result,
        )
    else:
        content = _render_welcome() if result is None else _render_result(result)
    dashboard_content = _render_dashboard(dashboard)
    active_workspace = dashboard.active_workspace if dashboard else None
    workspace_field = (
        f'<input type="hidden" name="workspace_id" '
        f'value="{escape(active_workspace.id)}">'
        if active_workspace is not None
        else ""
    )
    mission_content = f"""<section>
    <h2>Criar missão</h2>
    <form method="post" action="/missions">
      {workspace_field}
      <label for="title">Título</label>
      <input id="title" name="title" required maxlength="160">
      <label for="objective">Objetivo</label>
      <textarea id="objective" name="objective" required
        maxlength="2000"></textarea>
      <button type="submit">Criar e executar missão</button>
    </form>
  </section>
  {content}"""
    page_content = content if page == "workspaces" else mission_content
    return f"""<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Genesis Companion</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #09111f; color: #e8edf6; }}
    main {{ width: min(1040px, 90%); margin: 32px auto 60px; }}
    header, section {{ background: #111c2e; border: 1px solid #263750;
      border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
    h1 {{ color: #79e2c0; margin: 0; }}
    h2, h3 {{ color: #b8c8e6; }}
    nav {{ display: flex; gap: 12px; margin: 18px 0 0; }}
    a {{ color: #79e2c0; }}
    nav a {{ text-decoration: none; font-weight: 700; }}
    .meta, .muted {{ color: #91a3bf; }}
    .eyebrow {{ color: #79e2c0; font-size: .78rem; font-weight: 800;
      letter-spacing: .12em; text-transform: uppercase; }}
    label {{ display: block; margin: 14px 0 6px; font-weight: 700; }}
    input, textarea {{ box-sizing: border-box; width: 100%; padding: 12px;
      border-radius: 8px; border: 1px solid #40526f; background: #0a1424;
      color: #fff; }}
    textarea {{ min-height: 110px; resize: vertical; }}
    button {{ margin-top: 18px; padding: 12px 18px; border: 0;
      border-radius: 8px; background: #79e2c0; color: #07130f;
      font-weight: 800; cursor: pointer; }}
    ol {{ padding-left: 24px; }}
    li {{ margin-bottom: 16px; }}
    .status {{ display: inline-block; padding: 4px 9px; border-radius: 20px;
      background: #203750; color: #9ce8d1; font-size: .85rem; }}
    .error {{ border-color: #a95353; color: #ffc2c2; }}
    .dashboard, .workspace-grid {{ display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }}
    .metric, .workspace-card {{ background: #0a1424; border: 1px solid #263750;
      border-radius: 12px; padding: 18px; }}
    .metric strong {{ display: block; color: #fff; font-size: 1.55rem;
      margin-top: 8px; }}
    .workspace-card h3 {{ margin-bottom: 8px; }}
    .button-link {{ display: inline-block; margin-top: 8px; padding: 9px 13px;
      border: 1px solid #79e2c0; border-radius: 8px; text-decoration: none; }}
    .notice {{ padding: 12px; border: 1px solid #387c69; border-radius: 8px;
      background: #102820; }}
    .notice.error {{ background: #2b171b; }}
    code {{ color: #b8c8e6; overflow-wrap: anywhere; }}
    pre {{ white-space: pre-wrap; background: #09111f; padding: 12px;
      border-radius: 8px; }}
  </style>
</head>
<body><main>
  <header>
    <p class="muted">Sistema Operacional de Inteligência</p>
    <h1>{escape(config.system_name)}</h1>
    <p class="meta">Companion v{escape(config.version)} · Ambiente:
      {escape(config.environment)}</p>
    <nav><a href="/">Dashboard</a><a href="/workspaces">Workspaces</a></nav>
  </header>
  {dashboard_content}
  {page_content}
</main></body>
</html>"""


def _render_dashboard(dashboard: CompanionDashboard | None) -> str:
    if dashboard is None:
        return ""
    active_name = (
        dashboard.active_workspace.name
        if dashboard.active_workspace is not None
        else "Nenhum"
    )
    return f"""<section id="dashboard">
  <p class="eyebrow">Dashboard</p>
  <h2>Visão geral</h2>
  <div class="dashboard">
    <div class="metric"><span class="muted">Workspace ativo</span>
      <strong>{escape(active_name)}</strong></div>
    <div class="metric"><span class="muted">Workspaces</span>
      <strong>{dashboard.workspace_count}</strong></div>
    <div class="metric"><span class="muted">Missões</span>
      <strong>{dashboard.mission_count}</strong></div>
  </div>
</section>"""


def _render_welcome() -> str:
    return """<section><h2>Pronto para começar</h2>
<p class="muted">A missão será planejada em três etapas e executada localmente
com o FakeProvider, sem chamadas de rede.</p></section>"""


def _render_result(result: Result) -> str:
    if not result.is_success or not isinstance(result.data, CompanionExecution):
        return (
            '<section class="error"><h2>Não foi possível executar</h2><p>'
            f"{escape(result.message)}</p></section>"
        )

    execution = result.data
    step_results = {
        item.step_id: item for item in execution.report.step_results
    }
    steps = "".join(
        _render_step(step, step_results[step.id])
        for step in execution.plan.steps
    )
    return f"""<section id="mission">
  <h2>Missão criada</h2>
  <h3>{escape(execution.mission.title)}</h3>
  <p>{escape(execution.mission.objective)}</p>
  <p class="meta">ID: {escape(execution.mission.id)} · Origem:
    {escape(execution.mission.source)}</p>
  <p class="meta">Workspace:
    {escape(execution.workspace.name if execution.workspace else '—')}</p>
</section>
<section id="plan">
  <h2>Plano demonstrativo</h2>
  <p>Provider: <strong>{escape(execution.provider_id)}</strong></p>
  <ol>{steps}</ol>
</section>
<section id="report">
  <h2>Relatório final</h2>
  <p>Status: <span class="status">
    {escape(execution.report.status.value.upper())}</span></p>
  <p class="meta">Mission: {escape(execution.report.mission_id)}<br>
    Plan: {escape(execution.report.plan_id)}<br>
    Etapas: {len(execution.report.step_results)}</p>
</section>"""


def _render_step(step, result) -> str:
    output = result.content or result.error or "Sem conteúdo"
    provider = result.provider_id or "—"
    dependencies = ", ".join(step.dependencies) or "nenhuma"
    return f"""<li>
  <h3>{escape(step.title)}</h3>
  <p>{escape(step.description)}</p>
  <p class="meta">Ordem: {step.order} · Capability:
    {escape(step.capability or '—')} · Dependências: {escape(dependencies)}</p>
  <p>Status: <span class="status">{escape(result.status.value.upper())}</span>
    · Provider: {escape(provider)}</p>
  <pre>{escape(output)}</pre>
</li>"""
