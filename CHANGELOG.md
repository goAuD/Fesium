# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Dependabot, keeping both the pinned requirements and the SHA-pinned GitHub Actions current.
- A Semgrep full scan of `main` on every push and weekly. Only pull requests were being scanned, and a diff scan cannot close a finding on the default branch, so five findings stayed open for ten days after the code causing them was fixed.
- `scripts/capture_screenshots.py`, which produces the README screenshots at exact colours and identical sizes. It replaces `scripts/capture_overview_mock.py`, which only opened a window to be photographed by hand.
- `scripts/profile_hot_paths.py`, which times one UI action and a cold start.
- `scripts/check_layout.py`, which drives the real views in a live window and measures legibility, settling and tile balance. The pytest suite is display-free and cannot see a layout bug.
- A `Project Database` check in `Diagnostics`. Fesium serves PHP but runs no database server, so a Laravel project pointed at MySQL used to start fine and then fail on its first query with a connection error from inside the framework. Fesium now reads the project's `.env`, checks whether anything is listening at the address it asks for, and says so plainly. Only `DB_CONNECTION`, `DB_HOST`, `DB_PORT` and `DB_DATABASE` are read - never credentials.
- Lucide icons in the sidebar, bundled as SVG sources plus rasterised PNGs under `src/fesium/assets/icons/lucide/`. They ship white on transparent and are tinted at runtime, so one file covers every state. `scripts/build_icons.py` regenerates them; nothing fetches or rasterises while the app runs.
- `CLAUDE.md` at the repo root, alongside `AGENTS.md`, covering the commands, the verification bar for UI work, and the traps specific to this codebase.
- Ruff lint, configured in `pyproject.toml` and enforced by its own CI job.
- The `Settings` view now holds real preferences instead of a placeholder: a default project folder, a reopen-last-project toggle, and the default server port. It states in one line which folder the next launch will open.
- `python -m fesium` and a `fesium` console script, so an installed copy does not need the root launcher.
- `secondary`, `danger`, and `danger_secondary` button variants, so destructive controls no longer look like primary actions.
- A sub-label under the `Read-only` switch explaining that write mode is session-scoped and resets on every launch.
- A cross-platform CI matrix (Ubuntu, Windows, macOS) replacing the single-runner workflow.

### Security

- CI actions are pinned to full commit SHAs instead of mutable `v4` / `v5` tags, which an action owner can silently repoint.
- The root launcher no longer `exec()`s the package `__init__` to read the version. `fesium._version` is now the single source, read by a plain import and by setuptools.
- Schema inspection binds the table name as a SQL parameter instead of formatting it into `PRAGMA table_info(...)`, using SQLite's `pragma_table_info()` table-valued function.
- Destructive-query detection now sees through leading comments and `WITH ... UPDATE` CTEs, so read-only mode cannot be talked past with a comment prefix.

### Changed

- Every UI action was spawning `php -v`. Rebuilding the views probed the PHP runtime eagerly, and eleven handlers rebuild the views, so each click stalled the window for ~78ms - 98% of the time spent selecting a project. The probe is gone from that path and the app-facing summary is cached; selecting a project went from 78.6ms to 1.7ms. `Diagnostics` re-probes when opened, which is the screen where a stale answer would matter.

- `requirements.txt` pins exact versions; `pyproject.toml` keeps the ranges. Semgrep's supply-chain analysis skips unpinned dependencies, so 17751 vulnerability rules were running against zero packages.
- Every view is a bento grid now, not just `Database`. `Overview`, `Server`, `Diagnostics`, `Guide` and `Settings` follow, and the scrolling page bodies are gone with them.
- `Overview` has real controls. The card titled `Quick Actions` used to contain none; serving state now takes the largest tile with Start, Stop and Open in Browser inline.
- `Server` presents its runtime facts as a two-column list instead of a label above each value, which hands the space back to the live log.
- The sidebar is one surface with the current row marked, instead of six bordered boxes. Nav rows carry an icon and lose their borders; the active row takes the accent.
- Pillow is now a declared dependency. customtkinter has always imported it for `CTkImage` without declaring it.
- The `Database` view is rebuilt as a bento grid. It used to stack six equally weighted panels, which pushed the SQL editor and results below the fold; the table list now runs the full height on the left, and schema, editor and results share the rest. The `Read-only` switch moved next to `Run SQL`, since it decides what Run does.
- Tile headings are small, uppercase and secondary-coloured. `accent.primary` is reserved for active state and primary actions instead of sitting on every section heading.
- `requires-python` is now `>=3.10`, matching what the code actually needs. CI runs that floor so the claim stays tested.
- Softened the accent palette to a matte tone so the shell reads calm in long sessions.
- Status badges are sized and centered to sit subordinate to the buttons beside them.
- The schema browser hides SQLite's internal `sqlite_*` bookkeeping tables.

### Fixed

- Starting a local server no longer freezes the window for two seconds. The port check connected to the port instead of trying to bind it, with no timeout, which measured 2047ms per call on Windows - and up to twenty times that when scanning for a free port. Binding answers the question the callers actually have, in 0.2ms.
- `test_find_available_port_returns_value_in_range` no longer fails at random. It scanned ports 50000-50004 and asserted one was free, which depends on what else the machine is doing; a Windows CI runner reported all five in use. The test holds a port itself now, so the answer is knowable.

- `Overview`'s `Workspace` tile shows the project path on its own; the project kind moved to the tile's meta rather than sitting in a labelled row beside it.
- Tile titles that do not fit are cut with an ellipsis instead of silently, and a meta list's label column now yields as the tile gets narrower instead of reserving a fixed 150px.
- Text is no longer clipped to a single character. `CTkLabel` grids its inner label with a sticky taken from `anchor`, so a correctly sized frame could still contain a 9px label once that label stopped asking for width.
- Panels no longer shimmer, and side-by-side tiles are the same width. A wrapped label asks Tk for its `wraplength` as its width, so it demanded back whatever width it was last given; that stretched one Diagnostics tile to 561px and squeezed its neighbour to 250px, clipping three lines of text, and the tug of war against the grid was visible as a flicker. Labels leave the width to the cell now.
- The `Server` controls fit on one row again. They wrapped at a hardcoded 980px, which was a guess about how wide five buttons are; the row now wraps only when the buttons measurably do not fit.
- Views no longer shift when you switch pages. Four of them wrapped their content in a scrolling frame that inset it by 6px, and each built its own header, so content started up to 6px left and 8px high depending on the page. All six share one `ViewHeader` and start at the same place.
- Buttons have room around their labels again. CustomTkinter derives horizontal padding from the corner radius, so squaring the corners had cut it from 10px to 2px.
- Nav labels line up with their icons.
- Corners no longer render doubled. CustomTkinter draws a rounded corner as an anti-aliased circle glyph and the straight edges as hard-edged rectangles, so wherever a radius met a border the two failed to line up. Structural surfaces are square now; status badges keep their capsule, which has no border and draws one clean arc.
- Badge text is optically centred. Tk centres a label on the font's line box, which reserves space above the caps for accents the label never uses, leaving the text a pixel low.
- Disabled buttons are readable again. CustomTkinter only swaps the text colour on a disabled button and leaves the fill alone, so a disabled primary rendered grey text on a full-strength accent at roughly 1.05:1 contrast. Disabled buttons now change surface too, and every button pairing is held to WCAG AA by a test.
- The `Results` panel showed its heading twice, because the empty-state view model also used "Results" as its title.
- Installing the package no longer drops the bundled fonts and icons. They were never declared as package data, so a `pip install` produced an app without its offline assets.
- Paragraph text no longer gets clipped at the start and end of every line. Views used fixed pixel wrap widths that were wider than the panel at any window below roughly 1400px, including the app's own 1100px minimum size. Paragraphs now wrap to the width they are actually given.
- `detect_php()` is a single probe with a subprocess timeout. Two chained probes used to freeze the UI on a slow or hanging `php` binary.

## [2.0.0] - 2026-04-19

See [docs/release/v2.0.0.md](docs/release/v2.0.0.md) for the narrative release notes.

### Added

- Bootstrapped the `src/fesium/` package and thin launchers for the `Fesium` migration
- Migrated config, database, server, environment, project detection, and security helpers into modular core packages
- Added the first sidebar shell and real view modules for overview, server, database, environment, guide, and settings
- Bundled offline font assets and Graphite Grid theme tokens
- Added repository guidance files, editor configuration, and a GitHub Actions pytest workflow
- Added the `Pure Orbit` brand assets, controlled GitHub social preview sources, and a new `Overview` screenshot
- Added runtime window icon assets sourced from the master brand SVG
- Added a static fallback server when PHP is unavailable
- Added controller-based runtime orchestration for project selection and local serving
- Added a live server log panel in the `Server` view
- Added interactive SQLite workflow in the `Database` view with manual database file selection
- Added one-statement SQL execution with result rendering and write-query confirmations
- Added a focused SQLite schema browser with table list, schema inspect, and quick preview queries
- Added a student-facing `Guide` view that explains when and how to use Fesium

### Changed

- Repositioned the project under the `Fesium` brand while preserving the original local-dev purpose
- Updated the top-level documentation to reflect the current migration state honestly
- Kept SQLite read-only mode and local-first assumptions as explicit product defaults
- Refreshed the public repository metadata around the `goAuD/Fesium` slug and approved topic set
- Consolidated contributor installation around a single primary `requirements.txt`
- Switched the repository license from MIT to Apache-2.0

### Removed

- `PanelCard` and `ScrollableViewBody`, superseded by `Tile` and `BentoGrid`.

- Removed the legacy flat runtime modules in favor of the `src/fesium/` package layout
- Removed the old root-level `test_nanoserver.py` suite after replacing it with the new `tests/` structure
- Removed obsolete root brand images and the legacy design-system document

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
