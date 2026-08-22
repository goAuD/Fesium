# Repository Conventions

## Code Organization

- `src/fesium/core/` - server, database, config, environment, path, detection, preference, and security logic (framework-free)
- `src/fesium/app/` - application bootstrap and controller
- `src/fesium/ui/` - navigation, shell, views, widgets, and theme
- `src/fesium/assets/` - bundled offline assets (fonts, icons)
- `tests/unit/` - unit coverage that mirrors the source layout

### Guardrails

- No new flat root-level runtime modules. Everything runtime-facing lives under `src/fesium/`.
- Keep `app.py`-style god files out. Prefer small focused modules.
- `core/` never imports from `ui/`.
- Root launchers (`fesium.py`, `nanoserver.py`) stay thin - they only start the app.

## Design

- Follow the approved **Graphite Grid** direction: dark graphite shell, restrained matte accent, and clear panel hierarchy.
- **Type is decided on whether a beginner can read it without getting it wrong**, not on how it feels. `Atkinson Hyperlegible` sets everything the app writes and `JetBrains Mono` sets code; one family plus a mono, because size and weight already carry the hierarchy in a bento layout. Judge a candidate on its *worst* confusable pair, never the average - a reader is tripped by the one pair a face gets wrong. `src/fesium/assets/fonts/README.md` carries the measurements.
- Prefer muted/matte accents over bright neon for dev-tool UIs.
- Buttons must use the right variant: `primary` for the main call-to-action, `secondary` for supporting actions, `danger` for destructive ones. Never use the same variant for every control in a view.
- Icons come from the bundled Lucide set. Add an SVG under `src/fesium/assets/icons/lucide/`, run `python scripts/build_icons.py`, and reference it by name. Never fetch or rasterise at runtime.
- Corner geometry lives in `SHAPE_TOKENS`. Never pair a corner radius with a border on the same widget: CustomTkinter draws the arc and the straight edges as separate canvas items and they do not meet, so the corner renders doubled. A test enforces it.
- Views are laid out as a bento grid: `BentoGrid` from `ui/widgets/` plus `Tile` for each cell. Size carries the hierarchy - a tile that matters spans more columns or takes more row weight - so headings can stay quiet.
- Paragraphs, meta-list labels and tile titles use `WidthAgnosticLabel`, which stops a label dictating its container's width without letting it collapse. It adds the horizontal stretch to whatever `grid`/`pack` it is given, so the two halves cannot come apart - but it still needs a cell with weight to stretch into.
- Never let a label ask for width. A wrapped label requests its `wraplength` as its width, which stretches its tile, breaks the grid's uniform columns and makes panels shimmer. Paragraphs go through `BodyText`, and a tile's `meta` is for a short qualifier - a count, a unit, a status word - not a sentence.
- Never give a widget inside a tile a fixed pixel height. `CTkTextbox` asks for 200px by default; stack three and grid stops honouring row weights, and the tiles clip instead of sharing the space.
- Every button is `Button` from `ui/widgets/`. A raw `CTkButton` misses the disabled styling, and CustomTkinter only swaps the text colour on a disabled button, which leaves it unreadable.
- Reserve `accent.primary` for state that matters: the active nav item, the primary action, live status. It used to sit on every section heading, which meant it signalled nothing.
- Paragraph text uses `BodyText` from `ui/widgets/`. Never hardcode `wraplength` in a view: a constant pixel wrap is only correct for the one window size, string and typeface it was measured against, and it clips at every smaller one. The sidebar tagline carried `wraplength=180` tuned to the old body font, and changing the face was enough to break it. Grid paragraphs with `sticky="ew"`, or pack them, so the container drives the width.
- Badges must be visually subordinate to the buttons they sit next to - equal or smaller in height, with balanced horizontal padding.
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
