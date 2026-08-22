import socket

from fesium.core.server import find_available_port, is_port_in_use


def _listening_socket():
    """A real listener on a port the OS picked, so the state is known."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
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
