from http import HTTPStatus
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from Interfaces.Companion.server import create_server


@pytest.fixture
def companion_server():
    server = create_server(port=0)
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


def test_home_page_loads_form_and_environment(companion_server):
    with urlopen(f"{companion_server}/", timeout=2) as response:
        content = response.read().decode("utf-8")

    assert response.status == HTTPStatus.OK
    assert "Gênesis" in content
    assert "Ambiente:" in content
    assert 'action="/missions"' in content


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
