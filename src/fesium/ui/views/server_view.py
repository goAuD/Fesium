from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token, get_shape_token
from fesium.ui.widgets.bento import BentoGrid
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.button import Button
from fesium.ui.widgets.meta_list import MetaList
from fesium.ui.widgets.tile import Tile
from fesium.ui.widgets.view_header import HEADER_GAP, ViewHeader

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
    """Serving state, the controls that change it, and the live log.

    The runtime facts used to run label-above-value down 580px of the page,
    which pushed the log - the only thing here that changes while you watch -
    below the fold. They are a two-column meta list now, and the log tile takes
    every pixel the other two do not need.
    """

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
        self.grid_rowconfigure(1, weight=1)

        resolved_status = server_status or ("running" if is_running else "stopped")
        model = build_server_view_model(
            project_root=project_root,
            project_kind=project_kind,
            document_root=document_root,
            port=port,
            backend_kind=backend_kind,
            server_status=resolved_status,
            local_url=local_url,
            last_error=last_error,
            log_lines=log_lines,
        )
        self._model = model
        self._action_buttons: dict[str, Button] = {}

        header = ViewHeader(
            self,
            "Server",
            "Serve the current project locally",
            badges=((model["status_label"], model["status_tone"]),),
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, HEADER_GAP))

        grid = BentoGrid(self)
        grid.grid(row=1, column=0, sticky="nsew")

        grid.place_tile(self._build_runtime_tile(grid, model), row=0, column=0, span=12)
        grid.place_tile(
            self._build_controls_tile(
                grid, model, on_select_project, on_start, on_stop, on_restart, on_open_browser
            ),
            row=1,
            column=0,
            span=12,
        )
        grid.place_tile(self._build_logs_tile(grid, model), row=2, column=0, span=12, row_weight=1)

        if model["last_error"]:
            error_label = BodyText(self, model["last_error"], tone="accent.danger")
            error_label.grid(row=2, column=0, sticky="ew", pady=(HEADER_GAP, 0))

    def _build_runtime_tile(self, parent, model):
        tile = Tile(parent, "Runtime", meta=model["local_url"])
        rows = (
            ("Selected Project", model["selected_project"]),
            ("Project Type", model["project_type"]),
            ("Document Root", model["document_root"]),
            ("Backend", model["backend_label"]),
            ("Port", model["port_label"]),
        )
        MetaList(tile.body, rows).grid(row=0, column=0, sticky="new")
        return tile

    def _build_controls_tile(
        self, parent, model, on_select_project, on_start, on_stop, on_restart, on_open_browser
    ):
        tile = Tile(parent, "Controls")
        self.actions_content = tile.body

        def _noop():
            return None

        commands = {
            "select_project": on_select_project or _noop,
            "start": on_start or _noop,
            "stop": on_stop or _noop,
            "restart": on_restart or _noop,
            "open_in_browser": on_open_browser or _noop,
        }
        variants = {
            "select_project": "secondary",
            "start": "primary",
            "stop": "danger",
            "restart": "secondary",
            "open_in_browser": "secondary",
        }
        for attr_name, label_text, action_key in ACTION_BUTTON_SPECS:
            button = Button(
                self.actions_content,
                label_text,
                variant=variants[action_key],
                enabled=model["actions"][action_key],
                command=commands[action_key],
            )
            setattr(self, attr_name, button)
            self._action_buttons[action_key] = button

        self._render_action_buttons(ONE_ROW_SERVER_ACTION_LAYOUT)
        self.bind("<Configure>", self._on_resize, add="+")
        return tile

    def _build_logs_tile(self, parent, model):
        tile = Tile(parent, "Logs", meta="live", surface="bg.panel_alt")
        tile.body.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(
            tile.body,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            border_width=0,
            corner_radius=get_shape_token("input.radius"),
            height=60,
        )
        self.log_textbox.grid(row=0, column=0, sticky="nsew")
        self.log_textbox.insert("1.0", model["log_text"])
        self.log_textbox.configure(state="disabled")
        return tile

    def _on_resize(self, _event=None) -> None:
        self._render_action_buttons(resolve_server_action_layout(self.winfo_width()))

    def _render_action_buttons(self, layout) -> None:
        max_columns = max(len(row) for row in layout)
        for column in range(5):
            self.actions_content.grid_columnconfigure(column, weight=0)

        for button in self._action_buttons.values():
            button.grid_forget()

        for row_index, row_actions in enumerate(layout):
            for column, action_key in enumerate(row_actions):
                self._action_buttons[action_key].grid(
                    row=row_index,
                    column=column,
                    sticky="w",
                    padx=(0 if column == 0 else 8, 0),
                    pady=(0 if row_index == 0 else 8, 0),
                )
        # Spare width goes to the far right so the row stays left-aligned.
        self.actions_content.grid_columnconfigure(max_columns, weight=1)
