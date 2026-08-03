from __future__ import annotations

from html import escape

from Core.result import Result
from Engines.Workspace import Workspace


def render_workspace_page(
    workspaces: tuple[Workspace, ...],
    *,
    selected: Workspace | None = None,
    result: Result | None = None,
) -> str:
    feedback = _render_feedback(result)
    cards = "".join(_render_workspace_card(item) for item in workspaces)
    if not cards:
        cards = '<p class="muted">Nenhum Workspace ativo.</p>'
    detail = _render_workspace_detail(selected) if selected is not None else ""
    return f"""<section id="workspaces">
  <div class="section-heading">
    <div><p class="eyebrow">Organização</p><h2>Workspaces</h2></div>
  </div>
  {feedback}
  <form method="post" action="/workspaces" class="workspace-form">
    <label for="workspace-name">Nome</label>
    <input id="workspace-name" name="name" required maxlength="120">
    <label for="workspace-description">Descrição</label>
    <textarea id="workspace-description" name="description"
      maxlength="1000"></textarea>
    <button type="submit">Criar Workspace</button>
  </form>
</section>
<section>
  <h2>Workspaces ativos</h2>
  <div class="workspace-grid">{cards}</div>
</section>
{detail}"""


def _render_workspace_card(workspace: Workspace) -> str:
    return f"""<article class="workspace-card">
  <span class="status">{escape(workspace.status.value.upper())}</span>
  <h3>{escape(workspace.name)}</h3>
  <p>{escape(workspace.description) or 'Sem descrição'}</p>
  <p class="meta">{len(workspace.mission_ids)} missão(ões)</p>
  <a class="button-link" href="/workspaces/{escape(workspace.id)}">Abrir</a>
</article>"""


def _render_workspace_detail(workspace: Workspace) -> str:
    missions = "".join(
        f"<li><code>{escape(mission_id)}</code></li>"
        for mission_id in workspace.mission_ids
    )
    if not missions:
        missions = '<li class="muted">Nenhuma missão associada.</li>'
    return f"""<section id="workspace-detail">
  <p class="eyebrow">Workspace aberto</p>
  <h2>{escape(workspace.name)}</h2>
  <p>{escape(workspace.description) or 'Sem descrição'}</p>
  <p class="meta">ID: {escape(workspace.id)} · Criado em:
    {escape(workspace.created_at.isoformat())}</p>
  <h3>Missões</h3>
  <ul class="mission-list">{missions}</ul>
</section>"""


def _render_feedback(result: Result | None) -> str:
    if result is None:
        return ""
    css_class = "notice" if result.is_success else "notice error"
    return f'<p class="{css_class}">{escape(result.message)}</p>'
