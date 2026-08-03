from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from Core.configuration import Configuration
from Interfaces.Companion.application import CompanionApplication
from Interfaces.Companion.views import render_page, stylesheet


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_REQUEST_BYTES = 16_384


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    application: CompanionApplication | None = None,
) -> ThreadingHTTPServer:
    app = application or CompanionApplication.default(persistent=True)
    config = Configuration.default()

    class CompanionHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            path = parsed.path
            if path == "/static/styles.css":
                self._respond_bytes(
                    HTTPStatus.OK,
                    stylesheet(),
                    "text/css; charset=utf-8",
                )
                return
            if path == "/":
                self._respond(HTTPStatus.OK, self._render("dashboard"))
                return
            if path == "/workspaces":
                self._respond(HTTPStatus.OK, self._render("workspaces"))
                return
            if path == "/projects":
                self._respond(HTTPStatus.OK, self._render("projects"))
                return
            if path.startswith("/workspaces/"):
                workspace_id = unquote(path.removeprefix("/workspaces/"))
                result = app.open_workspace(workspace_id)
                status = (
                    HTTPStatus.OK
                    if result.is_success
                    else HTTPStatus.NOT_FOUND
                )
                self._respond(
                    status,
                    self._render(
                        "workspaces",
                        result=None if result.is_success else result,
                        workspace=(
                            result.data if result.is_success else None
                        ),
                    ),
                )
                return
            if path == "/missions":
                self._respond(HTTPStatus.OK, self._render("missions"))
                return
            if path == "/memory":
                fields = parse_qs(parsed.query, keep_blank_values=True)
                self._respond(
                    HTTPStatus.OK,
                    self._render(
                        "memory",
                        query=_first(fields, "q") or "",
                        category=_first(fields, "category") or "",
                    ),
                )
                return
            if path in ("/executions", "/doctor", "/settings"):
                self._respond(HTTPStatus.OK, self._render(path[1:]))
                return
            self._respond(HTTPStatus.NOT_FOUND, "Página não encontrada")

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            if path not in (
                "/missions",
                "/workspaces",
                "/projects",
                "/memory",
            ):
                self._respond(HTTPStatus.NOT_FOUND, "Página não encontrada")
                return

            content_length = self.headers.get("Content-Length")
            try:
                length = int(content_length or "0")
            except ValueError:
                self._respond(HTTPStatus.BAD_REQUEST, "Requisição inválida")
                return

            if length < 1 or length > MAX_REQUEST_BYTES:
                self._respond(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    "Tamanho de requisição inválido",
                )
                return

            body = self.rfile.read(length).decode("utf-8", errors="replace")
            fields = parse_qs(body, keep_blank_values=True)
            if path == "/projects":
                result = app.create_project(
                    workspace_id=_first(fields, "workspace_id"),
                    title=_first(fields, "title"),
                    client=_first(fields, "client"),
                    address=_first(fields, "address"),
                    description=_first(fields, "description"),
                )
                status = (
                    HTTPStatus.OK
                    if result.is_success
                    else HTTPStatus.BAD_REQUEST
                )
                self._respond(
                    status,
                    self._render("projects", result=result),
                )
                return

            if path == "/workspaces":
                result = app.create_workspace(
                    name=_first(fields, "name"),
                    description=_first(fields, "description"),
                )
                status = (
                    HTTPStatus.OK
                    if result.is_success
                    else HTTPStatus.BAD_REQUEST
                )
                self._respond(
                    status,
                    self._render(
                        "workspaces",
                        result=result,
                        workspace=result.data if result.is_success else None,
                    ),
                )
                return

            if path == "/memory":
                result = app.store_memory(
                    workspace_id=_first(fields, "workspace_id"),
                    category=_first(fields, "category"),
                    title=_first(fields, "title"),
                    content=_first(fields, "content"),
                )
                status = (
                    HTTPStatus.OK
                    if result.is_success
                    else HTTPStatus.BAD_REQUEST
                )
                self._respond(
                    status,
                    self._render("memory", result=result),
                )
                return

            result = app.execute_mission(
                title=_first(fields, "title"),
                objective=_first(fields, "objective"),
                workspace_id=_first(fields, "workspace_id"),
            )
            status = HTTPStatus.OK if result.is_success else HTTPStatus.BAD_REQUEST
            self._respond(
                status,
                self._render("missions", result=result),
            )

        def log_message(self, format: str, *args: object) -> None:
            return

        def _respond(self, status: HTTPStatus, content: str) -> None:
            self._respond_bytes(
                status,
                content.encode("utf-8"),
                "text/html; charset=utf-8",
            )

        def _respond_bytes(
            self,
            status: HTTPStatus,
            payload: bytes,
            content_type: str,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def _render(
            self,
            page: str,
            *,
            result=None,
            workspace=None,
            query: str = "",
            category: str = "",
        ) -> str:
            dashboard = app.dashboard()
            workspace_id = (
                dashboard.active_workspace.id
                if dashboard.active_workspace is not None
                else None
            )
            missions = app.list_missions(workspace_id=workspace_id).data
            executions = app.list_executions(workspace_id=workspace_id).data
            project_result = app.list_projects(workspace_id=workspace_id)
            projects = project_result.data if project_result.is_success else ()
            if page == "memory" and (query or category):
                memory_result = app.search_memories(
                    workspace_id=workspace_id,
                    text=query,
                    category=category or None,
                )
            else:
                memory_result = app.list_memories(workspace_id=workspace_id)
            memories = (
                getattr(memory_result.data, "records", memory_result.data)
                if memory_result.is_success
                else ()
            )
            return render_page(
                config,
                result,
                dashboard=dashboard,
                page=page,
                workspaces=app.list_workspaces().data,
                projects=projects,
                workspace=workspace,
                missions=missions,
                memories=memories,
                executions=executions,
                timeline=app.timeline(workspace_id=workspace_id),
                query=query,
                category=category,
            )

    return ThreadingHTTPServer((host, port), CompanionHandler)


def _first(fields: dict[str, list[str]], name: str) -> str | None:
    values = fields.get(name)
    return values[0] if values else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Genesis Companion v0.1")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    host, port = server.server_address[:2]
    print(f"Genesis Companion disponível em http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando Genesis Companion...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
