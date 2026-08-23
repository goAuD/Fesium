# Security review: the local server (ox-alpha, 2026-08-23)

**Status: every finding below is closed.** The fixes landed as separate commits, each revertible on its own, and the code they describe is in `static_server.py`, `server.py` and `assets/php/router.php`. The review is kept as written, before the fixes, because what was wrong is worth more than a note saying it no longer is.

Scope: `src/fesium/core/static_server.py`, `src/fesium/core/server.py`, `src/fesium/core/browser.py`, and document-root validation in `src/fesium/core/security.py` and `src/fesium/app/controller.py`.

Method: static reading, checked against how the standard library's `http.server` behaves - `SimpleHTTPRequestHandler.translate_path` in particular. No runtime exploit was run for this document; the fixes were separately verified against a live server afterwards.

Threat model: a localhost-only development server with no public exposure. Authentication, HTTPS, rate limiting and third-party dependencies are deliberately not proposed.

---

## Findings, worst first

| # | Finding | Where | Risk |
| --- | --- | --- | --- |
| 1 | Double-decoding bypass (`%252E`) | `static_server.py:31` against the stdlib's `translate_path` | High |
| 2 | PHP backend has no dot-file filter at all | `server.py:133` | High |
| 3 | DNS rebinding: no Host header check | `static_server.py:70-97` | Medium |
| 4 | Symlinks and junctions lead out of the root | `static_server.py:78-82` | Medium |
| 5 | Windows 8.3 short names, volume dependent | `static_server.py:32` | Medium to low |
| 6 | NTFS alternate data streams (`::$DATA`) | a variant of #1 | Closes with #1 |

---

## A) Yes, `is_hidden_path()` can be bypassed

### A1. Double URL-encoding - the bypass that matters most

- **Where:** `static_server.py:31` unquotes once. `SimpleHTTPRequestHandler.translate_path`, reached through `super().send_head()` at lines 78-82, unquotes again on its own.
- **The problem:** two decoding passes, one check. The check runs against the first pass and the filesystem sees the second.
- **Attacker input:** `GET /%252Eenv`, or `GET /%252Egit/config`
  - `is_hidden_path()` sees `%2Eenv` after one decode. That does not start with a dot, so it passes.
  - `translate_path` decodes again, gets `.env`, and **the file is served**.
- **Impact:** the whole of `.env` and the whole `.git` tree become readable - exactly what the filter was written to prevent, as its own docstring at lines 20-26 says.
- **Risk:** high in this threat model. No network attacker is needed. A page in a browser tab reaches it through DNS rebinding (see C), and so does an `<img src="/%252Eenv">` on a page the project itself serves.
- **Suggested fix:** unquote repeatedly until the string stops changing, or refuse a segment that still contains a `%` after decoding.

### A2. NTFS alternate data streams - through the same bypass

- **Where:** `static_server.py:31-32`. Neither `$DATA` nor the colon appears in the filter, but `/.env::$DATA` on its own is already blocked, because the segment starts with a dot.
- **Attacker input:** `GET /%252Eenv::$DATA` reaches the content stream of `.env` through the A1 bypass.
- **Risk:** medium, and effectively a variant of A1. Fixing A1 closes it.

### A3. Windows 8.3 short names - a separate bypass, no encoding needed

- **Where:** `static_server.py:32` looks only at the text of the path, and `GIT~1` contains no dot.
- **Attacker input:** `GET /GIT~1/config`, the short name of `.git`, on any volume where 8.3 name generation is on. That is the default on SMB shares and older Windows volumes, and off on many modern systems.
- **Risk:** medium, and platform dependent. It cannot be defended against at the level of text alone. The realistic mitigation is to `resolve()` the requested path and then check whether any segment of the real name starts with a dot - or to document the limit.

### A4. Symbolic links and junctions - out of the root entirely

- **Where:** `static_server.py:78-82` checks text only. `translate_path` and `open` follow the link without asking where it lands.
- **Attacker input:** not HTTP input but **project content**: a cloned repository containing `link -> /home/user`, or a Windows junction to `C:\Users\xxx\documents`. Then `GET /link/.ssh/id_rsa`.
- **Scenario:** a student clones a malicious "practice" repository and serves it with Fesium. Any file on their machine becomes readable.
- **Risk:** medium. Fix: `Path.resolve()` the translated path and check it is still under the document root. That also covers part of A3.

### What turned out not to be a problem, checked

- **`..` segments:** `translate_path` runs `normpath` **after** the final decode and clamps back to the root, so the classic `../../../etc/passwd` never leaves it. Fine.
- **Backslashes:** the `replace("\\", "/")` at line 32 covers them, and the stdlib's own `dirname(word)` filtering catches the mixed forms. Fine.
- **Unicode normalisation:** the dot (U+002E) survives normalisation unchanged, and the filesystem does not map the fullwidth variants onto `.`. Not exploitable.

## B) Can anything outside the document root be served, given the `send_head` override?

Two channels:

1. **Symlinks and junctions** (A4). This is the only genuine "outside the root" vector.
2. Double decoding (A1) reaches hidden files **inside** the root. It does not get out of it.

`list_directory` (lines 84-91) and `render_no_index_page` (lines 35-67) are sound in themselves: every interpolated value is passed through `html.escape`, so there is no XSS on the 404 page.

## C) Binding to `127.0.0.1`

- `static_server.py:133` and `server.py:133` really do listen only on the IPv4 loopback and are not reachable from a network interface. Correct in that sense.
- **Where exposure remains anyway:**
  1. **Other users and processes on the same machine** - a lab machine, a shared workstation. Every local account can reach the loopback. Combined with the A1 bypass, that means another user can read the `.env`.
  2. **DNS rebinding**, the important remote vector. A malicious site points `evil.com` at `127.0.0.1` and can then `fetch` the server from that same origin, because the browser's same-origin policy considers the origin to match. Ports 8000 to 8009 are easy to guess. **Fix, with no dependency:** check the Host header in `ProjectFileHandler.send_head` - a rebinding request carries the attacker's domain there, not `127.0.0.1:{port}`. A few lines, no library. On the PHP server this vector stays open, since the headers are not ours to handle there.
  3. Peripheral: with WSL2 mirrored networking or a published Docker port, a server run inside a container can leak to the host. Worth a line in the documentation rather than code.

## D) Yes, `php -S 127.0.0.1:PORT -t docroot` serves things it should not

- **Where:** `src/fesium/core/server.py:133`. There is no router script, so the PHP built-in server does **raw static serving**, with no filtering of dot-files. This is documented PHP behaviour.
- **Attacker input:** a plain `GET /.env` or `GET /.git/config`. No encoding trick is needed, because there is no filter to get around.
- **Impact:** the same data `ProjectFileHandler` was written to protect is freely readable by switching to the PHP backend. The two backends therefore offer inconsistent security.
- **Risk:** high relative to this project's own goals, because the most obvious request there is works.
- **Suggested fix:** a small bundled `router.php` as the fourth argument to `php -S`, applying the same logic as `is_hidden_path` and returning `false` for everything else so the built-in handler takes it. No new dependency.

## E) `browser.py` URL validation - sound, with small notes

- `src/fesium/core/browser.py:10` allows only the `http` scheme, so `file://` and `javascript:` are blocked. Good.
- `:13` the userinfo check catches the `http://127.0.0.1@evil.com/` trick. Good.
- `:16` the hostname allowlist is `localhost` and `127.0.0.1`. `[::1]` is refused, which is consistent with binding IPv4 only. Good.
- `:19-22` handling `ValueError` from `parsed.port` catches invalid ports. Good.
- A note rather than a vulnerability: the allowlist is stricter than it needs to be, since `127.0.0.2` through `127.255.255.254` are loopback too. A stricter allowlist is the right direction for security, and these URLs are generated internally from `LOOPBACK` plus a port, so this layer is defence in depth. Fine as it stands.

---

## Suggested order of work

1. **#1** - a stabilising unquote loop in `is_hidden_path`, about three lines, plus unit tests for `%252E`, `%252Egit/config` and `%252Eenv::$DATA`.
2. **#3** - the Host header check in `ProjectFileHandler`, about ten lines, plus a test with a foreign Host.
3. **#2** - a small `router.php` on the `PHPServer` command line, with the same dot-file logic.
4. **#4** - `resolve()` plus a document-root prefix check in `send_head`, which also covers part of A3.
5. **#5** - document the limit, or let the resolve-based check from #4 handle it.

---

## What was done, and what was checked afterwards

All five were implemented. The remaining limit, recorded rather than fixed: 8.3 short names cannot be defended against as text, and the `resolve()` check from #4 covers them only on volumes where resolving expands them.

The fixes were then attacked against a running server rather than read: 35 vectors including `/%252Eenv`, `/%25252Eenv`, `/%252Egit/config`, `/sub/%252Eenv`, `/GIT~1/config`, `/.env::$DATA`, `/.env%00.html`, `/%2E%2E/outside.txt` and a symlink out of the root. None returned anything. Foreign Host headers are refused, and the PHP backend now blocks the same set while still serving `index.php`.

One check worth naming because a router script could easily have broken it: front-controller routing still works. The built-in server was compared with and without `router.php` on the same tree, and `/users/42` still reaches `index.php`, so Laravel projects are unaffected.
