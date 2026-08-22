# Testing

Fesium uses `pytest`. The suite is pure-Python and runs without a display, without PHP, and without network access.

## Run the Full Suite

```bash
python -m pytest -v
```

## Run Only Unit Tests

```bash
python -m pytest tests/unit -v
```

## Layout

```text
tests/
└── unit/
    ├── app/     Mirrors src/fesium/app/
    ├── core/    Mirrors src/fesium/core/
    └── ui/      Mirrors src/fesium/ui/
```

When you change source code under `src/fesium/`, add or update the matching test under `tests/unit/` in the same-named subfolder.

## Testing Guidelines

- Prefer testing pure view-model functions (e.g. `build_server_view_model`, `build_database_summary`) over rendered widgets.
- Use `tmp_path` for any filesystem interaction; never touch `~/.fesium` from a test.
- Use `monkeypatch` to stub subprocess calls (`php -v`, server startup).
- Do not introduce tests that require a running PHP or network access.
- A test that needs a display is allowed only when it skips cleanly without one, and only when it is not the sole coverage for the behaviour. Ubuntu CI has no X server; Windows and macOS runners do. Share a single session-scoped Tk root - destroying one leaves the interpreter unable to create another, so per-test roots skip everything after the first for a reason unrelated to the display.
- A layout assertion should carry a control case that reproduces the defect in the same run. `tests/unit/ui/test_width_agnostic_label.py` asserts that a plain label collapses and the widget under test does not, so the test cannot quietly stop measuring anything.

## Layout checks

The suite is display-free, so it cannot see a layout bug. `scripts/check_layout.py` can: it drives the real views in a live window and asserts on measurements.

```bash
python scripts/check_layout.py
```

It measures three things, each of which has been a real defect here: every label has room for its text, no layout keeps resizing once the window stops, and tiles of equal span come out equal width. Run it before calling a UI change done, and prove any new assertion by reintroducing the defect and watching it fail - a check that has never failed has not been tested.

## Performance

`scripts/profile_hot_paths.py` times what a user waits on: one UI action, and a cold start.

```bash
python scripts/profile_hot_paths.py
```

Profile before optimising anything. The only real bottleneck found so far was invisible by eye - `php -v` costs about 78ms and every one of the eleven handlers that rebuild the views used to spawn it, so each click stalled the window. Two things that measurement got wrong first, and are now built into the script:

- The cold start is measured in a **fresh process**. Measuring it in the profiler's own process reads about twice as fast, because customtkinter and the app are already imported.
- Measure the path the app actually takes. An early benchmark looped `get_table_info` over every table and made the database browser look expensive; the app only ever asks for the selected one.

## Security scanning

Semgrep runs twice, and the difference matters:

- **On every pull request** as a diff scan, via the Semgrep Cloud Platform integration. It reports what the change introduces.
- **On every push to `main`, and weekly**, as a full scan via `.github/workflows/semgrep.yml`. This is the one that *closes* findings.

A diff scan cannot resolve anything on the default branch. Without the full scan, a finding stays Open after the code causing it is fixed and merged - five of them sat open for ten days that way. The full scan needs a `SEMGREP_APP_TOKEN` repository secret to upload results; without it the job still scans and fails on findings, it just cannot update the dashboard.

Locally:

```bash
semgrep --config p/default --config p/python --config p/security-audit --config p/github-actions .
```

## CI

Tests run on every push and pull request via [.github/workflows/python-tests.yml](../../.github/workflows/python-tests.yml).
