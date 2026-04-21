# Repository Conventions

## Code Organization

- `src/fesium/core/` — server, database, config, environment, path, detection, and security logic (framework-free)
- `src/fesium/app/` — application bootstrap and controller
- `src/fesium/ui/` — navigation, shell, views, widgets, and theme
- `src/fesium/assets/` — bundled offline assets (fonts, icons)
- `tests/unit/` — unit coverage that mirrors the source layout

### Guardrails

- No new flat root-level runtime modules. Everything runtime-facing lives under `src/fesium/`.
- Keep `app.py`-style god files out. Prefer small focused modules.
- `core/` never imports from `ui/`.
- Root launchers (`fesium.py`, `nanoserver.py`) stay thin — they only start the app.

## Design

- Follow the approved **Graphite Grid** direction: dark graphite shell, restrained matte accent, and clear panel hierarchy.
- Prefer muted/matte accents over bright neon for dev-tool UIs.
- Buttons must use the right variant: `primary` for the main call-to-action, `secondary` for supporting actions, `danger` for destructive ones. Never use the same variant for every control in a view.
- Badges must be visually subordinate to the buttons they sit next to — equal or smaller in height, with balanced horizontal padding.
- Bundle fonts in-repo only. Do not load fonts or other runtime assets from the network.
- Preserve offline-first behavior. The app must remain useful without internet access.

## Security

- SQLite read-only mode stays enabled by default, resets on every launch.
- Destructive database actions require explicit confirmation.
- Local server behavior is `localhost`-first.
- Validate project paths and document roots before server startup.
- Do not log sensitive local filesystem details unnecessarily.

## Documentation

- Update [`README.md`](../../README.md) and [`CHANGELOG.md`](../../CHANGELOG.md) when user-facing behavior changes.
- Add an entry under [`docs/release/`](../release/) when tagging a new version.
- Record major planning or design shifts under [`docs/plans/`](../plans/) and [`docs/specs/`](../specs/) with a dated filename.
- When an architectural decision becomes durable and reusable, add an ADR under [`docs/decisions/`](../decisions/).
- Keep docs honest. Do not describe unfinished work as shipped.
