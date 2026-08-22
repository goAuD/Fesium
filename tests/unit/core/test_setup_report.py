from dataclasses import fields
from pathlib import Path

import pytest

from fesium.core.environment import EnvironmentStatus
from fesium.core.project_database import DatabaseReadiness, DatabaseRequirement
from fesium.core.setup_report import (
    build_setup_report,
    redact_home,
    render_setup_report,
)

HOME = Path("C:/Users/agnes")
READY_PHP = EnvironmentStatus(
    php_available=True, php_version="PHP 8.5.2 (cli)",
    summary="PHP 8.5.2 (cli)", path="C:/php/php.exe")
NO_PHP = EnvironmentStatus(
    php_available=False, php_version="", summary="PHP not found", path="")


def report_text(**kwargs):
    defaults = {"version": "2.1.0", "home": HOME}
    defaults.update(kwargs)
    return render_setup_report(build_setup_report(**defaults))


# -- redaction ---------------------------------------------------------------

@pytest.mark.parametrize("raw", [
    "C:/Users/agnes/Projects/portal",
    "C:\\Users\\agnes\\Projects\\portal",
    "c:/users/AGNES/Projects/portal",
])
def test_redact_home_hides_the_account_name(raw):
    """The account name is the leak, and a Windows path always carries it.

    This text exists to be pasted into a group chat or a ticket, so the path
    has to say where the project is without saying who the student is.
    """
    assert redact_home(raw, home=HOME) == "~/Projects/portal"


def test_redact_home_leaves_a_path_outside_home_alone():
    assert redact_home("D:/GitHub/Fesium", home=HOME) == "D:/GitHub/Fesium"


def test_redact_home_handles_nothing_to_redact():
    assert redact_home("", home=HOME) == "-"
    assert redact_home(None, home=HOME) == "-"


def test_rendered_report_never_contains_the_home_directory():
    text = report_text(
        status=READY_PHP,
        project_root=HOME / "Projects" / "portal",
        project_kind="laravel",
        document_root=HOME / "Projects" / "portal" / "public",
        needs_php=True, backend="php", port=8000)

    assert "agnes" not in text.lower()
    assert "~/Projects/portal" in text


# -- credentials -------------------------------------------------------------

def test_the_requirement_this_report_prints_carries_no_credential():
    """Safe by construction rather than by remembering.

    The report prints a DatabaseRequirement. As long as that type has no field
    for a user or a password, no future edit to the report can leak one.
    """
    names = {field.name for field in fields(DatabaseRequirement)}

    assert names == {"connection", "host", "port", "database"}


def test_report_states_that_it_is_safe_to_share():
    text = report_text(status=READY_PHP, project_root=HOME / "site", needs_php=False)

    assert "No passwords are included." in text


# -- what to do --------------------------------------------------------------

def test_without_a_project_the_only_advice_is_to_open_one():
    report = build_setup_report(NO_PHP, version="2.1.0", home=HOME)

    assert report.actions == (
        "Open a project folder in Fesium - nothing else can be checked until then.",)


def test_a_php_project_without_php_is_told_to_install_it():
    report = build_setup_report(
        NO_PHP, version="2.1.0", home=HOME,
        project_root=HOME / "portal", project_kind="laravel", needs_php=True)

    assert any("Install PHP" in step for step in report.actions)


def test_a_static_project_is_not_told_to_install_php():
    """A project that never touches PHP has no PHP problem to report."""
    report = build_setup_report(
        NO_PHP, version="2.1.0", home=HOME,
        project_root=HOME / "site", project_kind="standard", needs_php=False)

    assert not any("Install PHP" in step for step in report.actions)


def test_an_unreachable_database_names_the_address_and_the_reason():
    readiness = DatabaseReadiness(
        requirement=DatabaseRequirement(
            connection="mysql", host="127.0.0.1", port=3306, database="portal"),
        reachable=False)

    report = build_setup_report(
        READY_PHP, version="2.1.0", home=HOME, project_root=HOME / "portal",
        project_kind="laravel", needs_php=True, readiness=readiness)

    advice = " ".join(report.actions)
    assert "127.0.0.1:3306" in advice
    assert "does not run a database" in advice


def test_a_sqlite_project_is_not_told_to_start_a_server():
    readiness = DatabaseReadiness(
        requirement=DatabaseRequirement(
            connection="sqlite", host="", port=None, database="database.sqlite"),
        reachable=None)

    report = build_setup_report(
        READY_PHP, version="2.1.0", home=HOME, project_root=HOME / "portal",
        project_kind="laravel", needs_php=True, readiness=readiness)

    assert not any("Start the" in step for step in report.actions)


def test_a_ready_setup_says_so_rather_than_listing_nothing():
    """An empty What-to-do section reads like the check failed to run."""
    report = build_setup_report(
        READY_PHP, version="2.1.0", home=HOME, project_root=HOME / "portal",
        project_kind="laravel", needs_php=True, backend="php", port=8000)

    assert report.actions == ("Nothing is missing. Press Start and open the site in a browser.",)


# -- shape -------------------------------------------------------------------

def test_report_carries_the_sections_a_teacher_would_otherwise_ask_for():
    readiness = DatabaseReadiness(
        requirement=DatabaseRequirement(
            connection="mysql", host="127.0.0.1", port=3306, database="portal"),
        reachable=True)

    report = build_setup_report(
        READY_PHP, version="2.1.0", home=HOME, project_root=HOME / "portal",
        project_kind="laravel", needs_php=True, backend="php", port=8000,
        readiness=readiness)

    assert [section.title for section in report.sections] == [
        "System", "Runtime", "Project", "Database"]


def test_database_section_is_omitted_when_nothing_was_probed():
    report = build_setup_report(
        READY_PHP, version="2.1.0", home=HOME, project_root=HOME / "site",
        project_kind="standard", needs_php=False)

    assert "Database" not in [section.title for section in report.sections]


def test_advice_is_wrapped_so_it_survives_being_pasted():
    """Unwrapped, these run past 130 characters and fold in the middle of a path."""
    text = report_text(
        status=NO_PHP, project_root=HOME / "portal", project_kind="laravel",
        needs_php=True)

    assert max(len(line) for line in text.splitlines()) <= 78
    # The continuation lines still read as part of the same step.
    assert any(line.startswith("    ") for line in text.splitlines())


def test_rendered_report_names_the_binary_that_answered():
    """A machine can carry several PHP installs and PATH decides which one."""
    text = report_text(status=READY_PHP, project_root=HOME / "portal", needs_php=True)

    assert "C:/php/php.exe" in text


def test_a_php_living_under_the_home_folder_is_redacted_too():
    """A portable PHP is usually unzipped into the user's own folder.

    That path carries the account name exactly like the project path does, and
    it reaches the report through a different argument, so it needs its own
    check rather than relying on the project path being covered.
    """
    portable = EnvironmentStatus(
        php_available=True, php_version="PHP 8.5.2 (cli)", summary="",
        path=str(HOME / "Downloads" / "php" / "php.exe"))

    text = report_text(status=portable, project_root=HOME / "portal", needs_php=True)

    assert "agnes" not in text.lower()
    assert "~/Downloads/php/php.exe" in text
