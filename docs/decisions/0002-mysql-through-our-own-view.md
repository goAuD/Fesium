# ADR 0002 - Reach MySQL Through Fesium's Own Database View, Not a Bundled Admin Panel

- Status: Accepted
- Date: 2026-08-22
- Superseded by: -

## Context

MySQL support is the one capability asked for by an experienced user rather than inferred from the roadmap. Fesium already detects that a project wants MySQL and reports whether it is reachable; what it cannot do is show the data.

`ROADMAP.md` previously described this as a "phpMyAdmin-style query interface", which reads as *build an admin panel*. Three ways to get there were considered.

**A. Serve an existing admin panel.** Adminer is a single PHP file covering MySQL, MariaDB, PostgreSQL and SQLite. Fesium already runs a PHP server, so this is almost no work: start the server pointed at the file and open a browser. Adminer is actively maintained - 6.0.1 was released on 2026-08-14 - and the AdminerEvo fork that once looked like the successor is the one that has stopped.

**B. Extend the database view we already have.** `src/fesium/core/database.py` is 188 lines. `sqlite3` appears in four places: the connect call, the row factory, the `sqlite_master` table listing and the `pragma_table_info` column lookup. Everything else - the read-only gate, the risk classification, the transaction handling, `validate_table_name`, the result shape the views consume - is engine-neutral already.

**C. Write our own admin panel.** Rejected on inspection. Adminer's size and its CVE history come mostly from being a *web application*: sessions, CSRF, output escaping on every path, authentication. Reproducing that inherits the whole attack surface with none of the scrutiny that a widely deployed tool attracts, in a program handed to students who will point it at real data.

## Decision

**Take route B.** MySQL is reached through Fesium's own `Database` view, over a driver, from the desktop process. No web application is bundled and none is written.

1. **`PyMySQL` is the driver.** Pure Python and MIT licensed, so it installs with no compiler. `mysqlclient` is a C extension and will not build on the locked-down school machine this app exists for, which makes it the wrong dependency regardless of its performance.
2. **A dialect seam, not a rewrite.** `DatabaseManager` keeps the read-only gate, the risk classification and the result shape. Only the four SQLite-specific points move behind an engine boundary: connecting, listing tables (`sqlite_master` versus `information_schema.tables`), describing columns (`pragma_table_info` versus `information_schema.columns`) and the driver's error type.
3. **Identifiers stay validated, values stay bound.** `validate_table_name` applies unchanged, and column lookups use `information_schema` with the table name as a bound parameter - the same posture that `pragma_table_info(?)` gave us on SQLite.
4. **The password is never persisted.** It is asked for per session and kept in memory. `~/.fesium/config.json` gains no secret, and `Diagnostics` continues to read only `DB_CONNECTION`, `DB_HOST`, `DB_PORT` and `DB_DATABASE` from a project's `.env`, which is enough to pre-fill every field except the one that matters.
5. **Read-only stays the default,** resets on every launch, and destructive statements still require confirmation - exactly as for SQLite.

## Consequences

- Fesium will not offer what an admin panel offers: dump import and export, form-based row editing, user and privilege management. That is the price, and it is worth naming rather than discovering later.
- Serving Adminer would have undermined a guardrail the product is built on. Read-only-by-default is a Fesium behaviour; a panel served in a browser has its own rules, and a `DROP TABLE` would sit one click away with nothing of ours in between. Route B keeps every safety property that already applies to SQLite.
- One new runtime dependency. It is pinned in `requirements.txt` like the rest and tracked by Dependabot, which a vendored PHP file would not have been.
- Route A is not forbidden, it is deferred. If the missing admin features turn out to matter, serving Adminer can be added *beside* this rather than instead of it, and this ADR should be amended rather than superseded. Reading Adminer's source to understand an engine's behaviour is fine; copying from it is not, since its licence would then reach into Fesium.
- Route B generalises. The same seam that admits MySQL admits PostgreSQL later at the cost of one more driver, which route A would have given us only by inheriting a whole panel.

## Checklist When This Is Built

- `PyMySQL` pinned in `requirements.txt`, ranged in `pyproject.toml`.
- The engine seam covered by tests that never open a socket, in keeping with a suite that runs without network access.
- A connection failure reported the way `Diagnostics` reports a missing service - in plain words, naming the host and port it tried.
- `docs/dev/conventions.md` updated with the rule that credentials are never written to disk.
