from dataclasses import dataclass
import subprocess

from fesium.core.server import check_php_installed, get_subprocess_flags


@dataclass(frozen=True)
class EnvironmentStatus:
    php_available: bool
    php_version: str
    summary: str


def get_php_version() -> str:
    try:
        result = subprocess.run(
            ["php", "-v"],
            capture_output=True,
            text=True,
            **get_subprocess_flags(),
        )
    except FileNotFoundError:
        return ""

    if result.returncode != 0 or not result.stdout:
        return ""
    return result.stdout.splitlines()[0]


def summarize_php_environment() -> EnvironmentStatus:
    if not check_php_installed():
        return EnvironmentStatus(False, "", "PHP not found in PATH")

    version = get_php_version()
    return EnvironmentStatus(True, version, version or "PHP available")
