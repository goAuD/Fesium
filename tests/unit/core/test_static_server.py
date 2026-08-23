import socket
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from fesium.core.static_server import StaticServer, is_hidden_path

# Every request here talks to a server this process just started on the
# loopback address, so ten seconds is generous. The point is not the number: a
# request with no timeout waits forever, and one that did held a macOS CI job
# open until GitHub's six hour limit.
HTTP_TIMEOUT = 10


def test_static_server_starts_serves_index_html_and_exposes_local_url(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    logs: list[str] = []
    server = StaticServer(on_log=logs.append)

    url = server.start(document_root=project, port=8123)
    body = urlopen(url, timeout=HTTP_TIMEOUT).read().decode("utf-8")

    assert url == "http://127.0.0.1:8123"
    assert server.is_running is True
    assert "hello" in body
    assert any("Started" in line for line in logs)

    server.stop()


def test_static_server_rejects_repeated_start(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    server = StaticServer()
    server.start(document_root=project, port=8124)

    try:
        server.start(document_root=project, port=8125)
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass

    server.stop()


def test_static_server_rejects_missing_document_root(tmp_path):
    server = StaticServer()
    missing = tmp_path / "missing"

    try:
        server.start(document_root=missing, port=8126)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_static_server_stop_marks_server_not_running_and_allows_restart(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    server = StaticServer()
    server.start(document_root=project, port=8127)
    server.stop()

    assert server.is_running is False

    url = server.start(document_root=project, port=8128)

    assert url == "http://127.0.0.1:8128"
    assert server.is_running is True

    server.stop()


def test_static_server_uses_next_available_port_when_requested_port_is_busy(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("localhost", 0))
        busy_port = probe.getsockname()[1]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("localhost", 0))
        alternate_port = probe.getsockname()[1]

    server = StaticServer()

    from pytest import MonkeyPatch

    monkeypatch = MonkeyPatch()
    monkeypatch.setattr("fesium.core.static_server.is_port_in_use", lambda port: port == busy_port)
    monkeypatch.setattr("fesium.core.static_server.find_available_port", lambda port: alternate_port)
    try:
        url = server.start(document_root=project, port=busy_port)
        assert url == f"http://127.0.0.1:{alternate_port}"
        assert server.port == alternate_port
        server.stop()
    finally:
        monkeypatch.undo()


# --- what a project folder must not hand out --------------------------------


@pytest.mark.parametrize("path", [
    "/.env",
    "/.git/config",
    "/%2Eenv",
    "/sub/.env",
    "/.ssh/id_rsa",
    "/.env?ignored=1",
    # Double-encoded forms: is_hidden_path decodes once, translate_path
    # decodes again, so only decoding to a fixed point sees what the stdlib
    # will open.
    "/%252Eenv",
    "/%252Egit/config",
    "/sub/%252Eenv",
])
def test_a_dot_path_is_never_served(path):
    """Fesium reads four keys out of a project's .env and never the credentials.

    Serving the file whole over HTTP undid that care: the static server handed
    out .env and the whole of .git for any project served from its own root.
    """
    assert is_hidden_path(path) is True


@pytest.mark.parametrize("path", ["/", "/index.html", "/assets/app.css", "/a.b/c"])
def test_an_ordinary_path_is_still_served(path):
    assert is_hidden_path(path) is False


def test_the_server_refuses_dot_files_over_http(tmp_path):
    project = tmp_path / "site"
    (project / ".git").mkdir(parents=True)
    (project / ".env").write_text("DB_PASSWORD=hunter2", encoding="utf-8")
    (project / ".git" / "config").write_text("[core]", encoding="utf-8")
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    server = StaticServer()
    url = server.start(document_root=project, port=8141)
    try:
        # The double-encoded form is the interesting one: it decodes to a
        # dot path only on the second pass, inside translate_path.
        for path in ("/.env", "/.git/config", "/%2Eenv", "/%252Eenv"):
            with pytest.raises(HTTPError) as caught:
                urlopen(url + path, timeout=HTTP_TIMEOUT)
            assert caught.value.code == 403
        assert "hello" in urlopen(url, timeout=HTTP_TIMEOUT).read().decode("utf-8")
    finally:
        server.stop()


# --- a folder with nothing to serve -----------------------------------------


def test_a_folder_without_an_index_explains_itself(tmp_path):
    """A directory listing of a source repo looks like a broken website.

    It also says nothing about why, which is the whole problem: a SvelteKit
    project has no index.html at its root, and the listing gave no hint that a
    build step is what is missing.
    """
    project = tmp_path / "app"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text("{}", encoding="utf-8")

    server = StaticServer()
    url = server.start(
        document_root=project, port=8142,
        hints=["This is a SvelteKit project.", "Run npm run dev on port 5173."])
    try:
        with pytest.raises(HTTPError) as caught:
            urlopen(url, timeout=HTTP_TIMEOUT)
        body = caught.value.read().decode("utf-8")
    finally:
        server.stop()

    assert caught.value.code == 404
    assert "Nothing to serve here" in body
    assert "SvelteKit" in body
    assert "5173" in body
    # The thing it replaced: a listing of the folder's contents.
    assert "package.json" not in body
    assert "src" not in body


def test_the_no_index_page_stands_alone_without_hints(tmp_path):
    project = tmp_path / "empty"
    project.mkdir()

    server = StaticServer()
    url = server.start(document_root=project, port=8143)
    try:
        with pytest.raises(HTTPError) as caught:
            urlopen(url, timeout=HTTP_TIMEOUT)
        body = caught.value.read().decode("utf-8")
    finally:
        server.stop()

    assert "index.html" in body
    assert "Fesium" in body


def test_request_logs_reach_the_app_instead_of_stderr(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hi</h1>", encoding="utf-8")

    logs: list[str] = []
    server = StaticServer(on_log=logs.append)
    url = server.start(document_root=project, port=8144)
    try:
        urlopen(url, timeout=HTTP_TIMEOUT).read()
    finally:
        server.stop()

    assert any("GET /" in line for line in logs)
