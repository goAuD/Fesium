from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union


@dataclass(frozen=True)
class QueryRisk:
    level: str
    requires_confirmation: bool
    first_word: str


def classify_query_risk(query: str) -> QueryRisk:
    first_word = query.lstrip("; \t\n").split()[0].upper() if query.strip() else ""
    destructive = {"DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE"}
    return QueryRisk(
        level="danger" if first_word in destructive else "safe",
        requires_confirmation=first_word in destructive,
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
