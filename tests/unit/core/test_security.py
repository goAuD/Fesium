from fesium.core.security import (
    classify_query_risk,
    normalize_existing_directory,
    strip_sql_leading_noise,
    validate_single_sql_statement,
)


def test_classify_query_risk_marks_drop_as_destructive():
    risk = classify_query_risk("DROP TABLE users")

    assert risk.level == "danger"
    assert risk.requires_confirmation is True


def test_classify_query_risk_marks_select_as_safe():
    risk = classify_query_risk("SELECT * FROM users")

    assert risk.level == "safe"
    assert risk.requires_confirmation is False


def test_classify_query_risk_sees_through_line_comments():
    risk = classify_query_risk("-- looks harmless\nDROP TABLE users")

    assert risk.requires_confirmation is True
    assert risk.first_word == "DROP"


def test_classify_query_risk_sees_through_block_comments_and_semicolons():
    risk = classify_query_risk(";;/* wrapper */ DELETE FROM audit")

    assert risk.requires_confirmation is True
    assert risk.first_word == "DELETE"


def test_classify_query_risk_flags_with_cte_containing_update():
    risk = classify_query_risk(
        "WITH moved AS (SELECT id FROM tmp) UPDATE users SET active = 0 FROM moved"
    )

    assert risk.requires_confirmation is True
    assert risk.first_word == "WITH"


def test_classify_query_risk_leaves_pure_with_cte_safe():
    risk = classify_query_risk(
        "WITH active_users AS (SELECT id FROM users) SELECT * FROM active_users"
    )

    assert risk.requires_confirmation is False
    assert risk.first_word == "WITH"


def test_strip_sql_leading_noise_removes_mixed_prefixes():
    cleaned = strip_sql_leading_noise(";;  -- note\n/* block */  SELECT 1")

    assert cleaned.startswith("SELECT")


def test_normalize_existing_directory_rejects_missing_path(tmp_path):
    missing = tmp_path / "does-not-exist"

    ok, result = normalize_existing_directory(missing)

    assert ok is False
    assert "does not exist" in result


def test_normalize_existing_directory_accepts_real_directory(tmp_path):
    ok, result = normalize_existing_directory(tmp_path)

    assert ok is True
    assert result == tmp_path.resolve()


def test_validate_single_sql_statement_rejects_empty_query():
    ok, message = validate_single_sql_statement("   ")

    assert ok is False
    assert "empty" in message.lower()


def test_validate_single_sql_statement_rejects_multiple_statements():
    ok, message = validate_single_sql_statement("SELECT 1; SELECT 2;")

    assert ok is False
    assert "single statement" in message.lower()


def test_validate_single_sql_statement_accepts_one_statement():
    ok, message = validate_single_sql_statement("SELECT 1")

    assert ok is True
    assert message == ""
