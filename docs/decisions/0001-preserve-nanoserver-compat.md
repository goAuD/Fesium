# ADR 0001 — Preserve NanoServer Compatibility During Fesium Migration

- Status: Accepted
- Date: 2026-04-19
- Superseded by: —

## Context

Fesium is the rebrand of the original NanoServer project. Existing users have:

- a config file at `~/.nanoserver/config.json` with their last project path and port
- muscle memory for launching via `python nanoserver.py`
- bookmarks and links that point at `NanoServer`-branded assets and docs

A clean break would force every existing user to reconfigure and relearn on day one of the rebrand.

## Decision

During the v2.x line, Fesium preserves two explicit compatibility surfaces:

1. **Legacy config fallback.** If `~/.fesium/config.json` does not exist, the app reads `~/.nanoserver/config.json` once on startup and writes subsequent state to `~/.fesium/`. Implemented in `src/fesium/core/config.py` via `legacy_config_dir`.
2. **Legacy launcher shim.** `nanoserver.py` at repo root forwards into `fesium.app.main()`. Its only purpose is to keep `python nanoserver.py` working.

## Consequences

- New users should never see `.nanoserver/` created. The legacy directory is read-only from Fesium's perspective — we never write there.
- The shim and the legacy fallback will be removed in the next major release (v3.0.0). This ADR does not commit to a date, but the intent is to scope the compat window to the v2.x line.
- Until removal, tests must cover the legacy read-path so it does not silently break.
- Docs (README, CONTRIBUTING, release notes) mention `nanoserver.py` as a compatibility launcher, not as a recommended entry point.

## Removal Checklist (future v3.0.0)

- Delete `nanoserver.py` from repo root.
- Drop `legacy_config_dir` from `AppPaths` and `Config`.
- Remove the legacy-related branches in `tests/unit/core/test_config.py`.
- Update this ADR's status to Superseded and add a link to the v3.0.0 release note.
