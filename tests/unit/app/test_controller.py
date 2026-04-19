from fesium.app.controller import FesiumController


def test_controller_starts_with_stopped_state(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    state = controller.state

    assert state.server_status == "stopped"
    assert state.backend_kind == "none"
    assert state.log_lines == ()


def test_controller_log_buffer_is_bounded(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path, log_limit=3)

    controller.append_log("one")
    controller.append_log("two")
    controller.append_log("three")
    controller.append_log("four")

    assert controller.state.log_lines == ("two", "three", "four")


def test_controller_rejects_nonpositive_log_limit(tmp_path):
    for log_limit in (0, -1):
        try:
            FesiumController(config=None, cwd=tmp_path, log_limit=log_limit)
        except ValueError as exc:
            assert "log_limit" in str(exc)
        else:
            raise AssertionError("expected ValueError for nonpositive log_limit")
