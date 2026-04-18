from fesium.core.environment import summarize_php_environment


def test_summarize_php_environment_missing_php(monkeypatch):
    monkeypatch.setattr("fesium.core.environment.check_php_installed", lambda: False)

    status = summarize_php_environment()

    assert status.php_available is False
    assert "PHP not found" in status.summary
