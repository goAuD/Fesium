import socket
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from fesium.core.server import (
    LOOPBACK,
    PHP_ROUTER,
    PHPServer,
    find_available_port,
    is_port_in_use,
)

HTTP_TIMEOUT = 10


def _listening_socket():
    """A real listener on a port the OS picked, so the state is known."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((LOOPBACK, 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


def test_is_port_in_use_sees_a_port_that_is_taken():
    sock, port = _listening_socket()
    try:
        assert is_port_in_use(port) is True
    finally:
        sock.close()


def test_is_port_in_use_sees_a_port_that_is_free():
    sock, port = _listening_socket()
    sock.close()

    assert is_port_in_use(port) is False


def test_find_available_port_skips_the_taken_one():
    """Deterministic on purpose.

    The old version scanned 50000-50004 and asserted something was free, which
    depends on whatever else the machine is doing. It passed everywhere until
    a Windows CI runner reported all five in use, and then failed for reasons
    no one could reproduce. Holding the port makes the answer knowable.
    """
    sock, port = _listening_socket()
    try:
        found = find_available_port(port, max_attempts=4)

        assert found is not None
        assert found != port
        assert port < found < port + 4
    finally:
        sock.close()


def test_find_available_port_gives_up_when_nothing_is_free():
    sock, port = _listening_socket()
    try:
        assert find_available_port(port, max_attempts=1) is None
    finally:
        sock.close()


def test_is_port_in_use_returns_bool():
    assert isinstance(is_port_in_use(59999), bool)


# --- the address the servers actually use -----------------------------------


def test_the_loopback_address_is_a_literal_not_a_name():
    """Bind and connect on the same literal address, never on "localhost".

    The name resolves to ::1 before 127.0.0.1 on Windows and macOS, and both
    servers bind IPv4 only, so a client going by name tries IPv6 first against
    a port nothing is listening on. On Windows that measured 2131ms against
    2ms. On a macOS CI runner the attempt does not refuse at all - it hangs,
    and it held a test job open until GitHub's six hour limit.
    """
    assert LOOPBACK == "127.0.0.1"
    assert is_port_in_use.__defaults__ == (LOOPBACK,)


def test_the_php_server_reports_the_address_it_was_told_to_bind():
    server = PHPServer()
    server.port = 8000

    assert server.url == "http://127.0.0.1:8000"


def test_the_php_router_ships_with_the_package():
    """The dot-path filter only protects servers it is actually passed to."""
    assert PHP_ROUTER.is_file()
    assert PHP_ROUTER.name == "router.php"


def test_the_php_built_in_server_refuses_dot_paths(tmp_path):
    """`php -S` alone serves .env raw - the router restores the Python filter.

    Skipped where PHP is not installed; the guarantee matters wherever the
    PHP backend can start at all.
    """
    from fesium.core.environment import detect_php

    if not detect_php().php_available:
        pytest.skip("PHP is not installed on this machine")

    project = tmp_path / "site"
    project.mkdir()
    (project / "index.php").write_text("hello", encoding="utf-8")
    (project / ".env").write_text("DB_PASSWORD=hunter2", encoding="utf-8")

    server = PHPServer()
    assert server.start(str(project), port=8151) is True
    try:
        base = server.url
        # Plain and double-encoded dot paths both have to be refused.
        for path in ("/.env", "/%2Eenv", "/%252Eenv"):
            with pytest.raises(HTTPError) as caught:
                urlopen(base + path, timeout=HTTP_TIMEOUT)
            assert caught.value.code == 403
        body = urlopen(base + "/", timeout=HTTP_TIMEOUT).read().decode("utf-8")
        assert "hello" in body
    finally:
        server.stop()


def test_every_http_call_in_the_suite_has_a_timeout():
    """A request with no timeout waits forever, which is how a hang starts.

    Grep-shaped on purpose. The failure it prevents is not a wrong answer, it
    is a job that never finishes and so never says anything at all.
    """
    root = Path(__file__).resolve().parents[3] / "tests"
    offenders = []
    for path in sorted(root.rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "urlopen(" in line and "timeout" not in line and "def " not in line:
                offenders.append(f"{path.name}:{number}")

    assert offenders == [], f"add a timeout to these calls: {offenders}"
