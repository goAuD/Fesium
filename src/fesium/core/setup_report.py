"""A plain-text summary of this machine, this project, and what is missing.

Written to be pasted. A student who cannot get a project running asks a
teacher, and the exchange that follows is usually five rounds of "what version
of PHP", "where is the project", "is MySQL actually running". Every one of
those answers is already on the Diagnostics screen. This turns them into one
block of text the student can hand over, so the question is answered once.

Two rules shape it.

**No credentials, ever.** Nothing here touches a password. ``DatabaseRequirement``
carries only the connection, host, port and database name, which is what it was
built to carry, so this stays honest by construction rather than by discipline.

**Paths lose the home directory.** A Windows project path contains the account
name, and the whole point of this text is that it gets pasted somewhere - a
group chat, a forum, a ticket. ``~`` says everything the reader needs and
nothing about who the student is.
"""

from __future__ import annotations

import platform
import textwrap
from dataclasses import dataclass
from pathlib import Path

MISSING = "-"
# Wide enough for a path, narrow enough to survive a chat window and a quote
# marker in a reply.
WRAP_WIDTH = 78


@dataclass(frozen=True)
class ReportSection:
    title: str
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SetupReport:
    """The model. ``render_setup_report`` turns it into the pasteable text."""

    sections: tuple[ReportSection, ...]
    actions: tuple[str, ...]


def redact_home(value: str | Path | None, *, home: Path | None = None) -> str:
    """Replace the user's home directory with ``~``.

    Case-insensitively and for either slash, because a path can reach this
    function from a file dialog, from a config file written on another machine,
    or from a string a user typed.
    """
    if not value:
        return MISSING

    text = str(value)
    root = str(home if home is not None else Path.home())
    if not root:
        return text

    for candidate in {root, root.replace("\\", "/"), root.replace("/", "\\")}:
        if text.lower().startswith(candidate.lower()):
            remainder = text[len(candidate):]
            return "~" + remainder.replace("\\", "/")
    return text.replace("\\", "/")


def _runtime_rows(status, *, needs_php: bool, backend: str,
                  home: Path | None = None) -> tuple[tuple[str, str], ...]:
    if not status.php_available:
        php = "Missing from PATH"
    elif needs_php:
        php = "Available"
    else:
        php = "Available, not used by this project"

    return (
        ("PHP", php),
        ("Version", status.php_version or MISSING),
        # A machine can carry several PHP installs and PATH decides which one
        # answers, so the version alone does not identify it.
        # Redacted like any other path: a portable PHP often lives under the
        # user's own folder, and that path carries the account name too.
        ("Binary", redact_home(getattr(status, "path", ""), home=home)),
        ("Serving with", backend or MISSING),
    )


def _database_rows(readiness) -> tuple[tuple[str, str], ...]:
    requirement = getattr(readiness, "requirement", None)
    if requirement is None:
        return (("Configured", "No .env with a DB_CONNECTION was found"),)

    if not requirement.needs_a_server:
        return (
            ("Connection", requirement.connection),
            ("Needs a server", "No - this is a file-backed database"),
        )

    reachable = getattr(readiness, "reachable", None)
    if reachable is True:
        state = "Reachable"
    elif reachable is False:
        state = "NOT reachable - nothing is listening there"
    else:
        state = "Not checked"

    return (
        ("Connection", requirement.connection),
        ("Address", requirement.address or MISSING),
        ("Database", requirement.database or MISSING),
        ("Status", state),
    )


def _actions(status, *, needs_php: bool, project_root, readiness) -> tuple[str, ...]:
    """What to actually do, in the order it has to be done.

    Deliberately imperative. The Diagnostics screen describes a state; someone
    reading this wants the next command.
    """
    steps: list[str] = []

    if project_root is None:
        steps.append("Open a project folder in Fesium - nothing else can be checked until then.")
        return tuple(steps)

    if needs_php and not status.php_available:
        steps.append(
            "Install PHP and make sure it is on PATH, then reopen the project. "
            "Until then this project can only be served as static files.")

    requirement = getattr(readiness, "requirement", None)
    if requirement is not None and requirement.needs_a_server:
        if getattr(readiness, "reachable", None) is False:
            steps.append(
                f"Start the {requirement.connection} server this project expects at "
                f"{requirement.address or 'the address in its .env'}. Fesium serves the "
                "site but does not run a database - without it the first query fails.")

    if not steps:
        steps.append("Nothing is missing. Press Start and open the site in a browser.")
    return tuple(steps)


def build_setup_report(
    status,
    *,
    version: str,
    project_root=None,
    project_kind: str = "",
    document_root=None,
    needs_php: bool = True,
    backend: str = "",
    port: int | None = None,
    readiness=None,
    home: Path | None = None,
) -> SetupReport:
    """Collect what a teacher would otherwise have to ask for, one question at a time."""
    system = (
        ("Fesium", version),
        ("Operating system", f"{platform.system()} {platform.release()}".strip() or MISSING),
        ("Python", platform.python_version()),
    )

    if project_root is None:
        project = (("Folder", "No project selected"),)
    else:
        project = (
            ("Folder", redact_home(project_root, home=home)),
            ("Detected as", project_kind.title() if project_kind else MISSING),
            ("Document root", redact_home(document_root, home=home)),
            ("Needs PHP", "Yes" if needs_php else "No"),
            ("Port", str(port) if port else MISSING),
        )

    sections = [
        ReportSection("System", system),
        ReportSection("Runtime", _runtime_rows(status, needs_php=needs_php,
                                               backend=backend, home=home)),
        ReportSection("Project", project),
    ]
    if readiness is not None:
        sections.append(ReportSection("Database", _database_rows(readiness)))

    return SetupReport(
        sections=tuple(sections),
        actions=_actions(status, needs_php=needs_php, project_root=project_root,
                         readiness=readiness),
    )


def render_setup_report(report: SetupReport) -> str:
    """Render as plain text, aligned, ready to paste into a chat or an email.

    Not Markdown: half the places this lands render it as literal asterisks,
    and a teacher reading it on a phone should not have to decode formatting.
    """
    width = max(
        (len(label) for section in report.sections for label, _ in section.rows),
        default=0)

    lines: list[str] = ["Fesium setup report", "=" * 19, ""]
    for section in report.sections:
        lines.append(section.title)
        for label, value in section.rows:
            lines.append(f"  {label.ljust(width)}  {value}")
        lines.append("")

    lines.append("What to do")
    for step in report.actions:
        # Wrapped with a hanging indent: unwrapped these run past 130
        # characters, which a chat window hides and an email client folds in
        # the middle of a path.
        lines.extend(textwrap.wrap(
            step, width=WRAP_WIDTH, initial_indent="  - ", subsequent_indent="    "))
    lines.append("")
    # Two sentences, two lines: wrapping them as one prose block split the
    # reassurance across a line break, which is the one part a nervous
    # student is most likely to read on its own.
    lines.append("Paths are shortened to ~ so this can be shared safely.")
    lines.append("No passwords are included.")
    return "\n".join(lines)
