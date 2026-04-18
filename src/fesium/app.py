from dataclasses import dataclass


@dataclass(frozen=True)
class AppMetadata:
    name: str
    tagline: str


def build_window_title(version: str) -> str:
    return f"Fesium v{version}"
