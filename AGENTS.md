# Fesium Agent Guide

## Product Direction

`Fesium` is an offline-first local dev toolbox for students and developers. The current repository contains the first desktop app in that toolbox and is mid-migration from the legacy `NanoServer` structure.

## Architecture Guardrails

- Keep runtime code under `src/fesium/`.
- Put reusable backend logic in `src/fesium/core/`.
- Put UI shell, views, widgets, and theme code in `src/fesium/ui/`.
- Put bundled offline assets in `src/fesium/assets/`.
- Keep root launchers thin. `fesium.py` is the primary launcher, and `nanoserver.py` remains a temporary compatibility shim.
- Do not introduce new god files. Prefer small focused modules over expanding `app.py` into a second monolith.

## Design Guardrails

- Follow the approved `Graphite Grid` direction: dark graphite shell, restrained cyan-based accent system, and refined panel hierarchy.
- Bundle fonts in-repo only. Do not load fonts or other runtime assets from the network.
- Preserve the offline-first posture. The app must remain useful without internet access.

## Security Guardrails

- Keep SQLite read-only mode enabled by default.
- Treat destructive database actions as explicit confirmation flows.
- Keep local server behavior `localhost`-first.
- Validate project paths and document roots before server startup.
- Avoid unnecessary logging of sensitive local filesystem details.

## Repo Hygiene

- Keep new code, tests, and assets in the directories that match their responsibilities.
- Update or add tests whenever behavior changes.
- Do not revert unrelated user changes.
- Keep documentation aligned with the current migration state instead of pretending unfinished work is complete.

## Documentation Policy

- Update `README.md` and `CHANGELOG.md` when user-facing behavior changes.
- Record major planning or design shifts under `docs/plans/` or `docs/superpowers/specs/`.
- When architectural decisions become durable and reusable, add a decision record under `docs/decisions/`.

