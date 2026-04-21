from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import customtkinter as ctk

from fesium.ui.theme.styles import get_button_style, get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody
from fesium.ui.widgets.status_badge import StatusBadge

ACTION_BUTTON_SPECS = (
    ("select_project_button", "Select Project Folder", "select_project"),
    ("start_button", "Start", "start"),
    ("stop_button", "Stop", "stop"),
    ("restart_button", "Restart", "restart"),
    ("open_browser_button", "Open in Browser", "open_in_browser"),
)

ONE_ROW_SERVER_ACTION_LAYOUT = [["select_project", "start", "stop", "restart", "open_in_browser"]]
TWO_ROW_SERVER_ACTION_LAYOUT = [["select_project", "start", "stop"], ["restart", "open_in_browser"]]


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


def _format_port_label(port: int | None, local_url: str) -> str:
    if local_url:
        parsed = urlsplit(local_url)
        if parsed.port is not None:
            return str(parsed.port)
    return str(port) if port else "Not set"


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
    port: int | None,
    backend_kind: str,
    server_status: str,
    local_url: str,
    last_error: str,
    log_lines: tuple[str, ...] = (),
) -> dict[str, Any]:
    is_running = server_status == "running"
    has_project = document_root is not None

    return {
        "selected_project": _format_path(project_root),
        "project_type": _format_project_kind(project_kind),
        "document_root": _format_path(document_root),
        "backend_label": _format_backend_label(backend_kind),
        "port_label": _format_port_label(port, local_url),
        "local_url": local_url or "Not running",
        "status_label": _format_status_label(server_status),
        "status_tone": _status_tone(server_status),
        "last_error": last_error,
        "log_text": "\n".join(log_lines),
        "actions": {
            "select_project": True,
            "start": has_project and not is_running,
            "stop": is_running,
            "restart": is_running,
            "open_in_browser": is_running and bool(local_url),
        },
    }


def resolve_server_action_layout(available_width: int) -> list[list[str]]:
    if available_width >= 980:
        return ONE_ROW_SERVER_ACTION_LAYOUT
    return TWO_ROW_SERVER_ACTION_LAYOUT


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
        log_lines: tuple[str, ...] = (),
        on_select_project=None,
        on_start=None,
        on_stop=None,
        on_restart=None,
        on_open_browser=None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        resolved_status = server_status or ("running" if is_running else "stopped")
        resolved_url = local_url or (f"http://localhost:{port}" if port else "")
        model = build_server_view_model(
            project_root=project_root or document_root,
            project_kind=project_kind,
            document_root=document_root,
            port=port,
            backend_kind=backend_kind,
            server_status=resolved_status,
            local_url=resolved_url if is_running or server_status == "running" else local_url,
            last_error=last_error,
            log_lines=log_lines,
        )

        def _noop() -> None:
            return None

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

        body = ScrollableViewBody(self)
        body.grid(row=2, column=0, columnspan=2, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        details_panel = PanelCard(body, surface_variant="inset")
        details_panel.grid(row=0, column=0, sticky="ew")
        details_content = details_panel.content_frame
        details_content.grid_columnconfigure(0, weight=1)

        details_title = ctk.CTkLabel(
            details_content,
            text="Runtime Summary",
            text_color=get_color_token("accent.primary"),
            font=get_font_token("section_heading"),
        )
        details_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        details = [
            ("Selected Project", model["selected_project"]),
            ("Project Type", model["project_type"]),
            ("Document Root", model["document_root"]),
            ("Backend", model["backend_label"]),
            ("Port", model["port_label"]),
            ("Local URL", model["local_url"]),
            ("Status", model["status_label"]),
        ]

        for row, (label_text, value_text) in enumerate(details):
            label = ctk.CTkLabel(
                details_content,
                text=label_text,
                text_color=get_color_token("text.primary"),
                font=get_font_token("body_medium"),
            )
            label.grid(row=row * 2 + 1, column=0, sticky="w", padx=16, pady=(8 if row == 0 else 10, 4))

            value = ctk.CTkLabel(
                details_content,
                text=value_text,
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                justify="left",
                wraplength=800,
            )
            value.grid(
                row=row * 2 + 2,
                column=0,
                sticky="w",
                padx=16,
                pady=(0, 4 if row < len(details) - 1 else 16),
            )

        actions_panel = PanelCard(body, surface_variant="inset")
        actions_panel.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        self.actions_content = actions_panel.content_frame

        self.actions_title = ctk.CTkLabel(
            self.actions_content,
            text="Controls",
            text_color=get_color_token("accent.primary"),
            font=get_font_token("section_heading"),
        )
        self.actions_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        self._action_buttons: dict[str, ctk.CTkButton] = {}
        action_variants = {
            "select_project": "secondary",
            "start": "primary",
            "stop": "danger",
            "restart": "secondary",
            "open_in_browser": "secondary",
        }
        for attr_name, label_text, action_key in ACTION_BUTTON_SPECS:
            commands = {
                "select_project": on_select_project or _noop,
                "start": on_start or _noop,
                "stop": on_stop or _noop,
                "restart": on_restart or _noop,
                "open_in_browser": on_open_browser or _noop,
            }
            button = ctk.CTkButton(
                self.actions_content,
                text=label_text,
                state="normal" if model["actions"][action_key] else "disabled",
                **get_button_style(action_variants[action_key]),
                command=commands[action_key],
            )
            setattr(self, attr_name, button)
            self._action_buttons[action_key] = button

        logs_panel = PanelCard(body, surface_variant="inset_strong")
        logs_panel.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        logs_content = logs_panel.content_frame
        logs_content.grid_columnconfigure(0, weight=1)
        logs_content.grid_rowconfigure(1, weight=1)

        logs_title = ctk.CTkLabel(
            logs_content,
            text="Logs",
            text_color=get_color_token("accent.primary"),
            font=get_font_token("section_heading"),
        )
        logs_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        self.log_textbox = ctk.CTkTextbox(
            logs_content,
            fg_color=get_color_token("bg.panel_alt"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            height=260,
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.log_textbox.insert("1.0", model["log_text"])
        self.log_textbox.configure(state="disabled")

        if model["last_error"]:
            error_label = ctk.CTkLabel(
                body,
                text=model["last_error"],
                text_color=get_color_token("accent.danger"),
                font=get_font_token("body"),
                justify="left",
                wraplength=900,
            )
            error_label.grid(row=3, column=0, sticky="w", pady=(16, 0))

        self._render_action_buttons(resolve_server_action_layout(self.winfo_reqwidth()))
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, _event) -> None:
        available_width = self.winfo_width() or self.winfo_reqwidth()
        self._render_action_buttons(resolve_server_action_layout(available_width))

    def _render_action_buttons(self, layout: list[list[str]]) -> None:
        max_columns = max(len(row) for row in layout)

        for column in range(5):
            self.actions_content.grid_columnconfigure(column, weight=1 if column < max_columns else 0)

        self.actions_title.grid_configure(columnspan=max_columns)

        for button in self._action_buttons.values():
            button.grid_forget()

        for row_index, row_actions in enumerate(layout, start=1):
            is_last_row = row_index == len(layout)
            for column, action_key in enumerate(row_actions):
                button = self._action_buttons[action_key]
                button.grid(
                    row=row_index,
                    column=column,
                    sticky="ew",
                    padx=(16 if column == 0 else 8, 16 if column == len(row_actions) - 1 else 8),
                    pady=(0, 16 if is_last_row else 8),
                )
