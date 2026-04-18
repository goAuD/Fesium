# Contributing to Fesium

## Scope

`Fesium` is being rebuilt from the original `NanoServer` codebase into a modular offline-first desktop app. Contributions should preserve that direction: small focused modules, local-first behavior, and security-conscious defaults.

## Local Setup

Requirements:

- Python 3.8+
- PHP on `PATH` if you want to manually test the local server flow

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Running the App

Primary launcher:

```bash
python fesium.py
```

Temporary compatibility launcher:

```bash
python nanoserver.py
```

## Running Tests

Run the full unit suite:

```bash
python -m pytest tests/unit -v
```

Run the complete test suite:

```bash
python -m pytest -v
```

## Code Organization

Place new code in the module that matches its responsibility:

- `src/fesium/core/` for server, database, config, environment, path, detection, and security logic
- `src/fesium/ui/` for navigation, shell, views, widgets, and theme code
- `src/fesium/assets/` for bundled offline assets such as fonts
- `tests/unit/` for unit coverage that mirrors the source layout

Avoid adding new flat root-level runtime modules. The repo is moving toward the `src/` package layout and away from the old monolithic entrypoint pattern.

## Design and Security Expectations

- Keep the `Graphite Grid` design direction consistent.
- Keep bundled fonts local to the repository.
- Preserve offline-first behavior.
- Keep SQLite read-only by default unless a task explicitly requires a write path.
- Treat destructive actions as opt-in and clearly signaled.

## Documentation

If your change affects behavior, update the relevant docs:

- `README.md` for user-facing workflow changes
- `CHANGELOG.md` for release-facing notes
- `docs/plans/` or `docs/superpowers/specs/` for larger scoped work

