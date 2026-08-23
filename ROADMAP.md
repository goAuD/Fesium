# Fesium Roadmap

Planned direction for `Fesium` after the v2.0.0 rebrand. Items here are intent, not a commitment - priorities shift as the app is used in classroom and dev environments.

Current released line: **v2.2.x** (see [docs/release/v2.2.0.md](docs/release/v2.2.0.md)).

## v2.1.0 - Shipped 2026-08-22

Focus: UI polish and quality-of-life on top of the new shell.

Everything here shipped in `v2.1.0`. See [docs/release/v2.1.0.md](docs/release/v2.1.0.md).

### UI / UX

- [x] Real `secondary` and `danger` button variants so destructive controls (Stop, Reset, destructive SQL) look distinct from primary actions
- [x] Matte accent palette pass - soften the default accent so the UI reads calm in long sessions
- [x] Badge sizing and text centering pass - badges subordinate to buttons
- [x] `Read-only` switch sub-label clarifying session-scoped behavior
- [x] Settings view wired to real preferences (port, default project folder, restore-last-project toggle)

### Reliability

- [x] Unified `detect_php()` with a subprocess timeout to prevent UI hangs
- [x] Consistent destructive-query detection (comments and `WITH ... UPDATE` CTEs)
- [x] Hide SQLite internal tables (`sqlite_*`) from the schema browser

### Tests / CI

- [x] Cross-platform GitHub Actions matrix (Ubuntu + Windows + macOS, Python 3.10-3.12)
- [x] Coverage for subprocess timeouts and comment-stripping in SQL risk classification
- [x] Actions pinned to commit SHAs, and the declared minimum Python is a tested claim
- [x] Ruff lint with its own CI job

### Design rework

Not planned when this section was written, but it is what the release turned out to be about.

- [x] Bento grid layout across all six views, replacing stacked equal-weight panels
- [x] `BentoGrid`, `Tile`, `ViewHeader`, `MetaList` and `Button` as shared primitives
- [x] Square structural corners, because CustomTkinter cannot render a radius and a border cleanly together
- [x] Bundled Lucide icons, tinted at runtime from theme colours
- [x] A contrast floor held by tests: every button and text-on-surface pairing clears WCAG AA

### Release and presentation

None of this changes how the app runs. It is what turns a working app into something someone else can look at.

- [x] Tag `v2.1.0`: move the `Unreleased` block in [CHANGELOG.md](CHANGELOG.md) under the version, and add `docs/release/v2.1.0.md` beside the v2.0.0 note
- [x] Full documentation pass - read `README.md`, `docs/` and the release notes against the app as it behaves now, not as it did before the bento rework. The repo has drifted before by shipping work the changelog denied.

## v2.2.0 - Shipped 2026-08-23

The hardening-and-handoff release: what two days of review found, closed, and wrote down. Full list in [CHANGELOG.md](CHANGELOG.md); narrative in [docs/release/v2.2.0.md](docs/release/v2.2.0.md).

- [x] Server hardening from an independent security review: dot-paths refused on both backends (including double-encoded forms), requests must resolve inside the document root, Host header must name this server, address fixed to `127.0.0.1`. Findings in [docs/reviews/ox-alpha-review-2026-08-23.md](docs/reviews/ox-alpha-review-2026-08-23.md).
- [x] A `Setup Report` in `Diagnostics`: one button that copies everything as pasteable text, home folders shortened to `~`, no credential can appear in it.
- [x] ADR 0002 recorded: MySQL will be reached through our own `Database` view over PyMySQL, not a bundled admin panel.
- [x] GitHub Pages portfolio page - its own layout in the Fesium brand colours, carrying the screenshots and what the app is for. Built by [scripts/build_site.py](scripts/build_site.py) from the app's own `COLOR_TOKENS`, so it cannot drift from the product it describes.

## Next up - MySQL Support

The agreed next task. Fesium detects that a project wants MySQL and reports whether it is reachable. What it does not do is run one - and it is worth being clear that these are different jobs. Bundling a database server is what Laragon did; matching that is a much larger commitment than a connection option.

How it is reached is settled in [docs/decisions/0002-mysql-through-our-own-view.md](docs/decisions/0002-mysql-through-our-own-view.md): through the `Database` view we already have, over `PyMySQL`, rather than by bundling or rebuilding an admin panel. That keeps read-only-by-default applying to MySQL exactly as it does to SQLite, which serving a panel in a browser would not.

Order of work, per the [handoff audit](docs/specs/2026-08-23-handoff-audit-and-continuation-plan.md):

- [ ] An engine seam in `core/database.py` - connect, list tables, describe columns, error type, file-vs-server connection model - as its own refactor with no behavior change, proven by the existing suite
- [ ] The PyMySQL engine behind that seam: `%s` placeholders, identifier quoting, and read/write classification that knows MySQL verbs (`SHOW`, `DESCRIBE` read; `REPLACE`, `CALL`, `GRANT`, `CREATE`, `RENAME`, `LOAD DATA` write)
- [ ] Connection UI in the `Database` view: host, port, database and user, with the password asked per session and never written to disk
- [ ] `Diagnostics` pre-fills from the project's `.env`, credentials excluded
- [ ] Deliberately not included: dump import/export, form-based row editing, user and privilege management

## Open, not scheduled

Carried between working sessions so they are not rediscovered.

- [ ] **A macOS CI job stalls at random.** Four times now, always `macos-latest`, moving between Python versions, always inside `Run tests`. The address fix removed one cause and the Ubuntu race removed another. The fourth stall left evidence: the last passing test was a pure helper in `test_width_agnostic_label.py`, so the hang is in the session `tk_root` fixture - the first `ctk.CTk()` on the runner. `faulthandler_timeout = 60` is wired into pytest config since v2.2.0, so the next stall dumps every thread's traceback and names the exact line within a minute instead of burning the 15-minute job timeout in silence. Do not disable a test on a guess before then.
- [ ] **Surface the build advice in `Diagnostics` and the setup report.** `core/node_project.py` already recognises SvelteKit, Next, Nuxt, Astro, Angular, CRA, Vue CLI and Vite from a project's `package.json`, and says which command builds it and on which port its dev server runs. That advice currently only appears on the page the static server returns when a folder has no `index.html`. The same lines belong on the `Diagnostics` screen and inside the copyable setup report, where someone looks *before* they hit the problem.
- [ ] **The `.well-known` exception, if a project ever needs one.** Every dot-path is refused, deliberately. Revisit only when something real asks for it.

## Later

No dates. Picked up when something real asks for them.

### System Tray Integration

- [ ] Minimize to system tray
- [ ] Tray icon with context menu (Start / Stop / Exit)
- [ ] Notification on server start / stop
- Dependencies: `pystray`, `pillow`

### Linux CLI Mode

- [ ] Headless mode for running on Linux servers
- [ ] Command-line arguments: `--port`, `--root`, `--no-gui`
- [ ] Daemon mode support

### Multi-Project Support

- [ ] Tab interface for multiple projects
- [ ] Each project runs on a different port
- [ ] Quick switch between projects

## v3.0.0 - Major (No Date)

Breaking-change release that drops the v2.x compatibility surface.

- [ ] Remove `nanoserver.py` legacy launcher shim
- [ ] Remove the `~/.nanoserver/` legacy config fallback in `Config`
- [ ] Portable distribution: PyInstaller build for Windows, bundled PHP, Linux AppImage
- [ ] Virtual hosts support, SSL/HTTPS local certificates, request logging with filters

See [docs/decisions/0001-preserve-nanoserver-compat.md](docs/decisions/0001-preserve-nanoserver-compat.md) for the v2.x compatibility contract and the v3.0 removal checklist.

---

## Notes

### Docker

Fesium is a **desktop GUI application** that uses local file dialogs and the host's PHP installation. Running it in Docker is not recommended. For containerized PHP development, use a standard PHP/Apache or PHP-FPM image with docker-compose instead.

### MySQL Status

MySQL support is not yet implemented. Currently Fesium is SQLite-only. The planned MySQL/MariaDB addition lives under **Next up** above.

---

## Contributing

Pick up any item and open an issue or PR on GitHub. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/dev/conventions.md](docs/dev/conventions.md) for repo rules.