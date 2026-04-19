from pathlib import Path
from typing import Dict, List, Optional

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.status_badge import StatusBadge


def _format_project_kind(project_kind: str) -> str:
    return project_kind.replace("_", " ").title() if project_kind else "Unknown"


def _format_server_status(server_status: str) -> str:
    labels = {
        "running": "Running",
        "stopped": "Stopped",
        "error": "Error",
    }
    return labels.get(server_status, server_status.replace("_", " ").title() or "Unknown")


def build_overview_cards(
    *,
    project_root: Path | None,
    project_kind: str,
    php_summary: str,
    server_status: str,
    local_url: str,
) -> List[Dict[str, str]]:
    quick_action_value = (
        f"Running at {local_url}" if server_status == "running" and local_url else "Open the Server view to manage the active site"
    )

    return [
        {
            "title": "Workspace",
            "value": str(project_root) if project_root else "Not selected",
            "badge": _format_project_kind(project_kind),
            "tone": "accent.primary",
        },
        {
            "title": "Quick Actions",
            "value": quick_action_value,
            "badge": _format_server_status(server_status),
            "tone": "accent.success" if server_status == "running" else "accent.primary",
        },
        {
            "title": "Environment Health",
            "value": php_summary or "PHP not found in PATH",
            "badge": "Healthy" if php_summary else "Missing",
            "tone": "accent.success" if php_summary else "accent.danger",
        },
    ]


class OverviewView(ctk.CTkFrame):
    """Overview dashboard for workspace, quick actions, and health."""

    def __init__(
        self,
        master,
        project_profile=None,
        php_summary: str = "",
        server_running: bool = False,
        *,
        project_root: Optional[Path] = None,
        project_kind: str = "",
        server_status: Optional[str] = None,
        local_url: str = "",
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure((0, 1), weight=1)

        resolved_project_root = project_root if project_root is not None else getattr(project_profile, "root", None)
        resolved_project_kind = project_kind or getattr(project_profile, "kind", "")
        resolved_server_status = server_status or ("running" if server_running else "stopped")

        title = ctk.CTkLabel(
            self,
            text="Overview",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Workspace, quick actions, and environment health",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 20))

        for index, card in enumerate(
            build_overview_cards(
                project_root=resolved_project_root,
                project_kind=resolved_project_kind,
                php_summary=php_summary,
                server_status=resolved_server_status,
                local_url=local_url,
            ),
            start=2,
        ):
            panel = PanelCard(self)
            panel.grid(row=index, column=0, columnspan=2, sticky="ew", pady=8)
            panel.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(
                panel,
                text=card["title"],
                text_color=get_color_token("text.primary"),
                font=get_font_token("body_medium"),
            )
            label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

            badge = StatusBadge(panel, text=card["badge"], tone=card["tone"])
            badge.grid(row=0, column=1, sticky="e", padx=16, pady=(16, 8))

            value = ctk.CTkLabel(
                panel,
                text=card["value"],
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                justify="left",
                wraplength=800,
            )
            value.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))
