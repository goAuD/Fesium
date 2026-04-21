# Fesium Roadmap

Planned direction for `Fesium` after the v2.0.0 rebrand. Items here are intent, not a commitment — priorities shift as the app is used in classroom and dev environments.

Current released line: **v2.0.x** (see [docs/release/v2.0.0.md](docs/release/v2.0.0.md)).

## v2.1.0 — Next

Focus: UI polish and quality-of-life on top of the new shell.

### UI / UX

- [ ] Real `secondary` and `danger` button variants so destructive controls (Stop, Reset, destructive SQL) look distinct from primary actions
- [ ] Matte accent palette pass — soften the default accent so the UI reads calm in long sessions
- [ ] Badge sizing and text centering pass — badges subordinate to buttons
- [ ] `Read-only` switch sub-label clarifying session-scoped behavior
- [ ] Settings view wired to real preferences (port, default project folder, restore-last-project toggle)

### Reliability

- [ ] Unified `detect_php()` with a subprocess timeout to prevent UI hangs
- [ ] Consistent destructive-query detection (comments and `WITH ... UPDATE` CTEs)
- [ ] Hide SQLite internal tables (`sqlite_*`) from the schema browser

### Tests / CI

- [ ] Cross-platform GitHub Actions matrix (Ubuntu + Windows + macOS, Python 3.11 + 3.12)
- [ ] Coverage for subprocess timeouts and comment-stripping in SQL risk classification

## v2.2.0 — Soon After

### System Tray Integration

- [ ] Minimize to system tray
- [ ] Tray icon with context menu (Start / Stop / Exit)
- [ ] Notification on server start / stop
- Dependencies: `pystray`, `pillow`

### Linux CLI Mode

- [ ] Headless mode for running on Linux servers
- [ ] Command-line arguments: `--port`, `--root`, `--no-gui`
- [ ] Daemon mode support

## v2.3.0 — Later

### Multi-Project Support

- [ ] Tab interface for multiple projects
- [ ] Each project runs on a different port
- [ ] Quick switch between projects

### MySQL Support

- [ ] MySQL / MariaDB connection option
- [ ] phpMyAdmin-style query interface
- [ ] Connection string configuration

## v3.0.0 — Major (No Date)

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

MySQL support is not yet implemented. Currently Fesium is SQLite-only. The planned MySQL/MariaDB addition lives under **v2.3.0** above.

---

## Contributing

Pick up any item and open an issue or PR on GitHub. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/dev/conventions.md](docs/dev/conventions.md) for repo rules.
