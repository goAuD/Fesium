# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Bootstrapped the `src/fesium/` package and thin launchers for the `Fesium` migration
- Migrated config, database, server, environment, project detection, and security helpers into modular core packages
- Added the first sidebar shell and real view modules for overview, server, database, environment, and settings
- Bundled offline font assets and Graphite Grid theme tokens
- Added repository guidance files, editor configuration, and a GitHub Actions pytest workflow

### Changed
- Repositioned the project under the `Fesium` brand while preserving the original local-dev purpose
- Updated the top-level documentation to reflect the current migration state honestly
- Kept SQLite read-only mode and local-first assumptions as explicit product defaults

### Removed
- Removed the legacy flat runtime modules in favor of the `src/fesium/` package layout
- Removed the old root-level `test_nanoserver.py` suite after replacing it with the new `tests/` structure

## [1.2.2] - 2026-01-27

### Security
- Added table name validation with regex pattern to prevent SQL injection in dynamic queries
- Added read-only SQL mode (enabled by default) that blocks INSERT/UPDATE/DELETE operations
- Added confirmation dialog for destructive queries (DROP, DELETE, UPDATE, TRUNCATE, ALTER)
- Added document root validation before server start

### Changed
- Updated misleading "SQL Injection Protection" claim to accurately describe raw SQL execution
- Added Docker and MySQL clarification to ROADMAP
- Added Development Setup section with testing instructions
- Version unification across codebase
- Removed unused "Pro Edition" branding

### Added
- Created `requirements-dev.txt` for development dependencies (pytest)
- Added version constraints to `requirements.txt`

## [1.2.1] - 2026-01-23

### Added
- Nano Design System theme module (`nano_theme.py`)
- Unified color palette across Nano product family
- NANO_COLORS constants for consistent styling

### Changed
- Updated UI to use Nano Design System colors
- Improved screenshot with dark theme background

## [1.2.0] - 2026-01-16

### Added
- Modular architecture: separated server, database, and config modules
- Real-time server log display in UI
- Config persistence (remembers last project folder and settings)
- SQL query parsing with read/write detection
- Execution tracing decorator for debugging
- Comprehensive unit test suite

### Changed
- Refactored codebase for better maintainability
- Improved transaction handling in database operations

## [1.0.0] - 2026-01-15

### Added
- Initial public release
- PHP built-in server management with GUI
- Laravel project auto-detection (serves from /public)
- SQLite database query interface
- Cross-platform support (Windows, Linux, macOS)
- Dark mode UI with CustomTkinter
- Port collision detection with auto-increment

