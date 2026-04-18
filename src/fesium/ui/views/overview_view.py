from typing import Dict, List

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.status_badge import StatusBadge


def build_overview_cards(project_profile, php_summary: str, server_running: bool) -> List[Dict[str, str]]:
    return [
        {
            "title": "Workspace",
            "value": str(project_profile.root),
            "badge": project_profile.kind.title(),
            "tone": "accent.primary",
        },
        {
            "title": "Quick Actions",
            "value": "Start local server" if not server_running else "Open running server",
            "badge": "Ready" if not server_running else "Running",
            "tone": "accent.success" if server_running else "accent.primary",
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

    def __init__(self, master, project_profile, php_summary: str, server_running: bool):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure((0, 1), weight=1)

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

        for index, card in enumerate(build_overview_cards(project_profile, php_summary, server_running), start=2):
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
