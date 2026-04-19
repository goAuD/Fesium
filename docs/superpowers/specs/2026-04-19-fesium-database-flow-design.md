# Fesium Database Flow Design

Date: 2026-04-19
Status: Draft for review
Scope: First SQLite interaction milestone after the restored server flow

## Summary

This milestone restores the first real database interaction workflow inside the new `Fesium` shell without overbuilding a full database browser. The goal is to make the `Database` view operational for SQLite files through a safe raw-SQL-first workflow that matches the project's offline-first and security-first posture.

The milestone covers:

- project-detected SQLite database selection
- manual `.sqlite` file selection through the UI
- session-scoped `read-only` mode with safe defaults
- one-statement-at-a-time SQL execution
- result rendering for read queries, write queries, and errors
- destructive-query confirmation when write mode is enabled
- fixing the inset panel corner artifact introduced by the current layered card rendering

The milestone does not attempt to build a full schema browser, table explorer, or multi-step SQL workspace.

## Goals

- Restore a usable SQLite workflow inside the `Database` view
- Keep `read-only` mode enabled by default on every app launch
- Make manual database selection explicit and persistent for the current session
- Keep database interaction logic out of the view class
- Preserve the existing `DatabaseManager` and security helper logic where possible
- Fix the visual panel-corner artifact as part of the same UI round

## Non-Goals

- Full database schema browser
- Table list and drilldown navigation
- Multi-statement SQL execution
- Query history, saved queries, or tabs
- Non-SQLite database engines
- Persisting write mode across app restarts
- Deep desktop UI automation

## User Experience

### Database View

The `Database` view becomes an operational utility screen with an explicit safety posture.

It should render:

- the currently active database path
- a source badge:
  - `Project Database`
  - `Manual Database`
  - `No Database Selected`
- a `Read-only Enabled` or `Write Mode` badge
- a `Select Database File` button
- a `Reset to Project Database` button when a project-detected database exists
- a `Read-only` toggle
- a SQL editor
- a `Run SQL` button
- a result panel that can display:
  - row and column output for read queries
  - affected row count for write queries
  - clear error output for invalid or blocked queries

This view should still feel like a focused utility panel rather than a full IDE.

### Database Source Rules

The active database source should follow these rules:

1. When a project is selected and no manual database has been chosen yet:
   - use the project-detected database when available
2. When the user manually selects a database file:
   - mark the source as `manual`
   - keep using it until the user explicitly changes it
3. When the user clicks `Reset to Project Database`:
   - switch back to the detected project database if one exists
4. If no usable project or manual database exists:
   - show `No Database Selected`

The UI must not silently overwrite a manual database choice during project refresh.

### Read-only Behavior

`Read-only` mode remains a core safety feature.

Required behavior:

- every app launch starts with `read-only` enabled
- the user may disable it for the current session only
- the view must make the current safety state obvious
- if a write query is attempted while `read-only` is enabled:
  - block execution
  - show a clear user-facing message

### Query Execution Contract

The first milestone stays intentionally strict:

- one `Run SQL` action executes one SQL statement only
- empty queries are rejected with a clear error
- multi-statement input is rejected
- destructive queries require a confirmation dialog when write mode is enabled

This keeps the execution model understandable and reduces accidental damage.

## Architecture

### Existing Core Reuse

The milestone should continue using:

- `src/fesium/core/database.py`
- `src/fesium/core/security.py`
- `src/fesium/app/controller.py`
- `src/fesium/app/bootstrap.py`
- `src/fesium/ui/views/database_view.py`

The existing `DatabaseManager.execute()` and `classify_query_risk()` logic are the right starting points.

### Controller Responsibilities

The existing `FesiumController` should absorb the database interaction state rather than introducing a second app-level controller.

Recommended new state fields:

- `database_path`
- `database_source`
- `database_read_only`
- `database_last_query`
- `database_last_result`
- `database_last_error`

Recommended `database_source` values:

- `project`
- `manual`
- `none`

The controller should expose small focused methods such as:

- `select_database(path)`
- `reset_to_project_database()`
- `set_database_read_only(enabled)`
- `run_database_query(query)`

The controller remains responsible for state transitions, not widget rendering.

### View Responsibilities

`DatabaseView` should:

- render the current DB state
- expose callbacks for selection, reset, toggle, and run
- read the SQL editor content when `Run SQL` is clicked

`DatabaseView` should not:

- call `DatabaseManager` directly
- classify query risk
- decide whether a destructive query needs confirmation

### Bootstrap Responsibilities

The UI orchestration in `src/fesium/app/bootstrap.py` should:

- wire file selection dialogs for manual database choice
- wire the destructive-query confirmation dialog
- refresh the relevant views after DB actions

This is consistent with how server-flow file dialogs are already handled.

## Query Safety Rules

### Statement Count

The first implementation only supports one SQL statement per run.

Required outcomes:

- one valid statement: execute
- multiple statements: reject
- empty or whitespace-only input: reject

This should happen before actual query execution.

### Read vs Write

The current `is_read_query()` logic remains the base gate for read-only enforcement.

Required outcomes:

- read query in read-only mode: allowed
- write query in read-only mode: blocked with a clear message
- write query in write mode: allowed only after normal validation

### Destructive Queries

The current `classify_query_risk()` helper should remain the main destructive-query check.

Required behavior:

- if `requires_confirmation` is `False`, run normally
- if `requires_confirmation` is `True` and write mode is enabled:
  - show a simple yes/no confirmation dialog
  - only execute on explicit approval

The first milestone does not require typed confirmation text.

## Result Model

The UI should render from a simple controller-owned result shape instead of raw sqlite objects.

Recommended result kinds:

- `none`
- `read`
- `write`
- `error`

Recommended read result payload:

- `columns`
- `rows`
- `count`

Recommended write result payload:

- `affected`

Recommended error payload:

- `message`

This keeps the rendering contract small and testable.

## Interaction Flow

### Select Database File

When the user clicks `Select Database File`:

1. Open a file picker
2. Let the user choose a SQLite-like file
3. Normalize and validate the path
4. Set the active database source to `manual`
5. Clear stale DB result state
6. Refresh the `Database` view

### Reset to Project Database

When the user clicks `Reset to Project Database`:

1. Check whether a project-detected database exists
2. If yes:
   - set that path active
   - mark the source as `project`
   - clear stale DB result state
3. If no:
   - leave the current state unchanged

### Toggle Read-only

When the user toggles `Read-only`:

1. Update controller state
2. Rebuild the DB manager or update its active mode
3. Refresh the `Database` view

This state is session-scoped and must not be persisted across app launches.

### Run SQL

When the user clicks `Run SQL`:

1. Read the current editor content
2. Reject empty input
3. Reject multi-statement input
4. Reject missing active database
5. Classify the query risk
6. If blocked by read-only mode:
   - return a user-facing error result
7. If destructive and write mode is enabled:
   - ask for confirmation
8. Execute through `DatabaseManager`
9. Store the normalized result or error in controller state
10. Refresh the `Database` view

## Visual Bug Fix

The current inset card rendering can visibly chip the rounded corners because the inner surface is too tightly layered against the outer rounded frame.

This milestone should fix that rendering issue as part of the same work.

Recommended direction:

- keep the overall inset hierarchy
- adjust inner padding and radius relationship so the corner silhouette remains clean
- simplify the inner-frame treatment if necessary
- prefer a cleaner contour over a stronger inset illusion

The panel fix should apply to all inset `PanelCard` variants, not only the `Database` view.

## Testing and Verification

This milestone should include:

- controller tests for database state transitions
- controller tests for manual database selection persistence
- controller tests for read-only resets on app startup
- core tests for single-statement enforcement if implemented in a pure helper
- view-model tests for the database summary/result contract
- regression tests for the panel surface corner fix if it can be expressed through a pure helper
- full `pytest` regression
- manual desktop verification with `python fesium.py`

Manual verification should cover:

- project database detection
- manual `.sqlite` selection
- read-only toggle behavior
- blocked write query in read-only mode
- destructive query confirmation in write mode
- clean result rendering
- no visible corner-chipping on inset panels

## Risks and Guardrails

- Do not let the manual database choice get silently replaced on project refresh
- Do not persist unsafe write mode across restarts
- Do not let the `DatabaseView` absorb controller or database logic
- Do not introduce multi-statement execution in this milestone
- Do not fix the panel-corner artifact with a visually heavier workaround that harms the overall Graphite Grid hierarchy

## Success Criteria

This milestone is successful when:

- the `Database` view can run one SQLite statement at a time
- `read-only` starts enabled on every launch
- manual database choice persists within the session until explicitly changed
- write queries are blocked in read-only mode with clear feedback
- destructive queries in write mode require confirmation
- results and errors are rendered clearly
- inset panel corners render cleanly without visible missing pieces
