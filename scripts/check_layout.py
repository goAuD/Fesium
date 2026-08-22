"""Drive the real views in a live Tk window and assert on measurements.

The pytest suite is display-free by design, so it cannot see a layout bug. This
is the check that can. Run it on any machine with a display, and before
claiming a UI change is done:

    python scripts/check_layout.py

Three things are measured, each of which has been a real defect:

* **Legibility** - every label must have room for its text. Measured on the
  *inner* tkinter.Label against the font, never `winfo_reqwidth`: a label whose
  width option is set in characters reports that width and clips, so a
  collapsed label measures as perfectly sized. A wrapped label is held to a
  different rule, because Tk breaks even an unbreakable word at a character
  boundary: it must not have collapsed, and it must not wrap wider than the box
  it was given.
* **Settling** - with the window size held still, nothing may keep resizing. A
  label that demands its own wraplength fights the grid, and the tug of war is
  visible as a panel that shimmers.
* **Balance** - tiles given the same span must come out the same width, or
  something inside one of them is dictating its container's size.
"""

import sys
import tkinter
from collections import Counter
from pathlib import Path
from tkinter import font as tkfont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import customtkinter as ctk  # noqa: E402

from fesium.core.environment import EnvironmentStatus  # noqa: E402
from fesium.core.project_database import DatabaseReadiness, DatabaseRequirement  # noqa: E402
from fesium.ui.shell import FesiumShell  # noqa: E402
from fesium.ui.views.database_view import DatabaseView  # noqa: E402
from fesium.ui.views.environment_view import EnvironmentView  # noqa: E402
from fesium.ui.views.guide_view import GuideView  # noqa: E402
from fesium.ui.views.overview_view import OverviewView  # noqa: E402
from fesium.ui.views.server_view import ServerView  # noqa: E402
from fesium.ui.views.settings_view import SettingsView  # noqa: E402
from fesium.ui.widgets.bento import BentoGrid  # noqa: E402
from fesium.ui.widgets.tile import Tile  # noqa: E402
from fesium.ui.widgets.width_agnostic_label import describe_font  # noqa: E402

VIEW_IDS = ("overview", "server", "database", "environment", "guide", "settings")
WIDTHS = range(1100, 1461, 40)
GEOMETRIES = ("1100x760", "1400x960")

# Long, awkward content on purpose: a deep Windows path and a full PHP banner
# are what exposed the squeezes.
PHP = "PHP 8.5.2 (cli) (built: Jan 13 2026 21:54:57) (ZTS Visual C++ 2022 x64)"
PROJECT = Path("D:/GitHub/streamapp-with-a-long-name")
LOGS = tuple(f"[127.0.0.1:5142{index}] GET /css/app.css - Accepted" for index in range(6))
READINESS = DatabaseReadiness(
    requirement=DatabaseRequirement(connection="mysql", host="127.0.0.1", port=3306, database="streamapp"),
    reachable=False,
)

# Below this a label is not narrow, it is gone. One character renders about 8px.
COLLAPSED_WIDTH = 40

failures: list[str] = []


def report(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'OK ' if ok else 'BAD'} {label}{('  ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def walk(widget):
    yield widget
    for child in widget.winfo_children():
        yield from walk(child)


def build_shell() -> FesiumShell:
    status = EnvironmentStatus(True, PHP, PHP)
    shell = FesiumShell()
    shell.register_view("overview", lambda p: OverviewView(
        p, project_root=PROJECT, project_kind="laravel", php_summary=PHP,
        server_status="running", local_url="http://localhost:8000", log_lines=LOGS))
    shell.register_view("server", lambda p: ServerView(
        p, document_root=PROJECT / "public", port=8000, project_root=PROJECT, project_kind="laravel",
        backend_kind="php", server_status="running", local_url="http://localhost:8000",
        last_error="", log_lines=LOGS))
    shell.register_view("database", lambda p: DatabaseView(
        p, db_path=str(PROJECT / "database" / "database.sqlite"), read_only=True, source="project",
        project_database_available=True, tables=("migrations", "users"), selected_table="users",
        selected_table_info=({"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},)))
    shell.register_view("environment", lambda p: EnvironmentView(
        p, status=status, project_root=PROJECT, project_kind="laravel",
        document_root=PROJECT / "public", database_readiness=READINESS))
    shell.register_view("guide", lambda p: GuideView(p))
    shell.register_view("settings", lambda p: SettingsView(
        p, config_data={"port": 8000, "last_project": str(PROJECT)}))
    return shell


def settle(shell, rounds: int = 8) -> None:
    for _ in range(rounds):
        shell.update_idletasks()
        shell.update()


def text_width(label, text: str) -> int:
    family, size, weight = describe_font(label.cget("font"))
    scaling = ctk.ScalingTracker.get_widget_scaling(label)
    # Tk reads a positive font size as points and a negative one as pixels, and
    # CustomTkinter renders the negative form.
    rendered = -abs(round(size * scaling))
    measure = tkfont.Font(family=family, size=rendered, weight=weight).measure
    return max((measure(line) for line in text.splitlines() or [""]), default=0)


def check_legibility(shell) -> None:
    illegible = []
    checked = 0
    for view_id in VIEW_IDS:
        shell.set_active_view(view_id)
        for geometry in GEOMETRIES:
            shell.geometry(f"{geometry}+40+40")
            settle(shell)
            for label in (w for w in walk(shell) if isinstance(w, ctk.CTkLabel)):
                text = label.cget("text")
                if not text:
                    continue
                checked += 1
                given = label._label.winfo_width()
                wraplength = label.cget("wraplength")
                if wraplength:
                    # A wrapped label breaks anything, including a word longer
                    # than the line - Tk splits it at a character boundary. So
                    # the failures worth catching are the two real ones: the
                    # label collapsed to nothing, or it is wrapping wider than
                    # the box it was given and spilling outside its panel.
                    if given < COLLAPSED_WIDTH:
                        illegible.append(f"{view_id} {geometry} collapsed to {given}px: {text[:34]!r}")
                    elif wraplength > given + 2:
                        illegible.append(f"{view_id} {geometry} wraps at {wraplength} in {given}px: "
                                         f"{text[:34]!r}")
                    continue

                needed = text_width(label, text)
                if needed > given + 2:
                    illegible.append(f"{view_id} {geometry} {text[:34]!r} given={given} needs={needed}")

    report(f"every label has room for its text ({checked} labels)", not illegible)
    for line in illegible[:12]:
        print(f"      {line}")


def check_settling(shell) -> None:
    noisy = []
    for view_id in VIEW_IDS:
        shell.set_active_view(view_id)
        settle(shell)
        view = shell._view_instances[view_id]
        labels = [w for w in walk(view) if isinstance(w, ctk.CTkLabel)]
        events = Counter()
        for index, widget in enumerate(labels):
            tkinter.Frame.bind(
                widget,
                "<Configure>",
                lambda _e, i=index, counter=events: counter.update([i]),
                add="+",
            )

        for width in WIDTHS:
            shell.geometry(f"{width}x804+40+40")
            settle(shell)
            events.clear()
            # The window is not changing size now, so a settled layout is silent.
            settle(shell, rounds=30)
            if any(count > 2 for count in events.values()):
                worst = max(events, key=lambda i: events[i])
                noisy.append(f"{view_id} at {width}px: {events[worst]} events on "
                             f"{labels[worst].cget('text')[:34]!r}")

    report(f"layouts settle ({len(VIEW_IDS)} views x {len(WIDTHS)} widths)", not noisy)
    for line in noisy[:12]:
        print(f"      {line}")


def check_tile_balance(shell) -> None:
    unbalanced = []
    for view_id in VIEW_IDS:
        shell.set_active_view(view_id)
        for geometry in GEOMETRIES:
            shell.geometry(f"{geometry}+40+40")
            settle(shell)
            view = shell._view_instances[view_id]
            grids = [w for w in walk(view) if isinstance(w, BentoGrid)]
            for grid in grids:
                by_span: dict[tuple[int, int], list] = {}
                for tile in (w for w in walk(grid) if isinstance(w, Tile)):
                    info = tile.grid_info()
                    if info.get("in") is not grid:
                        continue
                    key = (int(info["row"]), int(info["columnspan"]))
                    by_span.setdefault(key, []).append(tile)
                for (row, span), tiles in by_span.items():
                    if len(tiles) < 2:
                        continue
                    widths = [tile.winfo_width() for tile in tiles]
                    if max(widths) - min(widths) > 4:
                        unbalanced.append(f"{view_id} {geometry} row {row} span {span}: {widths}")

    report("tiles of equal span are equal width", not unbalanced)
    for line in unbalanced[:12]:
        print(f"      {line}")


def main() -> int:
    try:
        shell = build_shell()
    except Exception as exc:  # pragma: no cover - depends on the machine
        print(f"cannot open a window, skipping layout checks: {exc}")
        return 0

    try:
        check_legibility(shell)
        check_settling(shell)
        check_tile_balance(shell)
    finally:
        shell.destroy()

    print("\nRESULT:", "layout holds" if not failures else f"{len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
