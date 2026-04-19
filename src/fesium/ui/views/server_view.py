from pathlib import Path
from typing import Any

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.status_badge import StatusBadge


def _format_path(path: Path | None) -> str:
    return str(path) if path else "Not selected"


def _format_project_kind(project_kind: str) -> str:
    return project_kind.replace("_", " ").title() if project_kind else "Unknown"


def _format_backend_label(backend_kind: str) -> str:
    labels = {
        "php": "PHP Built-in Server",
        "static": "Static Fallback",
        "none": "Not Selected",
    }
    return labels.get(backend_kind, backend_kind.replace("_", " ").title() or "Unknown")


def _format_status_label(server_status: str) -> str:
    labels = {
        "running": "Running",
        "stopped": "Stopped",
        "error": "Error",
    }
    return labels.get(server_status, server_status.replace("_", " ").title() or "Unknown")


def _status_tone(server_status: str) -> str:
    tones = {
        "running": "accent.success",
        "stopped": "accent.warning",
        "error": "accent.danger",
    }
    return tones.get(server_status, "accent.primary")


def build_server_view_model(
    *,
    project_root: Path | None,
    project_kind: str,
    document_root: Path | None,
    backend_kind: str,
    server_status: str,
    local_url: str,
    last_error: str,
) -> dict[str, Any]:
    is_running = server_status == "running"
    has_project = document_root is not None

    return {
        "selected_project": _format_path(project_root),
        "project_type": _format_project_kind(project_kind),
        "document_root": _format_path(document_root),
        "backend_label": _format_backend_label(backend_kind),
        "local_url": local_url or "Not running",
        "status_label": _format_status_label(server_status),
        "status_tone": _status_tone(server_status),
        "last_error": last_error,
        "actions": {
            "select_project": True,
            "start": has_project and not is_running,
            "stop": is_running,
            "restart": is_running,
            "open_in_browser": is_running and bool(local_url),
        },
    }


class ServerView(ctk.CTkFrame):
    """Server operations view for current project serving state."""

    def __init__(
        self,
        master,
        document_root: Path | None,
        port: int | None = None,
        is_running: bool = False,
        *,
        project_root: Path | None = None,
        project_kind: str = "unknown",
        backend_kind: str = "none",
        server_status: str | None = None,
        local_url: str = "",
        last_error: str = "",
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        resolved_status = server_status or ("running" if is_running else "stopped")
        resolved_url = local_url or (f"http://localhost:{port}" if port else "")
        model = build_server_view_model(
            project_root=project_root or document_root,
            project_kind=project_kind,
            document_root=document_root,
            backend_kind=backend_kind,
            server_status=resolved_status,
            local_url=resolved_url if is_running or server_status == "running" else local_url,
            last_error=last_error,
        )

        title = ctk.CTkLabel(
            self,
            text="Server",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        badge = StatusBadge(self, text=model["status_label"], tone=model["status_tone"])
        badge.grid(row=0, column=1, sticky="e")

        subtitle = ctk.CTkLabel(
            self,
            text="Serve the current project locally",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 20))

        details_panel = PanelCard(self)
        details_panel.grid(row=2, column=0, columnspan=2, sticky="ew")
        details_panel.grid_columnconfigure(0, weight=1)

        details = [
            ("Selected Project", model["selected_project"]),
            ("Project Type", model["project_type"]),
            ("Document Root", model["document_root"]),
            ("Backend", model["backend_label"]),
            ("Local URL", model["local_url"]),
            ("Status", model["status_label"]),
        ]

        for row, (label_text, value_text) in enumerate(details):
            label = ctk.CTkLabel(
                details_panel,
                text=label_text,
                text_color=get_color_token("text.primary"),
                font=get_font_token("body_medium"),
            )
            label.grid(row=row * 2, column=0, sticky="w", padx=16, pady=(16 if row == 0 else 10, 4))

            value = ctk.CTkLabel(
                details_panel,
                text=value_text,
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                justify="left",
                wraplength=800,
            )
            value.grid(
                row=row * 2 + 1,
                column=0,
                sticky="w",
                padx=16,
                pady=(0, 4 if row < len(details) - 1 else 16),
            )

        actions_panel = PanelCard(self)
        actions_panel.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        actions_panel.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        actions_title = ctk.CTkLabel(
            actions_panel,
            text="Controls",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
        )
        actions_title.grid(row=0, column=0, columnspan=5, sticky="w", padx=16, pady=(16, 12))

        button_specs = [
            ("select_project_button", "Select Project Folder", "select_project"),
            ("start_button", "Start", "start"),
            ("stop_button", "Stop", "stop"),
            ("restart_button", "Restart", "restart"),
            ("open_browser_button", "Open in Browser", "open_in_browser"),
        ]

        for column, (attr_name, label_text, action_key) in enumerate(button_specs):
            button = ctk.CTkButton(
                actions_panel,
                text=label_text,
                state="normal" if model["actions"][action_key] else "disabled",
            )
            button.grid(row=1, column=column, sticky="ew", padx=(16 if column == 0 else 8, 16 if column == 4 else 8), pady=(0, 16))
            setattr(self, attr_name, button)

        if model["last_error"]:
            error_label = ctk.CTkLabel(
                self,
                text=model["last_error"],
                text_color=get_color_token("accent.danger"),
                font=get_font_token("body"),
                justify="left",
                wraplength=900,
            )
            error_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(16, 0))
