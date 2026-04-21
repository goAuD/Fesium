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
- Do not introduce tests that require a display server, a running PHP, or network access — the GitHub Actions workflow runs headless.

## CI

Tests run on every push and pull request via [.github/workflows/python-tests.yml](../../.github/workflows/python-tests.yml).
