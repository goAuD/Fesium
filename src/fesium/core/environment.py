from dataclasses import dataclass
import logging
import subprocess

from fesium.core.server import get_subprocess_flags


logger = logging.getLogger(__name__)

PHP_PROBE_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class EnvironmentStatus:
    php_available: bool
    php_version: str
    summary: str


def detect_php(timeout: float = PHP_PROBE_TIMEOUT_SECONDS) -> EnvironmentStatus:
    """Probe the local PHP installation once, with a hard subprocess timeout.

    A slow or hanging `php` binary used to freeze the UI because two separate
    probes (`check_php_installed` + `get_php_version`) were chained. This is
    the single probe that both callers now share.
    """
    try:
        result = subprocess.run(
            ["php", "-v"],
            capture_output=True,
            text=True,
            timeout=timeout,
            **get_subprocess_flags(),
        )
    except FileNotFoundError:
        logger.warning("PHP not found in PATH")
        return EnvironmentStatus(False, "", "PHP not found in PATH")
    except subprocess.TimeoutExpired:
        logger.warning("PHP probe timed out after %.1fs", timeout)
        return EnvironmentStatus(False, "", f"PHP probe timed out after {timeout:.1f}s")

    if result.returncode != 0 or not result.stdout:
        return EnvironmentStatus(False, "", "PHP returned a non-zero exit status")

    version = result.stdout.splitlines()[0]
    logger.info("PHP found: %s", version)
    return EnvironmentStatus(True, version, version)


def summarize_php_environment() -> EnvironmentStatus:
    return detect_php()
