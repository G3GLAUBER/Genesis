from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from Core.configuration import Configuration
from Interfaces.Companion.application import CompanionApplication
from Interfaces.Companion.views import render_page


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_REQUEST_BYTES = 16_384


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    application: CompanionApplication | None = None,
) -> ThreadingHTTPServer:
    app = application or CompanionApplication.default()
    config = Configuration.default()

    class CompanionHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if urlsplit(self.path).path != "/":
                self._respond(HTTPStatus.NOT_FOUND, "Página não encontrada")
                return
            self._respond(HTTPStatus.OK, render_page(config))

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/missions":
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
            result = app.execute_mission(
                title=_first(fields, "title"),
                objective=_first(fields, "objective"),
            )
            status = HTTPStatus.OK if result.is_success else HTTPStatus.BAD_REQUEST
            self._respond(status, render_page(config, result))

        def log_message(self, format: str, *args: object) -> None:
            return

        def _respond(self, status: HTTPStatus, content: str) -> None:
            payload = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

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
