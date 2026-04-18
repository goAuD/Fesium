from fesium.core.security import classify_query_risk, normalize_existing_directory


def test_classify_query_risk_marks_drop_as_destructive():
    risk = classify_query_risk("DROP TABLE users")

    assert risk.level == "danger"
    assert risk.requires_confirmation is True


def test_classify_query_risk_marks_select_as_safe():
    risk = classify_query_risk("SELECT * FROM users")

    assert risk.level == "safe"
    assert risk.requires_confirmation is False


def test_normalize_existing_directory_rejects_missing_path(tmp_path):
    missing = tmp_path / "does-not-exist"

    ok, result = normalize_existing_directory(missing)

    assert ok is False
    assert "does not exist" in result


def test_normalize_existing_directory_accepts_real_directory(tmp_path):
    ok, result = normalize_existing_directory(tmp_path)

    assert ok is True
    assert result == tmp_path.resolve()
