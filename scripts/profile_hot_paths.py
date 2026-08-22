"""Measure the paths a Fesium user waits on.

    python scripts/profile_hot_paths.py

Two things are timed, because two things are felt: how long a click takes to
come back, and how long a cold start takes to show a window.

Kept in the repo because "it feels slow" is not a measurement, and the one real
bottleneck found here was invisible by eye - `php -v` costs about 78ms, and
every one of the eleven UI handlers that rebuild the views used to pay it. The
numbers printed are from whatever machine runs this; what matters is the shape,
and the before and after on your own.
"""

import cProfile
import io
import json
import pstats
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Taken before the app is imported, so a cold start includes those imports.
PROCESS_START = time.perf_counter()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fesium.app import bootstrap  # noqa: E402
from fesium.app.controller import FesiumController  # noqa: E402
from fesium.core.database import DatabaseManager  # noqa: E402
from fesium.core.environment import detect_php, reset_php_cache, summarize_php_environment  # noqa: E402
from fesium.core.paths import AppPaths  # noqa: E402
from fesium.ui.shell import FesiumShell  # noqa: E402

STARTUP_CHILD = "--startup-child"


def bench(label: str, call, repeats: int = 10) -> float:
    call()  # keep one-off warm-up cost out of the number
    start = time.perf_counter()
    for _ in range(repeats):
        call()
    each = (time.perf_counter() - start) / repeats
    print(f"  {label:<46}{each * 1000:8.2f} ms")
    return each


def seeded_project(table_count: int) -> Path:
    root = Path(tempfile.mkdtemp(prefix="fesium-profile-"))
    database = root / "database.sqlite"
    database.touch()
    manager = DatabaseManager(str(database), read_only=False)
    for index in range(table_count):
        manager.execute(f"CREATE TABLE t_{index} (id INTEGER PRIMARY KEY, a TEXT, b TEXT)")
    return root


def profile_actions() -> None:
    print("what a single UI action costs")
    print()
    reset_php_cache()

    bench("detect_php()  [uncached, spawns php]", detect_php, repeats=5)
    summarize_php_environment()
    bench("summarize_php_environment()  [cached]", summarize_php_environment, repeats=200)

    project = seeded_project(50)
    controller = FesiumController(config=None, cwd=project)
    controller.select_project(project)

    bench("controller.select_project()", lambda: controller.select_project(project))
    bench("controller._database_browser_snapshot()", controller._database_browser_snapshot, repeats=50)

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(20):
        controller.select_project(project)
    profiler.disable()

    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(30)
    print()
    print("  where that time goes:")
    shown = 0
    for line in stream.getvalue().splitlines():
        if "fesium" in line and shown < 6:
            print("   " + line.strip())
            shown += 1


def measure_startup() -> None:
    """Run one launch and report it. Meant to be run as a fresh process."""
    home = Path(tempfile.mkdtemp(prefix="fesium-start-"))
    (home / "workspace").mkdir()
    config_dir = home / ".fesium"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"last_project": str(home / "workspace"), "active_view": "overview"}),
        encoding="utf-8",
    )
    bootstrap.build_default_paths = lambda home_dir=None: AppPaths(home_dir=home)

    marks: dict[str, float] = {"start": PROCESS_START}
    real_mainloop = FesiumShell.mainloop

    def fake_mainloop(self):
        marks["built"] = time.perf_counter()
        for _ in range(3):
            self.update_idletasks()
            self.update()
        marks["painted"] = time.perf_counter()
        self.tk.call(self.protocol("WM_DELETE_WINDOW"))

    FesiumShell.mainloop = fake_mainloop
    try:
        bootstrap.main()
    except Exception as exc:  # pragma: no cover - depends on the machine
        print(f"  cannot open a window, skipping: {exc}")
        return
    finally:
        FesiumShell.mainloop = real_mainloop

    print(f"  {'launch -> window built':<46}{(marks['built'] - marks['start']) * 1000:8.2f} ms")
    print(f"  {'launch -> first paint':<46}{(marks['painted'] - marks['start']) * 1000:8.2f} ms")


def profile_startup() -> None:
    """Measure a cold start in a *fresh* process.

    Measuring it in this one would be wrong: by the time it ran, customtkinter
    and the whole app would already be imported, and those imports are about
    200ms of the very thing being measured. An in-process number reads roughly
    twice as fast as a real launch.
    """
    print()
    print()
    print("cold start  (fresh process, imports included)")
    print()
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), STARTUP_CHILD],
        capture_output=True,
        text=True,
    )
    for line in completed.stdout.splitlines():
        if line.strip():
            print(line)
    if completed.returncode != 0:
        tail = completed.stderr.strip().splitlines()[-1:] or ["unknown error"]
        print(f"  startup measurement failed: {tail[0]}")

    print()
    print("  Most of that is CustomTkinter and Tk themselves: importing")
    print("  customtkinter is ~146ms and creating the Tk root ~61ms. Fesium's")
    print("  own share is small, which is why nothing here chases it.")


if __name__ == "__main__":
    if STARTUP_CHILD in sys.argv:
        measure_startup()
    else:
        profile_actions()
        profile_startup()
