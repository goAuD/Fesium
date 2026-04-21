import re
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union


DESTRUCTIVE_KEYWORDS = ("DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT", "REPLACE")

_DESTRUCTIVE_IN_BODY = re.compile(
    r"\b(" + "|".join(DESTRUCTIVE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


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


def classify_query_risk(query: str) -> QueryRisk:
    body = strip_sql_leading_noise(query)
    first_word = body.split()[0].upper() if body.split() else ""

    requires_confirmation = first_word in DESTRUCTIVE_KEYWORDS

    if first_word == "WITH" and _DESTRUCTIVE_IN_BODY.search(body):
        # WITH ... UPDATE/DELETE/INSERT CTE — treat as destructive.
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


def normalize_existing_directory(pathlike) -> Tuple[bool, Union[str, Path]]:
    candidate = Path(pathlike).expanduser().resolve()
    if not candidate.exists():
        return False, f"Path does not exist: {candidate}"
    if not candidate.is_dir():
        return False, f"Path is not a directory: {candidate}"
    return True, candidate
