# Fesium Server Flow Design

Date: 2026-04-19
Status: Draft for review
Scope: First interaction-restoration milestone after the `Fesium` brand rollout

## Summary

This milestone restores the first real interactive desktop flow in `Fesium` without collapsing the new architecture back into a monolith. The goal is to make the `Server` view operational again while keeping `Overview` informational.

The milestone covers:

- selecting a project folder
- automatic project detection for Laravel, standard PHP, and static HTML projects
- backend selection between `PHPServer` and a static fallback server
- `Start`, `Stop`, `Restart`, and `Open in Browser`
- a live or near-live server log panel
- persistence of the selected project and related basic state
- propagation of runtime state back into `Overview`

The milestone explicitly does not cover database interaction wiring. The `Database` view remains display-only in this phase.

## Goals

- Restore a usable local server workflow inside the new `Fesium` shell
- Keep interaction logic out of view classes
- Preserve the current security posture, especially local-first behavior and SQLite safety defaults
- Support offline use and non-PHP student projects through a static fallback server
- Keep the resulting structure small, testable, and ready for the next milestone

## Non-Goals

- SQL editor wiring
- database query execution from the new UI
- read-only toggle wiring in the database panel
- deep end-to-end desktop UI automation
- plugin or toolbox expansion beyond the current app
- manual document root override in this first milestone

## User Experience

### Overview

`Overview` remains a status-first landing view.

It should surface:

- current workspace path
- detected project type
- current server status
- environment health
- short quick-action messaging that points users toward the `Server` view
- optional recent log preview if there is meaningful runtime activity

It should not contain active server control buttons in this milestone.

### Server

`Server` becomes the operational control surface.

It should render:

- selected project path
- detected project type
- detected document root
- selected backend type
- current server status
- local URL when running
- action buttons:
  - `Select Project Folder`
  - `Start`
  - `Stop`
  - `Restart`
  - `Open in Browser`
- a server log panel

Recommended button behavior:

- `Start` enabled only when a valid project is selected and the server is not running
- `Stop` enabled only while running
- `Restart` enabled only while running
- `Open in Browser` enabled only while running and a local URL is known

## Detection and Backend Rules

### Project Detection

The current project detection base remains in `core/project_detection.py`.

Expected first-pass behavior:

- Laravel project:
  - detected by `artisan`
  - document root is `<project>/public`
  - project kind is `laravel`
- Standard project:
  - fallback when Laravel markers do not exist
  - document root is the selected root
  - project kind is `standard`

This milestone does not introduce a separate `html` project kind. Static HTML projects are treated as standard projects with a different runtime backend decision.

### Runtime Detection

A new `core/runtime_detection.py` module decides whether the active backend is:

- `php`
- `static`

Recommended decision logic:

1. If PHP is available:
   - Laravel uses `PHPServer`
   - standard projects also use `PHPServer`
2. If PHP is not available:
   - standard projects use the static fallback server
   - Laravel projects also fall back to static serving of the detected document root if possible, but the UI must make it clear that this is a reduced-capability fallback rather than full Laravel execution
3. If the selected project path is invalid or the document root cannot be served:
   - the controller returns an error state instead of attempting startup

This keeps the rule simple and predictable for the first milestone.

## Architecture

### New Modules

#### `src/fesium/core/static_server.py`

Responsible for serving static files when PHP is not available.

Responsibilities:

- serve the detected document root on `localhost`
- expose start and stop operations
- provide an `is_running` signal
- emit log lines through the same callback shape used by `PHPServer`
- expose the bound local URL

The implementation can use the standard library, such as `http.server`, as long as it stays offline-first and dependency-free.

#### `src/fesium/core/browser.py`

Small wrapper for opening a local URL in the default browser.

Responsibilities:

- open a validated local URL
- keep platform-specific opening logic out of the controller and view

#### `src/fesium/core/runtime_detection.py`

Responsible for deciding which backend kind should be active for the current project.

Responsibilities:

- inspect the detected project profile
- inspect PHP availability
- return a simple runtime decision object for the controller

#### `src/fesium/app/controller.py`

This is the key new orchestration layer.

Responsibilities:

- own the current app-side server state
- manage the selected project
- re-run detection when the project changes
- create and switch the active backend
- expose `start`, `stop`, `restart`, and `open_in_browser`
- receive log callbacks and maintain a bounded in-memory log buffer
- persist basic state into config
- expose state to the shell and views in a UI-friendly form

### Existing Modules That Stay

- `core/server.py`
- `core/project_detection.py`
- `core/environment.py`
- `core/config.py`
- `ui/shell.py`
- `ui/views/overview_view.py`
- `ui/views/server_view.py`

### Boundary Rules

- Views do not call `PHPServer` or the static fallback server directly
- Views do not contain project detection logic
- Views do not contain browser-launch logic
- The controller does not render widgets
- Core runtime modules do not know about `CustomTkinter`

## State Model

The controller should expose one clear runtime state object with fields similar to:

- `project_root`
- `project_kind`
- `document_root`
- `backend_kind`
- `server_status`
- `local_url`
- `php_available`
- `last_error`
- `log_lines`

Recommended values:

- `backend_kind`: `php`, `static`, or `none`
- `server_status`: `stopped`, `running`, or `error`

The UI should render from this state rather than from backend objects.

## Interaction Flow

### Select Project Folder

When the user clicks `Select Project Folder`:

1. Open a directory chooser
2. Normalize and validate the selected path
3. Re-run project detection
4. Re-run runtime detection
5. Update controller state
6. Persist `last_project`
7. Refresh the `Server` and `Overview` views

If validation fails:

- do not mutate the current running backend
- show a user-facing error state
- write the details into the log buffer

### Start

When the user clicks `Start`:

1. Validate the current project and document root
2. Resolve an active backend kind
3. Create the backend if needed
4. Start the backend with the detected document root and port
5. Store the resulting local URL
6. Mark the state as running
7. Append startup lines to the log buffer

### Stop

When the user clicks `Stop`:

1. Stop the active backend if running
2. Mark the state as stopped
3. Keep the selected project and detected runtime information
4. Append shutdown lines to the log buffer

### Restart

When the user clicks `Restart`:

1. Stop the active backend
2. Re-run startup against the current project and backend decision
3. Keep the action unavailable when the server is not already running

This milestone keeps `Restart` explicit and does not silently act like `Start`.

### Open in Browser

When the user clicks `Open in Browser`:

- require a running server
- require a known local URL
- open the URL through `core/browser.py`

If either condition fails, the controller should return an action error and log it instead of trying to infer missing state.

## Logging

The log panel should be backed by a bounded in-memory buffer owned by the controller.

Recommended first-pass behavior:

- keep the newest `200` lines
- allow both runtime backends to write through a shared callback interface
- append controller-level action messages such as:
  - project selected
  - backend resolved
  - server started
  - server stopped
  - browser opened
  - validation failed

The log view should prefer useful operational messages over noisy internals.

Sensitive local details should be limited to what is operationally useful, consistent with the approved security posture.

## Error Handling

The controller should separate three error classes:

### Validation Errors

Examples:

- selected folder does not exist
- document root does not exist
- invalid local path

Behavior:

- keep the app responsive
- do not crash the view
- surface a short user-facing message
- append detail to the log buffer

### Runtime Start Errors

Examples:

- selected backend cannot start
- no usable port found
- PHP runtime failure

Behavior:

- move state to `error`
- preserve current project selection
- append clear startup failure lines to the log

### Action Errors

Examples:

- `Open in Browser` without a running server
- `Restart` while stopped

Behavior:

- keep current runtime state unchanged
- show a short explanatory message
- log the rejected action

## Persistence

This milestone should persist only the stable pieces needed for the main server flow:

- `last_project`
- `active_view`
- `port`
- window geometry behavior already in place

It should not persist transient UI details such as:

- live log contents
- temporary errors
- button states

## Testing Strategy

### Core Tests

Add focused unit tests for:

- static fallback server startup and shutdown behavior
- runtime detection
- browser helper guardable behavior

### Controller Tests

Add unit tests for:

- selecting a project updates state correctly
- Laravel project chooses the `php` backend when PHP exists
- standard project chooses the `static` backend when PHP does not exist
- start moves state to running
- stop moves state to stopped
- restart is rejected while stopped
- open-in-browser is rejected while not running
- log buffer remains bounded

### View Tests

Add or extend view helper tests for:

- server status rendering
- action availability rules
- overview summary text based on live controller state

This milestone should prefer unit-level confidence over brittle desktop automation.

## Acceptance Criteria

The milestone is complete when:

- a project folder can be selected from the `Server` view
- project type and document root are updated automatically
- `PHPServer` starts when PHP is available
- a static fallback server starts when PHP is unavailable
- `Start`, `Stop`, `Restart`, and `Open in Browser` work with correct guards
- the `Server` log panel updates from real runtime events
- `Overview` reflects the actual selected project and server status
- the selected project survives app restart through config persistence
- the new logic is covered by focused unit tests

## Risks and Tradeoffs

- Static fallback for Laravel is intentionally limited. It is a usability fallback, not full Laravel execution.
- If the controller grows too much, it can become a new god file. Keep it narrow and push runtime-specific logic down into core modules.
- The first milestone should avoid manual document root editing, even if that would solve edge cases faster. Automatic detection is the agreed product direction here.

## Recommended Next Milestone

After this milestone, the next logical phase is the database interaction layer:

- SQL editor input
- read-only toggle wiring
- query execution and result rendering
- explicit confirmation flows for destructive actions

Keeping that work separate protects the current milestone from unnecessary coupling.
