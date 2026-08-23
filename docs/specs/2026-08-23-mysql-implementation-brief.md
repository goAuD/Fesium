# MySQL Implementation Brief

- Date: 2026-08-23
- Implements: [ADR 0002](../decisions/0002-mysql-through-our-own-view.md)
- Audience: whoever writes this, in whatever session. Written to be re-read.

## Why this file exists

The decision is settled, and the work is large enough that a single session can lose track of
it. This is the durable version: read it before starting, and read it again if you have lost
the thread. It is not a discussion. Where it disagrees with your memory of the task, it wins.

## What is already true

Read these before changing anything.

- `src/fesium/core/database.py` (188 lines) is SQLite-specific end to end. `DatabaseManager`
  opens a connection per query, gates writes with `is_read_query`, and returns a fixed result
  shape that the views consume.
- `src/fesium/core/project_database.py` already reads a project's `.env` and knows what
  database it wants. `DatabaseRequirement` carries `connection`, `host`, `port` and
  `database` - and deliberately no credentials. `probe_database()` answers "is anything
  listening there" with a 0.75s TCP connect.
- `src/fesium/app/controller.py` holds `ControllerState`, a frozen dataclass, and builds a
  `DatabaseManager` per action.
- `src/fesium/ui/views/database_view.py` keeps its logic in pure functions
  (`build_database_summary`, `build_database_result_view_model`) that the suite tests without
  a display. Follow that pattern; do not put testable logic in a widget.
- The suite is `347 passed, 1 skipped`. It runs headless, with no PHP and no network.

The SQLite coupling is wider than ADR 0002 claims. It says four places; there are five.

| # | Location | What is SQLite-specific |
|---|---|---|
| 1 | `database.py:85-86` | `sqlite3.connect` and `sqlite3.Row` |
| 2 | `database.py:140` | `except sqlite3.Error` |
| 3 | `database.py:156-160` | the `sqlite_master` table listing |
| 4 | `database.py:174-177` | `pragma_table_info(?)` and the row shape it returns |
| 5 | `database.py:111` | `os.path.exists(self.db_path)` - a MySQL target is not a file |

## The seam

One new flat module. This repository has no subpackages under `core/`; do not introduce one.

```
core/database.py          DatabaseManager, is_read_query, validate_table_name,
                          build_table_preview_query   - engine-neutral, delegates
core/database_engines.py  the DatabaseEngine protocol, SqliteEngine, MySQLEngine
```

`DatabaseManager` keeps the read-only gate, the risk classification, the transaction handling
and the result shape. The engine owns everything in the table below, and nothing else.

| Concern | SQLite | MySQL |
|---|---|---|
| connect | `sqlite3.connect(path)` | `pymysql.connect(...)`, imported lazily |
| availability | the file exists | the driver imports, the host answers |
| placeholder | `?` | `%s` |
| list tables | `sqlite_master`, skipping `sqlite_*` | `information_schema.tables`, current schema |
| describe columns | `pragma_table_info(?)` | `information_schema.columns`, table name bound |
| error type | `sqlite3.Error` | `pymysql.MySQLError` |
| identifier quoting | bare name | backticks |
| read verbs | `SELECT PRAGMA EXPLAIN WITH` | `SELECT SHOW DESCRIBE DESC EXPLAIN WITH` |
| extra write verbs | - | `REPLACE CALL GRANT REVOKE CREATE RENAME TRUNCATE LOAD` |

The pattern in `validate_table_name` applies unchanged on both engines. It is a deliberately
narrow subset that sidesteps most quoting questions. Do not widen it.

## Constraints that are not negotiable

These are the product's guardrails. A change that breaks one of them is wrong even if every
test passes.

1. **The password never reaches disk, and never enters `ControllerState`.** That dataclass is
   frozen, gets replaced constantly, and can be repr'd into a log. Hold the password in a
   private attribute on the controller, for the session only. Write a test asserting that no
   state field and no repr carries it.
2. **`DatabaseRequirement` gains no user or password field.** A test in
   `tests/unit/core/test_setup_report.py` pins that it has none. That test is the guardrail,
   not an obstacle. Connection settings are a separate structure.
3. **The whitelist in `project_database.py` stays exactly `DB_CONNECTION`, `DB_HOST`,
   `DB_PORT`, `DB_DATABASE`.** Fesium has never read a credential out of a `.env`, and does
   not start now.
4. **`~/.fesium/config.json` gains no secret.**
5. **No test opens a network connection.** `MySQLEngine` takes its connector as an injectable
   argument defaulting to `pymysql.connect`, so the suite hands it a fake. This is the single
   most important testability decision in the work - get it wrong and the tests either hit a
   socket or do not exist.
6. **A dead host must not freeze the UI.** Use the existing `probe_database()` as a fast
   pre-check before attempting a connection, and set PyMySQL's connect timeout besides. Every
   socket operation in this repository has a timeout, enforced by a test.
7. **Read-only, twice over.** Keyword classification is what enforces read-only today. On
   MySQL, also issue `SET SESSION TRANSACTION READ ONLY` after connecting when read-only is
   on. Keyword gating alone is trivially bypassed on a dialect it does not know.

## The four stages

Each stage ends with `python -m pytest -q`, then `python -m ruff check .`, then one commit.
Never begin stage N+1 before stage N is committed and green. If you are running out of room,
stop at a committed stage and say where you stopped and what comes next - that is a planned
outcome, not a failure. An abandoned uncommitted refactor is the failure.

### Stage 1 - the engine seam, with zero behaviour change

Create `core/database_engines.py` with the protocol and `SqliteEngine`. Move all five
SQLite-specific points behind it. `DatabaseManager` delegates.

**Do not edit any existing test.** The proof that this stage is correct is that the suite
still reads `347 passed, 1 skipped` against tests nobody touched. If an existing test fails,
the refactor is wrong; the test is not.

### Stage 2 - the PyMySQL engine

`MySQLEngine` behind the same protocol: `%s` placeholders, backtick quoting,
`information_schema` lookups with the table name bound, the MySQL verb sets, the read-only
session, a bounded connect timeout, and the injectable connector.

Pin `PyMySQL` in `requirements.txt` at an exact version, like every other line there, and
range it in `pyproject.toml`. Import it inside the method that connects, never at module
level, so a SQLite-only user never needs it installed.

New tests use a fake connection object. None of them open a socket.

### Stage 3 - controller and state

Connection settings, connect and disconnect, and the password held in memory for the session.
A failure is reported the way `Diagnostics` reports a missing service: plain words, naming the
host and port it tried, and no stack trace.

### Stage 4 - the UI, then the docs

A connection form in the `Database` view, its content built by a pure
`build_connection_form_model(...)` beside `build_database_summary`, so the suite can test it
headless. Pre-fill host, port, database and user from `detect_database_requirement()`, and ask
for the password per session.

Then the documentation, in one commit: `README.md`, `CHANGELOG.md` under `Unreleased`, the
`ROADMAP.md` boxes ticked, the credentials rule added to `docs/dev/conventions.md` as ADR 0002
asks for, and an amendment line on ADR 0002 recording the read-only session decision.

## Out of scope, deliberately

Dump import and export, form-based row editing, and user or privilege management. ADR 0002
names these as the price of not bundling an admin panel. Do not add them.

## How this will be checked

Expect all of it.

- Four commits, one per stage, in order.
- The stage 1 commit shows an empty `git diff --stat HEAD~1 -- tests/`.
- `import sqlite3` and `import pymysql` appear in `database_engines.py` and nowhere else under
  `src/`, and the `pymysql` one is inside a function.
- Nothing on `ControllerState` holds a password, and `~/.fesium/config.json` is byte-identical
  after a session that connected.
- A wrong host fails fast, in a sentence naming the host and port.
- `python scripts/check_layout.py` passes with the new form. The display-free suite cannot see
  a layout bug, and a new set of input fields is exactly where one hides.
