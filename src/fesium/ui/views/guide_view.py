import customtkinter as ctk

from fesium.ui.widgets.bento import BentoGrid
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.tile import Tile
from fesium.ui.widgets.view_header import HEADER_GAP, ViewHeader


def build_guide_sections() -> tuple[dict[str, str], ...]:
    return (
        {
            "title": "What Fesium Is For",
            "body": (
                "Fesium is an offline-first local dev toolbox for students and developers. "
                "It helps you run local projects, inspect SQLite files, and keep common "
                "classroom or laptop workflows simple."
            ),
        },
        {
            "title": "Best-Fit Projects",
            "body": (
                "Use it for plain HTML, CSS, and JavaScript sites, PHP projects that need localhost serving, "
                "and SQLite-backed apps where you want quick inspection without opening "
                "a heavier database tool."
            ),
        },
        {
            "title": "Recommended Workflow",
            "body": (
                "Start in Server, select your project, let Fesium detect the document "
                "root, then launch the site locally. "
                "Use Database when the project has SQLite data or when you want to inspect a standalone .sqlite file."
            ),
        },
        {
            "title": "Static Hosting Matters",
            "body": (
                "Static site hosting is a valid first-class workflow here, not just a fallback. "
                "If your project is just frontend files, Fesium should still feel like "
                "the right tool to open, serve, and test it."
            ),
        },
        {
            "title": "Safety Defaults",
            "body": (
                "SQLite starts in read-only mode, destructive queries ask for "
                "confirmation, and local serving stays localhost-first. "
                "Those defaults are meant to keep experimentation fast without making the app careless."
            ),
        },
    )


# The opening section is the thesis, so it runs full width; the four that
# follow are peers and pair off.
GUIDE_LAYOUT = (
    {"row": 0, "column": 0, "span": 12, "row_weight": 2},
    {"row": 1, "column": 0, "span": 6, "row_weight": 3},
    {"row": 1, "column": 6, "span": 6, "row_weight": 3},
    {"row": 2, "column": 0, "span": 6, "row_weight": 3},
    {"row": 2, "column": 6, "span": 6, "row_weight": 3},
)


class GuideView(ctk.CTkFrame):
    """Student-facing introduction and usage guidance for Fesium."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ViewHeader(self, "Guide", "How Fesium fits student-friendly local development")
        header.grid(row=0, column=0, sticky="ew", pady=(0, HEADER_GAP))

        grid = BentoGrid(self)
        grid.grid(row=1, column=0, sticky="nsew")

        for section, placement in zip(build_guide_sections(), GUIDE_LAYOUT, strict=True):
            tile = Tile(grid, section["title"])
            body = BodyText(tile.body, section["body"])
            body.grid(row=0, column=0, sticky="new")
            grid.place_tile(tile, **placement)
