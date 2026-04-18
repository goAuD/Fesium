from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class NavigationItem:
    id: str
    label: str
    description: str


def build_navigation_items() -> List[NavigationItem]:
    return [
        NavigationItem("overview", "Overview", "Workspace, health, and quick actions"),
        NavigationItem("server", "Server", "Serve the current project locally"),
        NavigationItem("database", "Database", "SQLite queries with safety defaults"),
        NavigationItem("environment", "Environment", "Local toolchain diagnostics"),
        NavigationItem("settings", "Settings", "Preferences and defaults"),
    ]
