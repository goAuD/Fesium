from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationItem:
    id: str
    label: str
    description: str
    icon: str
    """Name of a bundled Lucide icon in assets/icons/lucide/."""


def build_navigation_items() -> list[NavigationItem]:
    return [
        NavigationItem("overview", "Overview", "Workspace, health, and quick actions", "layout-dashboard"),
        NavigationItem("server", "Server", "Serve the current project locally", "server"),
        NavigationItem("database", "Database", "SQLite queries with safety defaults", "database"),
        NavigationItem("environment", "Diagnostics", "Runtime checks and project readiness", "activity"),
        NavigationItem("guide", "Guide", "What Fesium is for and how to use it well", "book-open"),
        NavigationItem("settings", "Settings", "Reserved for future app preferences", "settings"),
    ]
