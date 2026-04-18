from fesium.core.server import find_available_port, is_port_in_use


def test_find_available_port_returns_value_in_range():
    port = find_available_port(50000, max_attempts=5)
    assert port is not None
    assert 50000 <= port < 50005


def test_is_port_in_use_returns_bool():
    assert isinstance(is_port_in_use(59999), bool)
