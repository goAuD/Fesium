import subprocess
from types import SimpleNamespace

import pytest

from fesium.core import environment
from fesium.core.environment import (
    EnvironmentStatus,
    detect_php,
    summarize_php_environment,
)

PHP_BINARY = "C:/php/php.EXE"


@pytest.fixture(autouse=True)
def php_on_path(monkeypatch):
    """Put a known PHP on PATH for every test in this module.

    detect_php resolves the binary before running it, so a test that stubs
    only subprocess.run silently depends on the machine actually having PHP.
    That passed on Windows and Ubuntu runners, which ship one, and failed on
    macOS, which does not. Resolution is stubbed here so no test in this file
    can ask the machine anything.
    """
    monkeypatch.setattr(environment.shutil, "which", lambda _name: PHP_BINARY)


def test_detect_php_returns_available_with_version(monkeypatch):
    def fake_run(cmd, **kwargs):
        # The probe runs what it resolved, so the path it reports is
        # definitely the binary that answered.
        assert cmd == [PHP_BINARY, "-v"]
        assert kwargs.get("timeout") == pytest.approx(3.0)
        return SimpleNamespace(returncode=0, stdout="PHP 8.4.0 (cli)\nrest\n", stderr="")

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    status = detect_php()

    assert status.php_available is True
    assert status.path == PHP_BINARY
    assert status.php_version == "PHP 8.4.0 (cli)"
    assert status.summary == "PHP 8.4.0 (cli)"


def test_detect_php_reports_missing_when_not_on_path(monkeypatch):
    """No PHP anywhere on PATH: the probe must not be spawned at all."""
    monkeypatch.setattr(environment.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        environment.subprocess,
        "run",
        lambda *_a, **_k: pytest.fail("php was run despite not being on PATH"),
    )

    status = detect_php()

    assert status.php_available is False
    assert status.summary == "PHP not found in PATH"
    assert status.path == ""


def test_detect_php_handles_missing_binary(monkeypatch):
    """Resolved, then gone before it could run - a rare but real race."""
    def fake_run(*_, **__):
        raise FileNotFoundError("no php")

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    status = detect_php()

    assert status.php_available is False
    assert "PHP not found" in status.summary


def test_detect_php_handles_subprocess_timeout(monkeypatch):
    def fake_run(*_, **kwargs):
        raise subprocess.TimeoutExpired(cmd="php", timeout=kwargs.get("timeout", 3.0))

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    status = detect_php(timeout=0.5)

    assert status.php_available is False
    assert "timed out" in status.summary
    assert "0.5" in status.summary
    # The binary that hung is worth naming - that is the one to look at.
    assert status.path == PHP_BINARY


def test_detect_php_handles_nonzero_exit(monkeypatch):
    def fake_run(*_, **__):
        return SimpleNamespace(returncode=1, stdout="", stderr="broken")

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    status = detect_php()

    assert status.php_available is False
    assert status.summary == "PHP returned a non-zero exit status"
    assert status.path == PHP_BINARY


def test_summarize_php_environment_delegates_to_detect_php(monkeypatch):
    sentinel = EnvironmentStatus(True, "PHP 9.0.0", "PHP 9.0.0")
    environment.reset_php_cache()
    monkeypatch.setattr("fesium.core.environment.detect_php", lambda: sentinel)

    assert summarize_php_environment() is sentinel


def _counting_probe(counter, status):
    def probe(*_args, **_kwargs):
        counter.append(1)
        return status
    return probe


def test_summarize_php_environment_probes_once_within_the_window(monkeypatch):
    """The probe costs ~78ms and eleven UI handlers used to trigger it each."""
    environment.reset_php_cache()
    calls = []
    status = environment.EnvironmentStatus(True, "PHP 8.5.2", "PHP 8.5.2", PHP_BINARY)
    monkeypatch.setattr(environment, "detect_php", _counting_probe(calls, status))

    first = environment.summarize_php_environment()
    for _ in range(20):
        environment.summarize_php_environment()

    assert first is status
    assert len(calls) == 1


def test_summarize_php_environment_probes_again_once_the_window_passes(monkeypatch):
    environment.reset_php_cache()
    calls = []
    status = environment.EnvironmentStatus(False, "", "PHP not found in PATH")
    monkeypatch.setattr(environment, "detect_php", _counting_probe(calls, status))

    environment.summarize_php_environment()
    environment.summarize_php_environment(max_age=0)

    assert len(calls) == 2


def test_reset_php_cache_makes_the_next_answer_fresh(monkeypatch):
    """Someone diagnosing a missing PHP will install it and look again."""
    environment.reset_php_cache()
    calls = []
    monkeypatch.setattr(
        environment,
        "detect_php",
        _counting_probe(calls, environment.EnvironmentStatus(False, "", "missing")),
    )

    environment.summarize_php_environment()
    environment.reset_php_cache()
    environment.summarize_php_environment()

    assert len(calls) == 2


def test_detect_php_is_never_cached(monkeypatch):
    """The uncached probe is what tests and freshness-critical callers use."""
    environment.reset_php_cache()
    calls = []
    completed = SimpleNamespace(returncode=0, stdout="PHP 8.5.2 (cli)")

    def fake_run(*_args, **_kwargs):
        calls.append(1)
        return completed

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    for _ in range(3):
        environment.detect_php()

    assert len(calls) == 3
