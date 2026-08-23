# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- The screenshots on the Pages site are sized against the column they sit in rather than against the viewport. `100vw` counts the scrollbar and the layout does not, so the previous attempt came out a scrollbar's width too wide and pushed them off the right edge on a desktop window - while still leaving them narrower than the body text on a phone. They now widen by exactly the figure's own padding and border, which puts them flush with the paragraphs above and below at every size, reach both screen edges below 680px, and take their full 1272px only above 1360px where there is demonstrably room. Checked at twelve widths from 320px to 1920px with a scrollbar accounted for.

### Security

- The static server no longer serves dot-files. A project served from its own root handed out `.env` in full and the whole of `.git` over HTTP - `GET /.env` returned `DB_PASSWORD=...` with a 200. Localhost only, but Fesium reads exactly four keys out of a project's `.env` and deliberately never touches the credentials in it, and serving the file whole undid that care entirely. Any path with a dot-segment is refused, checked after unquoting so `%2Eenv` is the same request as `.env`.

- A security review of the local servers ([findings](docs/reviews/ox-alpha-review-2026-08-23.md)) turned up three ways past that filter, all closed now:
  - **Double-encoded paths.** The filter unquoted once while `translate_path` unquotes again, so `GET /%252Eenv` passed as `%2Eenv` and was served as `.env`. The check now decodes to a fixed point, so both layers see the same path.
  - **Links out of the project folder.** `translate_path` follows symlinks and junctions wherever they land - a cloned repo carrying one could serve any file the user can read. Requests must now resolve to a path inside the document root; on Windows resolving also expands short names, closing the `GIT~1` route to a dot directory. NTFS streams (`/.env::$DATA`) fall under the same checks.
  - **DNS rebinding.** Binding to `127.0.0.1` keeps the network out but not the browser: a page can rebind its own domain to `127.0.0.1` and read responses same-origin. Such requests carry the attacker's domain in `Host`, which is now required to be `127.0.0.1` or `localhost` on this server's port.

- The PHP built-in server applies the same dot-path filter. `php -S ... -t docroot` alone serves the document root raw, so on the PHP backend `GET /.env` needed no trick at all. A bundled `router.php` refuses dot paths - decoded to a fixed point, like the Python side - and falls through to the built-in handler for everything else.

### Fixed

- Starting the PHP backend waits until it is actually listening before reporting success. `php -S` is a subprocess, so `Popen` returning said nothing about whether PHP had bound anything - measured at roughly **600ms** on this machine, during which Fesium logged `Started`, enabled `Open in Browser` and would have handed the user a connection error. A backend that never comes up now reports the failure instead of the same success. Found because the new PHP router test raced and failed on Ubuntu CI while passing everywhere slower.

- The local server is reached at `127.0.0.1` rather than `localhost`, and binds there too. The name resolves to `::1` before `127.0.0.1` on Windows and macOS while both servers bind IPv4 only, so anything connecting by name tried IPv6 first, against a port nothing was listening on. On Windows that measured **2131ms against 2ms**. On a macOS runner the IPv6 attempt is not refused at all, it hangs - which is what left a `macos-latest / py3.11` job running until it was cancelled, three times. The suite went from 23s to 6.8s as a side effect, since every HTTP test was paying that timeout.

- Every HTTP call in the test suite sets a timeout, and the test job has a `timeout-minutes`. Neither did, so one stalled connection could hold a runner for six hours and report nothing at all. A test greps for calls without one; the job timeout is the backstop for whatever is not thought of.

- A folder with no `index.html` explains itself instead of listing its files. Opening a SvelteKit project showed a directory listing of the repository - `.git/`, `node_modules/`, `package.json` - which looks like a broken website and says nothing about why. Fesium now reads the project's `package.json`, recognises the framework, and answers with what is actually missing: which command builds it, where a build already sits if there is one, and that `npm run dev` serves it on its own port and rebuilds as you edit, which Fesium does not do.

- The Pages site's header no longer breaks apart on a phone. The five section links are flex children with no `white-space` rule, so when the row was squeezed each one wrapped *inside itself* - three lines for `How it is built`, one for `GitHub` - which is what made it look ragged rather than merely tight. Measured against the bundled face: the links want 421px and a 390px phone leaves about 240px for them, so it cannot fit below roughly 570px however it is styled. Links no longer break mid-phrase at any width, and below 680px the section anchors are hidden, leaving the one link that does something rather than scrolling to a section a reader reaches anyway. With them gone there is 126px of headroom on a 320px screen, so the wordmark stays.

- The landing page no longer repeats the mark at 168px directly under the 28px one in its own header. It said nothing the header had not already said and pushed the first real content down, which cost most on the screen with least room.

### Added

- A `Setup Report` in `Diagnostics`: one button that copies everything on that screen as plain text, to paste into a message when asking for help. A student who is stuck asks a teacher, and what follows is five rounds of "which PHP", "where is the project", "is MySQL actually running" - answers already on the screen. This turns that exchange into one paste. The home folder is shortened to `~`, because the whole point is that the text gets sent somewhere and a Windows path carries the account name. No credential can appear in it: the report prints a `DatabaseRequirement`, and a test asserts that type has no field for a user or a password.

- A GitHub Pages site, built by `scripts/build_site.py` and deployed by `.github/workflows/pages.yml`. It imports `COLOR_TOKENS` from the app rather than restating the palette, because the brand assets had already drifted from the product once. The page is one self-contained file with the screenshots inlined; a test regenerates it and fails if the committed copy and the generator disagree.
- [ADR 0002](docs/decisions/0002-mysql-through-our-own-view.md), settling how MySQL will be reached: through the `Database` view Fesium already has, over `PyMySQL`, rather than by bundling an admin panel or rebuilding one. Serving Adminer in a browser would have put a `DROP TABLE` one click away with none of Fesium's read-only default in between, and rebuilding it would inherit a web application's attack surface with none of its scrutiny.
- A test that every GitHub Actions reference in every workflow is pinned to a full commit SHA. The repo already pinned them by hand - a tag is mutable and its owner can silently repoint it - but nothing stopped the next workflow from forgetting.

## [2.1.0] - 2026-08-22

### Added

- `scripts/build_brand.py`, which draws the mark, the README banner, the social preview and the app icons from one geometry definition. The old assets had drifted apart: the mark was still the pre-matte neon `#73F0FF`, the preview set its wordmark in Arial, and the committed `.svg` and `.png` of the same poster disagreed.

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

- The app is set in `Atkinson Hyperlegible`, replacing `Sora` and `IBM Plex Sans`. The three faces were never chosen, they were picked at the start and kept, so five candidates were measured at 16px on how far apart their confusable characters sit. `Sora` had the worst pair of any of them - its `l` and `1` measured 0.10 apart on a 0-to-1 scale - and it was setting 12px tile titles, which is display-face work. Atkinson was drawn by the Braille Institute for exactly this and is the only candidate with a dotted zero, which is what a screen made of ports, ids and paths needs. One family plus `JetBrains Mono` now, because size and weight already carry the hierarchy in a bento layout.

- The brand mark is a solid tile rather than three transparent rings. Every stroke of the old mark was `stroke-opacity="0.28"` neon cyan, measuring 2.12:1 against GitHub's dark canvas - under the 3:1 floor for a graphical object - and, because the SVG was transparent and a README borrows the reader's theme, **1.10:1 in light mode**, which is invisible. Nothing in it had mass, so it also had no silhouette left below 32px.

- The README leads with a banner that bakes its own dark ground, so the header renders identically in either GitHub theme instead of borrowing whichever one the visitor is on. The social preview was redrawn in the matte palette; its predecessor tiled a 160px facet pattern that resolved into visible horizontal banding.

- The app icon carries per-size artwork. A `.ico` entry is redrawn heavier at 16px rather than downscaling artwork built for 512, where the orbit turned to mush.

- The docs describe the app as it behaves now. `README.md` still announced a migration that has finished, and three of its claims had gone stale behind the bento rework: it advertised `scroll-safe` views after the scrolling page bodies were removed, bordered panel surfaces after the sidebar became one, and PHP serving whenever PHP is installed rather than when the project uses it. Its `Status` section was a migration progress log rather than a description of the app. `AGENTS.md`, `CONTRIBUTING.md` and `docs/dev/setup.md` carried the same framing.

- The environment report follows the project. `Overview` showed a PHP version and `Diagnostics` a PHP runtime section for a plain HTML and JavaScript site that never touches PHP. A project that needs no runtime now says so, and a missing PHP is only flagged for a project that wants PHP.
- `Diagnostics` names the PHP binary it probed. A machine can carry several - a standalone install and a leftover from Laragon or XAMPP are common - and `PATH` decides which one Fesium gets, so a version number alone did not say which.

- The backend follows the project rather than the machine. Fesium picked the PHP built-in server whenever PHP was on `PATH`, using the project only to build a log message, so a plain HTML and JavaScript site was served by a PHP process it had no use for - and the static server was only ever a fallback, which contradicted the Guide describing it as a first-class workflow. A project is served statically unless it actually uses PHP.
- `Static Fallback` is now `Static Server` in the `Server` view. For a project that does not need PHP it is not a fallback; when PHP is genuinely missing, `Diagnostics` says so.

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

- Button and badge text sits centred again. Both widgets carried their own copy of a 2px bottom padding, measured against IBM Plex Sans, that pulled the text up to compensate for that face reserving more room above its caps than below its baseline. Atkinson's line box is already balanced, so the correction survived the swap as a visible shove upwards - measured at 12px above the caps against 16px below the baseline in a 38px button, where the two had been within a pixel of each other before. The offset now lives once in `tokens.py` beside the font decision it depends on, and a test derives the right value from the bundled font file so the next swap fails rather than ships.

- The sidebar tagline no longer wraps to a width the sidebar did not give it. It carried `wraplength=180`, a pixel constant tuned to the old body font, and changing the typeface was enough to break it - which is the failure the repo's own convention against hardcoded wraps exists to prevent. It uses `BodyText` now and takes the wrap from the width it is actually given. `scripts/check_layout.py` caught this; the pytest suite is display-free and could not.

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
