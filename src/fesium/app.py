from dataclasses import dataclass
from pathlib import Path

from fesium.core.paths import AppPaths


@dataclass(frozen=True)
class AppMetadata:
    name: str
    tagline: str


def build_window_title(version: str) -> str:
    return f"Fesium v{version}"


def build_default_paths(home_dir: Path = None) -> AppPaths:
    return AppPaths(home_dir=home_dir or Path.home())
