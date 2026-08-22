from pathlib import Path

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token, get_shape_token
from fesium.ui.widgets.bento import BentoGrid
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.button import Button
from fesium.ui.widgets.tile import Tile, text_tile
from fesium.ui.widgets.view_header import HEADER_GAP, ViewHeader


def _format_project_kind(project_kind: str) -> str:
    return project_kind.replace("_", " ").title() if project_kind else "Unknown"


def _format_server_status(server_status: str) -> str:
    labels = {
        "running": "Running",
        "stopped": "Stopped",
        "error": "Error",
    }
    return labels.get(server_status, server_status.replace("_", " ").title() or "Unknown")


def build_overview_model(
    *,
    project_root: Path | None,
    project_kind: str,
    php_summary: str,
    server_status: str,
    local_url: str,
    log_lines: tuple[str, ...] = (),
) -> dict:
    """Everything the Overview renders, as plain data.

    The old version returned four equal cards, one of them titled Quick Actions
    with no actions in it. Serving state is the thing you open this page to see,
    so it gets its own shape here and the largest tile on screen.
    """
    is_running = server_status == "running"
    recent_lines = log_lines[-8:]
    has_error = any("ERROR" in line for line in recent_lines)

    return {
        "server_status": _format_server_status(server_status),
        "server_tone": (
            "accent.success" if is_running else "accent.danger" if server_status == "error" else "accent.warning"
        ),
        "local_url": local_url if is_running and local_url else "Not serving",
        "project_root": str(project_root) if project_root else "Not selected",
        "project_kind": _format_project_kind(project_kind),
        "php_summary": php_summary or "PHP not found in PATH",
        "php_healthy": bool(php_summary),
        "activity": "\n".join(recent_lines) if recent_lines else "Nothing yet. Select a project to get started.",
        "activity_meta": "attention" if has_error else f"{len(recent_lines)} lines" if recent_lines else "idle",
        "activity_tone": "accent.danger" if has_error else "text.secondary",
        "actions": {
            "start": project_root is not None and not is_running,
            "stop": is_running,
            "open_in_browser": is_running and bool(local_url),
        },
    }


def build_overview_cards(
    *,
    project_root: Path | None,
    project_kind: str,
    php_summary: str,
    server_status: str,
    local_url: str,
    log_lines: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    """Legacy card shape, kept for callers that still want a flat summary."""
    model = build_overview_model(
        project_root=project_root,
        project_kind=project_kind,
        php_summary=php_summary,
        server_status=server_status,
        local_url=local_url,
        log_lines=log_lines,
    )
    quick_action_value = (
        f"Running at {local_url}"
        if server_status == "running" and local_url
        else "Open the Server view to manage the active site"
    )
    return [
        {
            "title": "Workspace",
            "value": model["project_root"],
            "badge": model["project_kind"],
            "tone": "accent.primary",
        },
        {
            "title": "Quick Actions",
            "value": quick_action_value,
            "badge": model["server_status"],
            "tone": model["server_tone"],
        },
        {
            "title": "Environment Health",
            "value": model["php_summary"],
            "badge": "Healthy" if model["php_healthy"] else "Missing",
            "tone": "accent.success" if model["php_healthy"] else "accent.danger",
        },
        {
            "title": "Recent Activity",
            "value": model["activity"],
            "badge": "Attention" if model["activity_tone"] == "accent.danger" else "Recent",
            "tone": model["activity_tone"],
        },
    ]


class OverviewView(ctk.CTkFrame):
    """What is running, where, and what just happened - with the controls inline."""

    def __init__(
        self,
        master,
        project_profile=None,
        php_summary: str = "",
        server_running: bool = False,
        *,
        project_root: Path | None = None,
        project_kind: str = "",
        server_status: str | None = None,
        local_url: str = "",
        log_lines: tuple[str, ...] = (),
        on_start=None,
        on_stop=None,
        on_open_browser=None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        resolved_root = project_root if project_root is not None else getattr(project_profile, "root", None)
        resolved_kind = project_kind or getattr(project_profile, "kind", "")
        resolved_status = server_status or ("running" if server_running else "stopped")

        model = build_overview_model(
            project_root=resolved_root,
            project_kind=resolved_kind,
            php_summary=php_summary,
            server_status=resolved_status,
            local_url=local_url,
            log_lines=log_lines,
        )

        header = ViewHeader(
            self,
            "Overview",
            "Workspace, quick actions, and environment health",
            badges=((model["server_status"], model["server_tone"]),),
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, HEADER_GAP))

        grid = BentoGrid(self)
        grid.grid(row=1, column=0, sticky="nsew")

        grid.place_tile(
            self._build_server_tile(grid, model, on_start, on_stop, on_open_browser),
            row=0,
            column=0,
            span=8,
        )
        grid.place_tile(self._build_environment_tile(grid, model), row=0, column=8, span=4)
        grid.place_tile(self._build_workspace_tile(grid, model), row=1, column=0, span=4, row_weight=1)
        grid.place_tile(self._build_activity_tile(grid, model), row=1, column=4, span=8, row_weight=1)

    def _build_server_tile(self, parent, model, on_start, on_stop, on_open_browser):
        tile = Tile(parent, "Local Server", meta=model["local_url"])
        body = tile.body

        status = ctk.CTkLabel(
            body,
            text=model["server_status"],
            text_color=get_color_token(model["server_tone"]),
            font=get_font_token("metric"),
            anchor="w",
        )
        status.grid(row=0, column=0, sticky="w")

        url = BodyText(body, model["local_url"], tone="text.secondary")
        url.grid(row=1, column=0, sticky="ew", pady=(2, 16))

        # The card this replaces was titled Quick Actions and contained none.
        # The buttons live in their own frame so the labels above, which span
        # the tile, cannot stretch the columns underneath them.
        actions_row = ctk.CTkFrame(body, fg_color="transparent")
        actions_row.grid(row=2, column=0, sticky="w")

        actions = (
            ("Start", "primary", "start", on_start),
            ("Stop", "danger", "stop", on_stop),
            ("Open in Browser", "secondary", "open_in_browser", on_open_browser),
        )
        for column, (label, variant, key, command) in enumerate(actions):
            Button(
                actions_row,
                label,
                variant=variant,
                enabled=model["actions"][key],
                command=command or (lambda: None),
            ).grid(row=0, column=column, padx=(0 if column == 0 else 8, 0))

        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(3, weight=1)
        return tile

    def _build_environment_tile(self, parent, model):
        return text_tile(
            parent,
            "Environment",
            model["php_summary"],
            meta="healthy" if model["php_healthy"] else "missing",
            meta_tone="accent.success" if model["php_healthy"] else "accent.danger",
        )

    def _build_workspace_tile(self, parent, model):
        """The path alone. The project kind is already this tile's meta, so a
        label column beside it only cost width - and in a quarter-width tile
        that reserve left the path 131px to render 157px in."""
        return text_tile(parent, "Workspace", model["project_root"], meta=model["project_kind"])

    def _build_activity_tile(self, parent, model):
        tile = Tile(
            parent,
            "Activity",
            meta=model["activity_meta"],
            meta_tone=model["activity_tone"],
            surface="bg.panel_alt",
        )
        tile.body.grid_rowconfigure(0, weight=1)

        self.activity_textbox = ctk.CTkTextbox(
            tile.body,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            font=get_font_token("mono"),
            border_width=0,
            corner_radius=get_shape_token("input.radius"),
            height=60,
        )
        self.activity_textbox.grid(row=0, column=0, sticky="nsew")
        self.activity_textbox.insert("1.0", model["activity"])
        self.activity_textbox.configure(state="disabled")
        return tile
