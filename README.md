# Fesium

<p align="center">
  <img src="docs/assets/brand/fesium-orbit.svg" width="120" alt="Fesium Pure Orbit logo">
</p>

**Local dev tools for students and developers.**

`Fesium` is the new direction of the original `NanoServer` project: a lightweight desktop app for serving local sites, inspecting SQLite databases, and keeping a student-friendly workflow fast, safe, and offline-first.

The migration off `NanoServer` is finished. Runtime code lives under `src/fesium/`, the old flat modules are gone, and every view is built on the same bento grid. What is left of the old project is two deliberate compatibility surfaces - the `nanoserver.py` launcher and a one-time read of `~/.nanoserver/config.json` - both scoped for removal in v3.0.0 by [ADR 0001](docs/decisions/0001-preserve-nanoserver-compat.md).

## Current Scope

`Fesium` currently targets:

- local project selection from the desktop app
- Laravel-aware and standard project detection
- PHP-backed local serving for projects that need it
- static local hosting for plain HTML, CSS, and JavaScript projects, whether or not PHP is installed
- static local serving as a fallback when a PHP project cannot find PHP
- opening the running local site in the default browser
- SQLite inspection and raw SQL execution with read-only defaults
- a readiness check for the database a project's own `.env` asks for
- lightweight SQLite schema browsing and table preview
- an in-app guide for students and first-time users
- stored preferences for the startup project and the default server port
- offline-first desktop usage

This is the first app in a future local-toolbox direction, but the repo does not pretend to be a larger suite yet.

## Principles

- **Offline-first:** no runtime dependency on external assets or hosted services
- **Security-first defaults:** read-only SQLite mode, local-only server assumptions, explicit destructive-action handling
- **Student-friendly:** lightweight setup, clear diagnostics, minimal friction on school or restricted machines
- **Modular architecture:** runtime logic under `src/fesium/` instead of a single monolithic script

## How It Is Built

- `core/` holds the framework-free logic - config, server, database, environment, paths, project detection and security - and never imports from the UI
- `app/` is bootstrap and controller; `ui/` is the shell, views, widgets and theme; `assets/` is everything bundled
- all six views are laid out as a bento grid, so size carries the hierarchy instead of a stack of equally weighted panels
- the `Graphite Grid` fonts and the Lucide icons ship in-repo and are tinted at runtime from the theme, so nothing is fetched or rasterised while the app runs
- a contrast floor is held by tests: every button and text-on-surface pairing clears WCAG AA
- the unit suite runs headless, without PHP and without network access, and `scripts/check_layout.py` covers what a display-free suite cannot see

## Local Server Workflow

From the `Server` view, `Fesium` can:

- select a local project folder
- auto-detect Laravel projects or treat the folder as a standard site
- run the site with PHP when the project actually uses PHP, and serve it statically when it does not
- fall back to static serving when a PHP project cannot find PHP, with `Diagnostics` saying what is missing
- open the running local site in your browser
- follow the live server log beside the runtime facts, in one screen with no scrolling

## Database Workflow

From the `Database` view, `Fesium` can:

- use a project-detected SQLite database when one is available
- let you manually select a `.sqlite`, `.db`, or `.db3` file
- reset back to the detected project database
- browse detected tables in the active SQLite file
- inspect column names, types, nullability, and primary-key flags
- generate a quick `SELECT * LIMIT 100` preview for the selected table
- run one SQL statement at a time
- keep `Read-only` mode enabled by default on every launch
- require confirmation before destructive queries run in write mode

The database tooling is intentionally SQLite-only and lightweight: a focused schema browser, not a database IDE.

## Settings

From the `Settings` view, `Fesium` can:

- choose whether launching reopens your last project
- set a default project folder to fall back on
- set the default port for the local server, validated to the 1024-65535 range

Preferences live in `~/.fesium/config.json`. A folder that has been moved or deleted since the last launch is skipped rather than treated as an error, and the view states in one line which folder the next launch will open.

## Current UI Preview

`Overview` shows what is running, where, and what just happened, with the controls in the tile itself.

![Fesium Overview](docs/assets/screenshots/fesium-overview.png)

`Server` keeps the runtime facts compact so the live log gets the room.

![Fesium Server view](docs/assets/screenshots/fesium-server.png)

Both are produced by `python scripts/capture_screenshots.py`, which grabs the window's client area directly. That keeps the colours exact - a snipping tool shifted every channel by about +17 and washed the whole palette out - and every image comes out the same size.

## Quickstart

```bash
git clone https://github.com/goAuD/Fesium.git
cd Fesium
python -m pip install -r requirements.txt
python fesium.py
```

Requires Python 3.10 or newer. Fesium serves your site. It does **not** run a database server: a project pointed at MySQL or PostgreSQL needs that service running separately, and the `Diagnostics` view says so before you open the site. SQLite needs nothing, because it is a file.

PHP on your `PATH` is only needed for projects that use PHP. A plain HTML, CSS and JavaScript project is served by the built-in static server either way.

Installing the package instead of running from the clone gives you a `fesium` command and `python -m fesium`:

```bash
python -m pip install -e .
fesium
```

Full install, launcher, and test instructions live in [docs/dev/setup.md](docs/dev/setup.md) and [docs/dev/testing.md](docs/dev/testing.md).

## Project Layout

```text
Fesium/
├── src/
│   └── fesium/
│       ├── app/
│       ├── core/
│       ├── ui/
│       └── assets/
├── tests/
├── docs/
├── fesium.py
└── nanoserver.py
```

## Origin

The project started as `NanoServer`, built as a free alternative for school environments where tools like Laragon were no longer a practical option. `Fesium` keeps that purpose, but gives it a stronger architecture, a better product shell, and a clearer long-term direction.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor entry point, and [docs/](docs/) for the full documentation tree (setup, testing, conventions, specs, plans, decisions, release notes).

## License

The repository is licensed under the Apache License, Version 2.0.
