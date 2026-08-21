from fesium.core.preferences import (
    MAX_PORT,
    MIN_PORT,
    describe_startup_project,
    normalize_default_project,
    normalize_port,
)


def test_normalize_port_accepts_a_plain_number():
    result = normalize_port("9001")

    assert result.ok is True
    assert result.value == 9001
    assert "9001" in result.message


def test_normalize_port_tolerates_surrounding_whitespace():
    assert normalize_port("  8080  ").value == 8080


def test_normalize_port_rejects_non_numeric_input():
    result = normalize_port("eight thousand")

    assert result.ok is False
    assert result.value is None
    assert "whole number" in result.message


def test_normalize_port_rejects_privileged_and_out_of_range_ports():
    """Below 1024 needs elevation on Linux and macOS, which students rarely have."""
    for candidate in (80, MIN_PORT - 1, 0, MAX_PORT + 1, 999999):
        result = normalize_port(candidate)
        assert result.ok is False, candidate
        assert str(MIN_PORT) in result.message and str(MAX_PORT) in result.message


def test_normalize_port_accepts_the_range_boundaries():
    assert normalize_port(MIN_PORT).ok is True
    assert normalize_port(MAX_PORT).ok is True


def test_normalize_default_project_resolves_an_existing_folder(tmp_path):
    result = normalize_default_project(str(tmp_path))

    assert result.ok is True
    assert result.value == str(tmp_path.resolve())


def test_normalize_default_project_treats_empty_input_as_clearing_it():
    for blank in ("", "   ", None):
        result = normalize_default_project(blank)
        assert result.ok is True
        assert result.value == ""
        assert "cleared" in result.message


def test_normalize_default_project_rejects_a_missing_folder(tmp_path):
    result = normalize_default_project(str(tmp_path / "gone"))

    assert result.ok is False
    assert "does not exist" in result.message


def test_normalize_default_project_rejects_a_file(tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("x", encoding="utf-8")

    result = normalize_default_project(str(target))

    assert result.ok is False
    assert "not a directory" in result.message


def test_describe_startup_project_prefers_the_last_project_when_restoring():
    summary = describe_startup_project(
        last_project="/projects/portal",
        default_project="/projects/default",
        restore_last_project=True,
    )

    assert "/projects/portal" in summary


def test_describe_startup_project_uses_the_default_when_not_restoring():
    summary = describe_startup_project(
        last_project="/projects/portal",
        default_project="/projects/default",
        restore_last_project=False,
    )

    assert "/projects/default" in summary
    assert "/projects/portal" not in summary


def test_describe_startup_project_falls_back_to_the_default_when_nothing_was_opened():
    summary = describe_startup_project(
        last_project="",
        default_project="/projects/default",
        restore_last_project=True,
    )

    assert "/projects/default" in summary


def test_describe_startup_project_admits_when_it_will_use_the_working_directory():
    summary = describe_startup_project(
        last_project="",
        default_project="",
        restore_last_project=True,
    )

    assert "started from" in summary
