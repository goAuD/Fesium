from pathlib import Path
from typing import Dict

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.status_badge import StatusBadge


def build_server_status(document_root: Path, port: int, is_running: bool) -> Dict[str, str]:
    return {
        "label": "Running" if is_running else "Stopped",
        "document_root": str(document_root),
        "url": f"http://localhost:{port}",
        "tone": "accent.success" if is_running else "accent.warning",
    }


class ServerView(ctk.CTkFrame):
    """Server operations view for current project serving state."""

    def __init__(self, master, document_root: Path, port: int, is_running: bool):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        status = build_server_status(document_root, port, is_running)

        title = ctk.CTkLabel(
            self,
            text="Server",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        badge = StatusBadge(self, text=status["label"], tone=status["tone"])
        badge.grid(row=0, column=1, sticky="e")

        subtitle = ctk.CTkLabel(
            self,
            text="Serve the current project locally",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 20))

        panel = PanelCard(self)
        panel.grid(row=2, column=0, columnspan=2, sticky="ew")
        panel.grid_columnconfigure(0, weight=1)

        details = [
            ("Document Root", status["document_root"]),
            ("Local URL", status["url"]),
            ("Status", status["label"]),
        ]

        for row, (label_text, value_text) in enumerate(details):
            label = ctk.CTkLabel(
                panel,
                text=label_text,
                text_color=get_color_token("text.primary"),
                font=get_font_token("body_medium"),
            )
            label.grid(row=row * 2, column=0, sticky="w", padx=16, pady=(16 if row == 0 else 10, 4))

            value = ctk.CTkLabel(
                panel,
                text=value_text,
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                justify="left",
            )
            value.grid(row=row * 2 + 1, column=0, sticky="w", padx=16, pady=(0, 4 if row < len(details) - 1 else 16))
