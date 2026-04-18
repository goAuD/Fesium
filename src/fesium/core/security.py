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


def normalize_existing_directory(pathlike) -> Tuple[bool, Union[str, Path]]:
    candidate = Path(pathlike).expanduser().resolve()
    if not candidate.exists():
        return False, f"Path does not exist: {candidate}"
    if not candidate.is_dir():
        return False, f"Path is not a directory: {candidate}"
    return True, candidate
