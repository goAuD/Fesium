import customtkinter as ctk

from fesium.core.preferences import MAX_PORT, MIN_PORT, describe_startup_project
from fesium.ui.theme.styles import get_button_style, get_color_token, get_font_token
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody

NO_DEFAULT_PROJECT = "Not set - Fesium opens the folder it was started from"


def build_settings_model(config_data: dict) -> dict:
    """Turn stored config into everything the Settings screen needs to render."""
    default_project = str(config_data.get("default_project", "") or "")
    last_project = str(config_data.get("last_project", "") or "")
    restore_last_project = bool(config_data.get("restore_last_project", True))

    return {
        "port": str(config_data.get("port", 8000)),
        "port_hint": f"Used the next time you start a local server. Allowed range {MIN_PORT}-{MAX_PORT}.",
        "default_project": default_project or NO_DEFAULT_PROJECT,
        "has_default_project": bool(default_project),
        "restore_last_project": restore_last_project,
        "startup_summary": describe_startup_project(
            last_project=last_project,
            default_project=default_project,
            restore_last_project=restore_last_project,
        ),
    }


class SettingsView(ctk.CTkFrame):
    """Application preferences: startup project and default server port."""

    def __init__(
        self,
        master,
        config_data: dict,
        *,
        on_apply_port=None,
        on_select_default_project=None,
        on_clear_default_project=None,
        on_toggle_restore_last_project=None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._config_data = dict(config_data)
        self._model = build_settings_model(self._config_data)
        self._on_apply_port = on_apply_port
        self._on_select_default_project = on_select_default_project
        self._on_clear_default_project = on_clear_default_project
        self._on_toggle_restore_last_project = on_toggle_restore_last_project

        title = ctk.CTkLabel(
            self,
            text="Settings",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Preferences stored in your local Fesium config",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 20))

        body = ScrollableViewBody(self)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        self._build_startup_panel(body)
        self._build_server_panel(body)

        self.feedback_label = BodyText(body, "", tone="text.secondary")
        self.feedback_label.grid(row=2, column=0, sticky="ew", pady=(16, 0))

    def _build_startup_panel(self, body) -> None:
        panel = PanelCard(body, surface_variant="inset")
        panel.grid(row=0, column=0, sticky="ew")
        content = panel.content_frame
        content.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            content,
            text="Startup",
            text_color=get_color_token("accent.primary"),
            font=get_font_token("section_heading"),
        )
        heading.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 12))

        self.restore_switch = ctk.CTkSwitch(
            content,
            text="Reopen my last project",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
            progress_color=get_color_token("accent.primary"),
            button_color=get_color_token("text.primary"),
            button_hover_color=get_color_token("text.secondary"),
            command=self._handle_toggle_restore,
        )
        if self._model["restore_last_project"]:
            self.restore_switch.select()
        else:
            self.restore_switch.deselect()
        self.restore_switch.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        hint = BodyText(
            content,
            "When off, Fesium starts from the default project folder below.",
            tone="text.secondary",
        )
        hint.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))

        folder_label = ctk.CTkLabel(
            content,
            text="Default project folder",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
        )
        folder_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        self.default_project_label = BodyText(
            content,
            self._model["default_project"],
            tone="text.secondary",
        )
        self.default_project_label.grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12)
        )

        select_button = ctk.CTkButton(
            content,
            text="Choose Folder",
            **get_button_style("secondary"),
            command=self._handle_select_default_project,
        )
        select_button.grid(row=5, column=0, sticky="ew", padx=(16, 8), pady=(0, 16))

        self.clear_button = ctk.CTkButton(
            content,
            text="Clear",
            state="normal" if self._model["has_default_project"] else "disabled",
            **get_button_style("secondary"),
            command=self._handle_clear_default_project,
        )
        self.clear_button.grid(row=5, column=1, sticky="ew", padx=(8, 16), pady=(0, 16))

        self.startup_summary_label = BodyText(
            content,
            self._model["startup_summary"],
            tone="text.primary",
        )
        self.startup_summary_label.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16)
        )

    def _build_server_panel(self, body) -> None:
        panel = PanelCard(body, surface_variant="inset")
        panel.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        content = panel.content_frame
        content.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            content,
            text="Local Server",
            text_color=get_color_token("accent.primary"),
            font=get_font_token("section_heading"),
        )
        heading.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 12))

        port_label = ctk.CTkLabel(
            content,
            text="Default port",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
        )
        port_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        self.port_entry = ctk.CTkEntry(
            content,
            fg_color=get_color_token("bg.app"),
            text_color=get_color_token("text.primary"),
            border_color=get_color_token("border.default"),
            font=get_font_token("mono"),
            height=38,
        )
        self.port_entry.insert(0, self._model["port"])
        self.port_entry.grid(row=2, column=0, sticky="ew", padx=(16, 8), pady=(0, 12))
        self.port_entry.bind("<Return>", lambda _event: self._handle_apply_port())

        apply_button = ctk.CTkButton(
            content,
            text="Apply",
            **get_button_style("primary"),
            command=self._handle_apply_port,
        )
        apply_button.grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(0, 12))

        hint = BodyText(content, self._model["port_hint"], tone="text.secondary")
        hint.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))

    def _show(self, result) -> None:
        """Render a PreferenceResult, or clear the line when there is nothing to say."""
        if result is None:
            return

        tone = "text.secondary" if result.ok else "accent.danger"
        self.feedback_label.configure(
            text=result.message,
            text_color=get_color_token(tone),
        )

    def _apply(self, result, key: str) -> None:
        """Show the outcome, then re-render whatever the change affects.

        Config stays the single source of truth - bootstrap has already
        written to it. This only keeps the on-screen copy in step, so the
        startup summary is never one click out of date.
        """
        self._show(result)
        if result is None or not result.ok:
            return

        self._config_data[key] = result.value
        self._model = build_settings_model(self._config_data)
        self.default_project_label.configure(text=self._model["default_project"])
        self.startup_summary_label.configure(text=self._model["startup_summary"])
        self.clear_button.configure(
            state="normal" if self._model["has_default_project"] else "disabled"
        )

    def _handle_apply_port(self) -> None:
        if self._on_apply_port is None:
            return
        self._apply(self._on_apply_port(self.port_entry.get()), "port")

    def _handle_toggle_restore(self) -> None:
        if self._on_toggle_restore_last_project is None:
            return
        result = self._on_toggle_restore_last_project(bool(self.restore_switch.get()))
        self._apply(result, "restore_last_project")

    def _handle_select_default_project(self) -> None:
        if self._on_select_default_project is None:
            return
        self._apply(self._on_select_default_project(), "default_project")

    def _handle_clear_default_project(self) -> None:
        if self._on_clear_default_project is None:
            return
        self._apply(self._on_clear_default_project(), "default_project")
