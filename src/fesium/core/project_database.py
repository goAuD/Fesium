"""What database a project expects, and whether it is actually there.

Fesium serves PHP; it does not run a database server. A Laravel project
pointed at MySQL therefore starts fine and then fails on the first query with
a connection error from deep inside the framework, which tells a student
nothing about what to do. This reads the project's own configuration and
checks the address, so the answer arrives before the site is opened.
"""

import socket
from dataclasses import dataclass
from pathlib import Path

# Only these keys are ever read out of a .env. Credentials are deliberately not
# in the list: Fesium has no use for them, and anything it reads can end up on
# screen or in a log.
ENV_KEYS = ("DB_CONNECTION", "DB_HOST", "DB_PORT", "DB_DATABASE")

DEFAULT_PORTS = {"mysql": 3306, "mariadb": 3306, "pgsql": 5432, "sqlsrv": 1433}

# Long enough for a busy local server to answer, short enough not to stall the
# UI when the host is simply not there.
PROBE_TIMEOUT_SECONDS = 0.75


@dataclass(frozen=True)
class DatabaseRequirement:
    """The database a project asks for, as read from its own configuration."""

    connection: str
    host: str
    port: int | None
    database: str

    @property
    def needs_a_server(self) -> bool:
        """SQLite is a file. Everything else means a server has to be running."""
        return bool(self.connection) and self.connection not in {"sqlite", ""}

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}" if self.host and self.port else ""


@dataclass(frozen=True)
class DatabaseReadiness:
    requirement: DatabaseRequirement | None
    reachable: bool | None
    """None when nothing was probed - no project, no config, or SQLite."""


@dataclass(frozen=True)
class ConnectionSettings:
    """What the user typed to reach a server-backed database.

    Deliberately carries no password. ``DatabaseRequirement`` has none either,
    and with both structures credential-free there is nowhere natural for a
    password to be persisted by accident: it lives in one private attribute on
    the controller, for the length of a session, and never reaches disk.
    """

    engine: str
    """Which driver this describes - ``mysql`` today."""
    host: str
    port: int
    database: str
    user: str

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


def parse_env_values(text: str) -> dict[str, str]:
    """Pull the whitelisted keys out of .env text.

    Deliberately small: enough for the KEY=VALUE lines Laravel writes, with
    quotes and trailing comments stripped. It is not a dotenv implementation
    and does not need to be.
    """
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        if key not in ENV_KEYS:
            continue

        value = value.strip()
        if value[:1] in {'"', "'"} and value[-1:] == value[:1] and len(value) > 1:
            value = value[1:-1]
        else:
            # An unquoted value ends at a whitespace-separated comment.
            value = value.split(" #")[0].strip()
        values[key] = value

    return values


def detect_database_requirement(project_root: Path | None) -> DatabaseRequirement | None:
    """Read a Laravel project's .env. Returns None when there is nothing to read."""
    if project_root is None:
        return None

    env_file = Path(project_root) / ".env"
    try:
        text = env_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    values = parse_env_values(text)
    connection = values.get("DB_CONNECTION", "").strip().lower()
    if not connection:
        return None

    host = values.get("DB_HOST", "").strip()
    raw_port = values.get("DB_PORT", "").strip()
    try:
        port = int(raw_port) if raw_port else DEFAULT_PORTS.get(connection)
    except ValueError:
        port = DEFAULT_PORTS.get(connection)

    return DatabaseRequirement(
        connection=connection,
        host=host,
        port=port,
        database=values.get("DB_DATABASE", "").strip(),
    )


def probe_database(
    requirement: DatabaseRequirement | None,
    *,
    timeout: float = PROBE_TIMEOUT_SECONDS,
) -> bool | None:
    """Is something accepting connections at the address the project wants?

    A TCP connect is all that is checked. Fesium does not authenticate, and it
    does not need to: refused is the failure students actually hit.
    """
    if requirement is None or not requirement.needs_a_server or not requirement.host or not requirement.port:
        return None

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((requirement.host, requirement.port)) == 0
    except OSError:
        return False


def summarize_project_database(project_root: Path | None) -> DatabaseReadiness:
    requirement = detect_database_requirement(project_root)
    return DatabaseReadiness(requirement=requirement, reachable=probe_database(requirement))


def describe_database_readiness(readiness: DatabaseReadiness) -> dict[str, str]:
    """Turn the probe into something worth reading on screen."""
    requirement = readiness.requirement

    if requirement is None:
        return {
            "label": "Not configured",
            "detail": "No .env with a DB_CONNECTION was found, so nothing here needs a database server.",
            "tone": "text.secondary",
            "meta": "none",
        }

    if not requirement.needs_a_server:
        return {
            "label": f"{requirement.connection} (file)",
            "detail": "A file-backed database. Nothing needs to be running for this project to query it.",
            "tone": "accent.success",
            "meta": requirement.connection,
        }

    name = requirement.database or "unnamed database"
    if readiness.reachable:
        return {
            "label": f"{requirement.connection} at {requirement.address}",
            "detail": f"Something is accepting connections there, so {name} should be reachable.",
            "tone": "accent.success",
            "meta": "reachable",
        }

    return {
        "label": f"{requirement.connection} at {requirement.address}",
        "detail": (
            f"Nothing is listening at {requirement.address}, so queries against {name} will fail with a "
            f"connection error. Fesium serves PHP but does not run a database server - start your own "
            f"{requirement.connection} service, or point the project at SQLite."
        ),
        "tone": "accent.danger",
        "meta": "unreachable",
    }
