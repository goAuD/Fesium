from pathlib import Path
from urllib.request import urlopen

from fesium.core.static_server import StaticServer


def test_static_server_starts_serves_index_html_and_exposes_local_url(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    logs: list[str] = []
    server = StaticServer(on_log=logs.append)

    url = server.start(document_root=project, port=8123)
    body = urlopen(url).read().decode("utf-8")

    assert url == "http://localhost:8123"
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

    assert url == "http://localhost:8128"
    assert server.is_running is True

    server.stop()
