"""Validation for the user-editable Fesium preferences.

Framework-free on purpose. The Settings view renders whatever comes back and
the bootstrap layer is the only thing that writes to Config, so the rules for
what counts as a valid preference live in exactly one place.
"""

from dataclasses import dataclass
from typing import Any

from fesium.core.security import normalize_existing_directory

# Ports below 1024 are privileged on Linux and macOS. Fesium is aimed at
# students on machines they do not administer, so rejecting them here beats a
# permission error at server start.
MIN_PORT = 1024
MAX_PORT = 65535


@dataclass(frozen=True)
class PreferenceResult:
    """Outcome of validating one preference, plus the line to show the user."""

    ok: bool
    value: Any
    message: str


def normalize_port(raw: Any) -> PreferenceResult:
    """Coerce user input into a port a non-root process can bind."""
    try:
        port = int(str(raw).strip())
    except (TypeError, ValueError):
        return PreferenceResult(False, None, f"Port must be a whole number, not {raw!r}")

    if not MIN_PORT <= port <= MAX_PORT:
        return PreferenceResult(
            False,
            None,
            f"Port must be between {MIN_PORT} and {MAX_PORT}",
        )

    return PreferenceResult(True, port, f"Port set to {port}")


def normalize_default_project(raw: Any) -> PreferenceResult:
    """Resolve a default project folder. An empty value clears the preference."""
    candidate = str(raw or "").strip()
    if not candidate:
        return PreferenceResult(True, "", "Default project folder cleared")

    ok, resolved = normalize_existing_directory(candidate)
    if not ok:
        return PreferenceResult(False, None, str(resolved))

    return PreferenceResult(True, str(resolved), f"Default project folder set to {resolved}")


def describe_startup_project(
    *,
    last_project: str,
    default_project: str,
    restore_last_project: bool,
) -> str:
    """Say, in one line, which folder the next launch will open.

    The three preferences interact, and a settings screen that lists them
    without saying what they add up to just moves the guesswork to the user.
    """
    if restore_last_project and last_project:
        return f"Next launch reopens your last project: {last_project}"

    if default_project:
        return f"Next launch opens the default folder: {default_project}"

    return "Next launch opens the folder Fesium is started from"
