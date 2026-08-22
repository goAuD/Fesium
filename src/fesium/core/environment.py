import logging
import subprocess
import time
from dataclasses import dataclass

from fesium.core.server import get_subprocess_flags

logger = logging.getLogger(__name__)

PHP_PROBE_TIMEOUT_SECONDS = 3.0

# Spawning `php -v` costs about 78ms, and the UI rebuilds its views after every
# action - eleven handlers call refresh_runtime_views(), each of which probed
# again. Measured with cProfile, the probe was 98% of the time spent selecting
# a project, on the main thread, so every click stalled the window for it.
#
# A whole session of caching would be wrong: someone diagnosing a missing PHP
# will install it and look again. Thirty seconds makes a burst of clicks pay
# once while still noticing an install within half a minute, and
# reset_php_cache() makes it immediate when there is a reason to re-check.
PHP_CACHE_SECONDS = 30.0

_cached_status: "EnvironmentStatus | None" = None
_cached_at = 0.0


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


def reset_php_cache() -> None:
    """Force the next summary to probe again."""
    global _cached_status, _cached_at
    _cached_status = None
    _cached_at = 0.0


def summarize_php_environment(*, max_age: float = PHP_CACHE_SECONDS) -> EnvironmentStatus:
    """The app-facing probe, cached.

    ``detect_php`` stays uncached: anything that needs a guaranteed-fresh
    answer, and every test, can still call it directly.
    """
    global _cached_status, _cached_at

    now = time.monotonic()
    if _cached_status is not None and now - _cached_at < max_age:
        return _cached_status

    _cached_status = detect_php()
    _cached_at = now
    return _cached_status
