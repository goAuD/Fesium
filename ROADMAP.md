# Fesium Roadmap

Future features and improvements planned for upcoming versions.

## v1.3.0 (Next Release)

### System Tray Integration
- [ ] Minimize to system tray
- [ ] Tray icon with context menu (Start/Stop/Exit)
- [ ] Notification on server start/stop
- **Dependencies:** `pystray`, `pillow`

### Linux CLI Mode
- [ ] Headless mode for running on Linux servers
- [ ] Command line arguments: `--port`, `--root`, `--no-gui`
- [ ] Daemon mode support

## v1.4.0 (Future)

### Multi-Project Support
- [ ] Tab interface for multiple projects
- [ ] Each project runs on different port
- [ ] Quick switch between projects

### MySQL Support
- [ ] MySQL/MariaDB connection option
- [ ] phpMyAdmin-style query interface
- [ ] Connection string configuration

## v2.0.0 (Major)

### Portable Distribution
- [ ] PyInstaller EXE build for Windows
- [ ] Bundled PHP (no installation required)
- [ ] Single-file portable executable
- [ ] Linux AppImage

### Advanced Features
- [ ] Virtual hosts support
- [ ] SSL/HTTPS local certificates
- [ ] Request logging with filtering
- [ ] Performance metrics

---

## Notes

### Docker
Fesium is a **desktop GUI application** that uses local file dialogs and the host's PHP installation. Running it in Docker is not recommended. For containerized PHP development, use a standard PHP/Apache or PHP-FPM image with docker-compose instead.

### MySQL Support
MySQL support is planned for **v1.4.0**. Currently only SQLite is supported. The roadmap item includes MySQL/MariaDB connections and a phpMyAdmin-style query interface.

---

## Contributing

Feel free to pick up any of these items! Open an issue or PR on GitHub.
