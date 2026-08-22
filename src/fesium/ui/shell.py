from collections.abc import Callable

import customtkinter as ctk

from fesium.ui.navigation import build_navigation_items
from fesium.ui.theme.styles import (
    apply_graphite_grid_theme,
    get_color_token,
    get_font_token,
)
from fesium.ui.theme.window_icon import apply_window_icon
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.button import Button

DEFAULT_WINDOW_GEOMETRY = "1400x960"
MIN_WINDOW_SIZE = (1100, 760)


class FesiumShell(ctk.CTk):
    """Primary desktop shell with a sidebar and content frame."""

    def __init__(self):
        apply_graphite_grid_theme()
        super().__init__()

        self.title("Fesium")
        self.geometry(DEFAULT_WINDOW_GEOMETRY)
        self.minsize(*MIN_WINDOW_SIZE)
        self.configure(fg_color=get_color_token("bg.app"))
        apply_window_icon(self)

        self._view_factories: dict[str, Callable[[ctk.CTkFrame], ctk.CTkBaseClass]] = {}
        self._view_instances: dict[str, ctk.CTkBaseClass] = {}
        self._navigation_buttons: dict[str, Button] = {}
        self.active_view_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=get_color_token("bg.sidebar"),
            border_width=0,
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=get_color_token("bg.app"),
            corner_radius=0,
            border_width=0,
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self._build_sidebar()

    def _build_sidebar(self) -> None:
        brand_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Fesium",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        brand_label.pack(anchor="w", padx=24, pady=(28, 6))

        # BodyText rather than a CTkLabel with wraplength=180. A pixel wrap
        # written into a view is only right for the string and the face it was
        # measured against: 180 was tuned to the old body font, and swapping
        # the face changed where the words break. BodyText takes the wrap from
        # the width the sidebar actually gives it.
        tagline_label = BodyText(
            self.sidebar_frame,
            "Local dev tools for students and developers",
            tone="text.secondary",
        )
        tagline_label.pack(anchor="w", padx=24, pady=(0, 20))

        for item in build_navigation_items():
            button = Button(
                self.sidebar_frame,
                item.label,
                variant="nav",
                icon=item.icon,
                anchor="w",
                width=192,
                command=lambda view_id=item.id: self.set_active_view(view_id),
            )
            # Full-width rows with a hairline gap: the sidebar is one surface
            # with the current row marked, not six separate boxes.
            button.pack(fill="x", padx=12, pady=2)
            self._navigation_buttons[item.id] = button

    def register_view(self, view_id: str, factory: Callable[[ctk.CTkFrame], ctk.CTkBaseClass]) -> None:
        self._view_factories[view_id] = factory

    def replace_view(self, view_id: str, factory: Callable[[ctk.CTkFrame], ctk.CTkBaseClass]) -> None:
        self._view_factories[view_id] = factory

        existing = self._view_instances.pop(view_id, None)
        was_active = self.active_view_id == view_id
        if existing is not None:
            existing.destroy()

        if was_active:
            self.active_view_id = None
            self.set_active_view(view_id)

    def set_active_view(self, view_id: str) -> None:
        if view_id == self.active_view_id:
            return

        current = self._view_instances.get(self.active_view_id)
        if current is not None:
            current.grid_remove()

        if view_id not in self._view_instances:
            factory = self._view_factories.get(view_id)
            if factory is None:
                raise KeyError(f"Unknown view id: {view_id}")
            self._view_instances[view_id] = factory(self.content_frame)

        next_view = self._view_instances[view_id]
        next_view.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self.active_view_id = view_id
        self._update_navigation_state()

    def _update_navigation_state(self) -> None:
        for view_id, button in self._navigation_buttons.items():
            button.set_active(view_id == self.active_view_id)
