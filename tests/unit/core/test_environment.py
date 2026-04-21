import subprocess
from types import SimpleNamespace

import pytest

from fesium.core.environment import (
    EnvironmentStatus,
    detect_php,
    summarize_php_environment,
)


def test_detect_php_returns_available_with_version(monkeypatch):
    def fake_run(cmd, **kwargs):
        assert cmd == ["php", "-v"]
        assert kwargs.get("timeout") == pytest.approx(3.0)
        return SimpleNamespace(returncode=0, stdout="PHP 8.4.0 (cli)\nrest\n", stderr="")

    monkeypatch.setattr("fesium.core.environment.subprocess.run", fake_run)

    status = detect_php()

    assert status.php_available is True
    assert status.php_version == "PHP 8.4.0 (cli)"
    assert status.summary == "PHP 8.4.0 (cli)"


def test_detect_php_handles_missing_binary(monkeypatch):
    def fake_run(*_, **__):
        raise FileNotFoundError("no php")

    monkeypatch.setattr("fesium.core.environment.subprocess.run", fake_run)

    status = detect_php()

    assert status.php_available is False
    assert "PHP not found" in status.summary


def test_detect_php_handles_subprocess_timeout(monkeypatch):
    def fake_run(*_, **kwargs):
        raise subprocess.TimeoutExpired(cmd="php", timeout=kwargs.get("timeout", 3.0))

    monkeypatch.setattr("fesium.core.environment.subprocess.run", fake_run)

    status = detect_php(timeout=0.5)

    assert status.php_available is False
    assert "timed out" in status.summary
    assert "0.5" in status.summary


def test_detect_php_handles_nonzero_exit(monkeypatch):
    def fake_run(*_, **__):
        return SimpleNamespace(returncode=1, stdout="", stderr="broken")

    monkeypatch.setattr("fesium.core.environment.subprocess.run", fake_run)

    status = detect_php()

    assert status.php_available is False
    assert status.summary == "PHP returned a non-zero exit status"


def test_summarize_php_environment_delegates_to_detect_php(monkeypatch):
    sentinel = EnvironmentStatus(True, "PHP 9.0.0", "PHP 9.0.0")
    monkeypatch.setattr("fesium.core.environment.detect_php", lambda: sentinel)

    assert summarize_php_environment() is sentinel
