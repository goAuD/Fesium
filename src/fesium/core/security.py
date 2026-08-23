import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Verbs that change state on every engine Fesium speaks to. A dialect with a
# larger vocabulary than SQLite's adds its own through `extra_destructive`.
DESTRUCTIVE_KEYWORDS = ("DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT", "REPLACE")


@lru_cache(maxsize=8)
def _destructive_in_body(keywords: frozenset[str]) -> re.Pattern[str]:
    return re.compile(r"\b(" + "|".join(sorted(keywords)) + r")\b", re.IGNORECASE)


@dataclass(frozen=True)
class QueryRisk:
    level: str
    requires_confirmation: bool
    first_word: str


def strip_sql_leading_noise(query: str) -> str:
    """Strip leading semicolons, whitespace, and SQL comments.

    Shared by :func:`classify_query_risk` and
    :func:`fesium.core.database.is_read_query` so comment-only prefixes can't
    smuggle destructive statements past one check while tripping the other.
    """
    remaining = query.lstrip("; \t\r\n")
    while remaining.startswith("--") or remaining.startswith("/*"):
        if remaining.startswith("--"):
            newline = remaining.find("\n")
            remaining = remaining[newline + 1 :] if newline != -1 else ""
        else:
            end = remaining.find("*/")
            remaining = remaining[end + 2 :] if end != -1 else ""
        remaining = remaining.lstrip("; \t\r\n")
    return remaining


def classify_query_risk(
    query: str,
    *,
    extra_destructive: frozenset[str] = frozenset(),
) -> QueryRisk:
    """Does this query need the user to confirm before it runs?

    ``extra_destructive`` carries the verbs that change state on the engine
    actually connected but are absent from the shared list because SQLite has
    no such statement - MySQL's ``GRANT`` and ``CALL``, for instance. Without
    it the confirmation gate is only ever as wide as SQLite's vocabulary, and
    a dialect with more verbs than that walks straight through it.
    """
    body = strip_sql_leading_noise(query)
    first_word = body.split()[0].upper() if body.split() else ""

    destructive = frozenset(DESTRUCTIVE_KEYWORDS) | frozenset(
        verb.upper() for verb in extra_destructive
    )
    requires_confirmation = first_word in destructive

    if first_word == "WITH" and _destructive_in_body(destructive).search(body):
        # WITH ... UPDATE/DELETE/INSERT CTE - treat as destructive.
        requires_confirmation = True

    return QueryRisk(
        level="danger" if requires_confirmation else "safe",
        requires_confirmation=requires_confirmation,
        first_word=first_word,
    )


def validate_single_sql_statement(query: str) -> tuple[bool, str]:
    stripped = query.strip()
    if not stripped:
        return False, "Query is empty"

    statements = [segment.strip() for segment in stripped.split(";") if segment.strip()]
    if len(statements) != 1:
        return False, "Only a single statement can be executed at a time"

    return True, ""


def normalize_existing_directory(pathlike) -> tuple[bool, str | Path]:
    candidate = Path(pathlike).expanduser().resolve()
    if not candidate.exists():
        return False, f"Path does not exist: {candidate}"
    if not candidate.is_dir():
        return False, f"Path is not a directory: {candidate}"
    return True, candidate
