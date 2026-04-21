# Fesium Redesign Design Spec

- Date: 2026-04-17
- Status: Approved for spec review
- Project: Rename and redesign of NanoServer into `Fesium`

## 1. Summary

`Fesium` is the new umbrella brand for the current NanoServer desktop application. The first shipped product remains a local desktop utility for students and developers, focused on local PHP serving, SQLite access, and environment diagnostics, while the product language, information architecture, and repository structure are redesigned to support future expansion into a broader local dev toolbox.

The first redesign release keeps the current Python and `CustomTkinter` foundation, preserves the existing backend logic where it is already sound, and replaces the single-file UI with a modular desktop shell built around a sidebar navigation model. The redesign is explicitly `offline-first`, `security-first`, and suitable for a public open-source repository.

## 2. Product Positioning

### Primary Positioning

`Fesium` is a local development utility suite for students and developers.

The first release under the new brand should communicate:

- easy local setup
- low friction for school and lightweight development work
- safe defaults
- local-only workflow without hidden cloud dependencies

### Brand Strategy

The brand is an umbrella brand, not a feature label. This is intentional:

- the current application is the first tool under the `Fesium` name
- the brand must remain usable if future local tools are added
- the name must not be tied to PHP, SQLite, or student-only language

### Working Product Message

`Fesium`

`Local dev tools for students and developers`

This message keeps the student-friendly origin visible without constraining the project to a school-only audience.

## 3. Goals

### Product Goals

- Rename NanoServer to `Fesium`
- Reposition the app from a single-purpose PHP launcher to the first tool in a local developer toolbox
- Deliver a more modern and structured desktop UX
- Preserve the app's lightweight and practical nature
- Keep the first release usable for students immediately

### Engineering Goals

- Split the current monolithic UI into focused modules
- Move to a public-repo-friendly `src/` layout
- Add repository structure that supports documentation, decisions, tests, and future modules
- Preserve existing backend logic where it is already adequate
- Avoid unnecessary platform migration in the first redesign

### Experience Goals

- The app must feel more intentional and modern without becoming visually noisy
- The shell must support future modules without fake or empty features
- The UI must remain understandable for less experienced users
- The app must remain fully functional without internet access

## 4. Non-Goals

- No migration to `PySide6` or another UI framework in the first redesign release
- No fake plugin marketplace or empty future modules in the sidebar
- No cloud dependency, telemetry requirement, or online asset loading
- No expansion to MySQL or multi-project orchestration in the first redesign release
- No major backend rewrite if the current core behavior is already correct

## 5. Architecture Decision

### Chosen Direction

The redesign will use a hybrid approach:

- keep `CustomTkinter` for the first redesign release
- reorganize code and views as if the project may later grow into a broader toolbox
- isolate UI, core logic, theme, and diagnostics so a later UI migration remains possible

### Why This Direction Was Chosen

This is the best compromise between delivery speed and long-term maintainability:

- the current backend behavior can be reused
- the UI can be improved substantially without a full platform rewrite
- the repository can be reorganized now so later growth does not force another structural reset

## 6. App Information Architecture

The application shell will use a left sidebar with real views only.

### Navigation

1. `Overview`
2. `Server`
3. `Database`
4. `Environment`
5. `Settings`

### View Responsibilities

#### Overview

Purpose:

- give a clear first-screen summary
- surface the active workspace
- expose the fastest safe actions
- summarize health and recent activity

Contains:

- workspace summary card
- quick actions card
- environment health card
- recent activity or log preview card

#### Server

Purpose:

- handle server-oriented workflow without mixing database or diagnostic concerns

Contains:

- selected project path
- detected document root
- port information
- start, stop, and restart actions
- open in browser action
- live server log panel

#### Database

Purpose:

- expose SQLite operations with explicit safety framing

Contains:

- selected database path
- read-only state indicator
- SQL input
- run action
- result summary and results area

#### Environment

Purpose:

- separate diagnostics from core usage

Contains:

- PHP availability
- PHP version if available
- PATH or environment hints
- project detection summary
- validation messages for common local setup problems

#### Settings

Purpose:

- persist user preferences and safety defaults without cluttering operational views

Contains:

- default port
- remembered path behavior
- startup preferences
- UI preferences that do not change core app behavior
- safety-related toggles only where a persistent setting is appropriate

## 7. Visual Design Direction

### Chosen Visual Direction

`Graphite Grid`

This is the approved visual direction for the first redesign release.

### Design Intent

The application should feel modern, elegant, and tool-like without becoming loud or decorative. The visual system should avoid flat enterprise grey and avoid overusing neon or cyberpunk styling.

### Surface Strategy

- deep graphite backgrounds instead of pure black
- subtle faceted or diamond-like geometric background pattern
- restrained accent usage
- clear separation between shell surfaces and work surfaces

### Color Tokens

Initial design tokens:

- `bg.app = #121419`
- `bg.sidebar = #171a21`
- `bg.panel = #181d25`
- `bg.panel_alt = #151a22`
- `border.default = #2b3440`
- `border.soft = #29313d`
- `text.primary = #eef3f7`
- `text.secondary = #8f9aa8`
- `accent.primary = #73F0FF`
- `accent.success = #52E38F`
- `accent.warning = #FFB454`
- `accent.danger = #FF6B6B`

### Layout Rules

- Sidebar remains text-based in the first redesign release
- Main content uses a context strip at the top with title, short description, and state badge
- Work content is organized into cards, not one continuous surface
- Operational surfaces such as inputs, logs, and query panels must remain calmer than outer shell surfaces

### Component Rules

- Card radius: approximately 14px to 16px
- Border weight: subtle, low-contrast, always visible
- Primary actions: filled accent treatment
- Secondary actions: dark surface buttons
- Inputs: visible focus state using the primary accent
- Logs: monospace, high legibility, non-black background

### State Language

- `Workspace Ready`
- `Running`
- `Stopped`
- `PHP Missing`
- `Read-only Enabled`
- `Laravel Detected`

State language must remain explicit and readable. Safety-oriented states must not read like errors unless they represent actual failure.

## 8. Typography and Offline Font Policy

The app must not depend on online font delivery.

### Font Principles

- fonts are bundled locally in the repository
- no CDN font loading
- no runtime dependence on internet access
- if a preferred font fails to load, the fallback chain must preserve layout integrity

### Selected Font Set

The first redesign release should bundle:

- `Sora` for headings and high-visibility UI labels
- `IBM Plex Sans` for body UI text
- `JetBrains Mono` for logs and technical surfaces

### Packaging Rules

- font files live under `src/fesium/assets/fonts/`
- license texts for bundled fonts live alongside the font assets or in a dedicated `licenses/` subdirectory
- the theme system must define fallback families for every font role

This gives the project an offline-capable and repo-contained visual identity without relying on the host system for the intended appearance.

## 9. Offline-First Principles

`Fesium` should treat offline behavior as a design constraint, not an implementation accident.

### Requirements

- all primary app functionality must work without internet access
- UI assets must be local
- fonts must be local
- core diagnostics must not require network calls
- documentation needed for local continuation must exist inside the repository

### Product Consequences

- no hidden telemetry
- no web-hosted dependencies for the core experience
- no external UI resources loaded at runtime
- local workflows remain first-class even on restricted school or lab machines

## 10. Security-First Principles

The product should continue to prefer safe defaults over convenience where the tradeoff is reasonable.

### Required Defaults

- SQLite read-only mode is enabled by default
- destructive queries require explicit confirmation
- server binds to `localhost` by default
- document root is validated before startup
- project and database paths are normalized and existence-checked
- PHP availability is validated before attempting server actions

### Additional Design Requirements

- safety state must be visible in the UI
- diagnostics should surface setup problems clearly without dumping unnecessary sensitive details
- logs should avoid exposing more local environment detail than is useful for troubleshooting
- future tools added under `Fesium` should inherit the same `safe-by-default` posture

### Core Security Module

A dedicated `security.py` module should be introduced for first-class safety checks that do not belong inside view code. This module should encapsulate reusable guards around file paths, dangerous actions, and future extension points.

## 11. Codebase Restructure

The current codebase is small enough to reorganize without a risky rewrite. The goal is a public-repo-friendly structure with clear boundaries.

### Target Repository Layout

```text
Fesium/
├─ src/
│  └─ fesium/
│     ├─ app.py
│     ├─ core/
│     │  ├─ config.py
│     │  ├─ database.py
│     │  ├─ environment.py
│     │  ├─ paths.py
│     │  ├─ project_detection.py
│     │  ├─ security.py
│     │  └─ server.py
│     ├─ ui/
│     │  ├─ shell.py
│     │  ├─ theme/
│     │  │  ├─ styles.py
│     │  │  └─ tokens.py
│     │  ├─ views/
│     │  │  ├─ database_view.py
│     │  │  ├─ environment_view.py
│     │  │  ├─ overview_view.py
│     │  │  ├─ server_view.py
│     │  │  └─ settings_view.py
│     │  └─ widgets/
│     └─ assets/
│        └─ fonts/
├─ tests/
│  ├─ integration/
│  └─ unit/
├─ docs/
│  ├─ decisions/
│  └─ specs/
├─ scripts/
├─ .github/
│  └─ workflows/
├─ .gitignore
├─ AGENTS.md
├─ CHANGELOG.md
├─ CONTRIBUTING.md
├─ LICENSE
├─ README.md
├─ pyproject.toml
└─ .editorconfig
```

### What Stays

The following core logic is retained conceptually, then moved into the new layout:

- PHP process management
- port detection and fallback
- SQLite execution logic
- config persistence
- Laravel detection
- log capture

### What Changes

- the current main UI file is decomposed into multiple views
- project detection moves out of the UI file
- environment diagnostics become a first-class core concern
- safety checks become reusable core behavior instead of mixed UI logic

## 12. Testing Strategy

The redesign must preserve the current strength of the project: small, understandable, testable logic.

### Testing Priorities

- unit tests for retained core logic
- unit tests for new project detection and environment diagnostics helpers
- unit tests for security guards
- integration tests for server startup preconditions where practical

### Testing Principles

- UI code should remain thin where possible
- business logic should live outside views
- anything safety-related should be testable without rendering UI

## 13. Documentation and Repository Hygiene

The repository should support pause-and-resume collaboration without relying on chat memory.

### Required Repo Files

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `AGENTS.md`
- `.gitignore`
- `.editorconfig`
- `pyproject.toml`
- GitHub workflow files under `.github/workflows/`

### Documentation Rules

- major implementation work should reference a spec or decision record
- architectural decisions should be tracked under `docs/decisions/`
- docs should explain enough for another contributor to continue the project without reverse-engineering intent
- local workspace artifacts such as `.fesium/` must remain untracked through `.gitignore`

## 14. AGENTS.md Direction

`AGENTS.md` should be repository-specific and operational, not generic.

It should document:

- the product goal of `Fesium`
- the `offline-first` rule
- the `security-first` rule
- the approved visual direction
- the required `src/` layout
- the expectation that new logic is placed in the correct module rather than added to large catch-all files
- the documentation expectation for major design and architecture changes

## 15. Delivery Scope for the First Redesign Release

The first redesign release should include:

- rename to `Fesium`
- repository restructure
- modular desktop shell with sidebar navigation
- `Overview`, `Server`, `Database`, `Environment`, and `Settings` views
- approved graphite visual system
- local bundled fonts
- preserved core server and SQLite capability
- explicit security and diagnostics improvements

It should not include:

- framework migration to Qt
- online dependency for basic usage
- fake future tools in the UI
- unrelated feature expansion

## 16. Future Expansion Boundary

This redesign intentionally prepares for future growth without pretending the suite already exists.

Future tools may be added later, but the first release should remain honest:

- one application
- multiple real views
- stronger brand and structure
- no empty promises in the interface

## 17. Final Decision

The project should move forward as `Fesium`, using the approved `Graphite Grid` visual direction, a modular `CustomTkinter` desktop shell, bundled offline fonts, public-repo-ready structure, and security-first defaults.
