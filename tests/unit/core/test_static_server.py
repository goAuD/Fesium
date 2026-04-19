from pathlib import Path

from fesium.core.static_server import StaticServer


def test_static_server_starts_and_exposes_local_url(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    logs: list[str] = []
    server = StaticServer(on_log=logs.append)

    url = server.start(document_root=project, port=8123)

    assert url == "http://localhost:8123"
    assert server.is_running is True
    assert any("Started" in line for line in logs)

    server.stop()


def test_static_server_stop_marks_server_not_running(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    server = StaticServer()
    server.start(document_root=project, port=8124)
    server.stop()

    assert server.is_running is False
