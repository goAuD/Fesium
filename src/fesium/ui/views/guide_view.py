import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody


def build_guide_sections() -> tuple[dict[str, str], ...]:
    return (
        {
            "title": "What Fesium Is For",
            "body": (
                "Fesium is an offline-first local dev toolbox for students and developers. "
                "It helps you run local projects, inspect SQLite files, and keep common classroom or laptop workflows simple."
            ),
        },
        {
            "title": "Best-Fit Projects",
            "body": (
                "Use it for plain HTML, CSS, and JavaScript sites, PHP projects that need localhost serving, "
                "and SQLite-backed apps where you want quick inspection without opening a heavier database tool."
            ),
        },
        {
            "title": "Recommended Workflow",
            "body": (
                "Start in Server, select your project, let Fesium detect the document root, then launch the site locally. "
                "Use Database when the project has SQLite data or when you want to inspect a standalone .sqlite file."
            ),
        },
        {
            "title": "Static Hosting Matters",
            "body": (
                "Static site hosting is a valid first-class workflow here, not just a fallback. "
                "If your project is just frontend files, Fesium should still feel like the right tool to open, serve, and test it."
            ),
        },
        {
            "title": "Safety Defaults",
            "body": (
                "SQLite starts in read-only mode, destructive queries ask for confirmation, and local serving stays localhost-first. "
                "Those defaults are meant to keep experimentation fast without making the app careless."
            ),
        },
    )


class GuideView(ctk.CTkFrame):
    """Student-facing introduction and usage guidance for Fesium."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Guide",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="How Fesium fits student-friendly local development",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 20))

        body = ScrollableViewBody(self)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        for index, section in enumerate(build_guide_sections()):
            panel = PanelCard(body, surface_variant="inset")
            panel.grid(row=index, column=0, sticky="ew", pady=(0, 16) if index < 4 else 0)
            panel_content = panel.content_frame
            panel_content.grid_columnconfigure(0, weight=1)

            panel_title = ctk.CTkLabel(
                panel_content,
                text=section["title"],
                text_color=get_color_token("accent.primary"),
                font=get_font_token("section_heading"),
            )
            panel_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

            panel_body = ctk.CTkLabel(
                panel_content,
                text=section["body"],
                text_color=get_color_token("text.primary"),
                font=get_font_token("body"),
                justify="left",
                wraplength=900,
            )
            panel_body.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))
