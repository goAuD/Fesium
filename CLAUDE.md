# Fesium - Claude Code Guide

Product direction, architecture, design and security guardrails live in [AGENTS.md](AGENTS.md). Read that first; this file only adds what an agent working in this repo needs on top of it.

## Commands

```bash
python -m pip install -r requirements.txt   # runtime + contributor deps, single file
python fesium.py                            # run from a clone
python -m pytest -q                         # full suite, headless, no PHP, no network
python -m ruff check .                       # lint, must be clean before commit
```

Installed instead of cloned: `python -m pip install -e .` gives a `fesium` console script and `python -m fesium`.

## Verification bar

The suite is deliberately display-free, so it cannot see a layout bug. **Do not eyeball UI changes and call them done.** Drive the real widgets in a live Tk window and assert on measurements:

```python
shell.update_idletasks(); shell.update()
label._label.winfo_reqwidth() > label.winfo_width()   # text is being clipped
```

Two habits that have already caught real bugs here:

- Run the same measurement against the pre-change code (`git worktree add --detach <tmp> HEAD`) to prove the check is not vacuous.
- Smoke-test startup by running the real `bootstrap.main()` with `FesiumShell.mainloop` patched and `build_default_paths` pointed at a temp dir, so `~/.fesium` is never touched.

## Traps specific to this codebase

- **`fesium.py` shares its name with the `src/fesium/` package.** Anything doing `import fesium` from the repo root gets the launcher, not the package. The launcher declares `__path__` to bridge that. Never make it `exec()` source again - `fesium._version` exists so a plain import does the job.
- **`CTkLabel` needs `wraplength` in pixels.** A constant is only right at one window size and clips text at every smaller one. Paragraphs go through `ui/widgets/BodyText`, gridded `sticky="ew"`.
- **`CTkLabel.bind()` forwards to the inner canvas and label, not the frame.** For the widget's own size, use `tkinter.Frame.bind(self, ..., add="+")` - and always `add="+"`, because CustomTkinter binds `<Configure>` for itself.
- **Never pair a corner radius with a border.** CustomTkinter draws the corner as an anti-aliased circle glyph and the edges as hard-edged rectangles; they do not line up, and the corner reads as doubled. `SHAPE_TOKENS` holds the decision and a test enforces it.
- **Nothing inside a tile gets a fixed pixel height.** `CTkTextbox` requests 200px by default. Three stacked exceed the window, grid stops applying row weights, and the tile that should be largest is the one that clips. Ask for little and let `row_weight` decide.
- **setuptools ships no non-Python file unless declared.** The bundled fonts and icons are `[tool.setuptools.package-data]`. If you add an asset, add it there, or an installed Fesium starts without it.
- **The floor is Python 3.10**, because `X | None` annotations are built at import time. CI runs 3.10 so the claim stays tested. Do not raise or lower it without changing `pyproject.toml`, the docs and the matrix together - a contract test checks all three agree.
- **SQLite cannot bind an identifier.** A table name in a `FROM` clause has to be validated (`validate_table_name`); everywhere else uses bound parameters, including schema inspection via `pragma_table_info(?)`.

## House style

- Plain ASCII punctuation. Write `-`, never an em dash, in docs, docstrings, comments, commit messages and PR bodies.
- Keep pure, testable functions out of the widget classes. Views build a model (`build_database_summary`, `build_settings_model`) that the suite can test without a display.
- Update `README.md`, `CHANGELOG.md` and `ROADMAP.md` when behaviour changes. The repo has drifted before by shipping work the changelog denied.

## Git

Work on a branch, commit per finished piece of work, open a **draft** PR and let the repo owner merge it. Commit messages say what was wrong and how it was verified, not just what changed.
