from fesium.core.project_database import (
    DatabaseReadiness,
    DatabaseRequirement,
    describe_database_readiness,
    detect_database_requirement,
    parse_env_values,
    probe_database,
)

LARAVEL_ENV = """
APP_NAME=Laravel
APP_ENV=local

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=streamapp
DB_USERNAME=root
DB_PASSWORD=hunter2
"""


def test_parse_env_values_reads_only_the_connection_keys():
    """Credentials are never read. Anything Fesium reads can reach a screen."""
    values = parse_env_values(LARAVEL_ENV)

    assert values == {
        "DB_CONNECTION": "mysql",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_DATABASE": "streamapp",
    }
    assert "DB_PASSWORD" not in values
    assert "DB_USERNAME" not in values


def test_parse_env_values_strips_quotes_and_trailing_comments():
    values = parse_env_values(
        'DB_CONNECTION="mysql"\nDB_DATABASE=\'my app\'\nDB_HOST=localhost # the default\n'
    )

    assert values["DB_CONNECTION"] == "mysql"
    assert values["DB_DATABASE"] == "my app"
    assert values["DB_HOST"] == "localhost"


def test_parse_env_values_ignores_comments_and_blank_lines():
    assert parse_env_values("# DB_CONNECTION=pgsql\n\n   \nDB_CONNECTION=sqlite\n") == {
        "DB_CONNECTION": "sqlite"
    }


def test_detect_database_requirement_reads_a_laravel_env(tmp_path):
    (tmp_path / ".env").write_text(LARAVEL_ENV, encoding="utf-8")

    requirement = detect_database_requirement(tmp_path)

    assert requirement == DatabaseRequirement(
        connection="mysql", host="127.0.0.1", port=3306, database="streamapp"
    )
    assert requirement.needs_a_server is True
    assert requirement.address == "127.0.0.1:3306"


def test_detect_database_requirement_falls_back_to_the_default_port(tmp_path):
    (tmp_path / ".env").write_text("DB_CONNECTION=pgsql\nDB_HOST=127.0.0.1\n", encoding="utf-8")

    assert detect_database_requirement(tmp_path).port == 5432


def test_detect_database_requirement_survives_a_nonsense_port(tmp_path):
    (tmp_path / ".env").write_text("DB_CONNECTION=mysql\nDB_PORT=not-a-port\n", encoding="utf-8")

    assert detect_database_requirement(tmp_path).port == 3306


def test_detect_database_requirement_returns_none_without_a_project_or_env(tmp_path):
    assert detect_database_requirement(None) is None
    assert detect_database_requirement(tmp_path) is None


def test_sqlite_needs_no_server(tmp_path):
    (tmp_path / ".env").write_text("DB_CONNECTION=sqlite\n", encoding="utf-8")
    requirement = detect_database_requirement(tmp_path)

    assert requirement.needs_a_server is False
    assert probe_database(requirement) is None


def test_probe_database_reports_a_refused_connection():
    """Port 1 on loopback is not something anyone serves from."""
    requirement = DatabaseRequirement(connection="mysql", host="127.0.0.1", port=1, database="demo")

    assert probe_database(requirement, timeout=0.5) is False


def test_probe_database_finds_a_listening_socket():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        requirement = DatabaseRequirement(
            connection="mysql", host="127.0.0.1", port=port, database="demo"
        )
        assert probe_database(requirement, timeout=0.5) is True


def test_describe_readiness_explains_that_fesium_runs_no_database_server():
    """The message a Laravel-on-MySQL user needs, instead of a stack trace."""
    readiness = DatabaseReadiness(
        requirement=DatabaseRequirement(
            connection="mysql", host="127.0.0.1", port=3306, database="streamapp"
        ),
        reachable=False,
    )

    described = describe_database_readiness(readiness)

    assert described["tone"] == "accent.danger"
    assert described["meta"] == "unreachable"
    assert "127.0.0.1:3306" in described["detail"]
    assert "streamapp" in described["detail"]
    assert "does not run a database server" in described["detail"]


def test_describe_readiness_is_calm_when_the_server_answers():
    readiness = DatabaseReadiness(
        requirement=DatabaseRequirement(
            connection="mysql", host="127.0.0.1", port=3306, database="streamapp"
        ),
        reachable=True,
    )

    assert describe_database_readiness(readiness)["tone"] == "accent.success"


def test_describe_readiness_handles_a_project_without_a_database():
    described = describe_database_readiness(DatabaseReadiness(requirement=None, reachable=None))

    assert described["meta"] == "none"
    assert described["tone"] == "text.secondary"
