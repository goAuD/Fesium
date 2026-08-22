from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDecision:
    backend_kind: str
    reason: str


def decide_runtime_backend(profile, php_available: bool) -> RuntimeDecision:
    """Pick a backend from what the project needs, not from what is installed.

    This used to return PHP whenever PHP was on the machine, using the profile
    only to build the reason string. A plain HTML and JavaScript site was
    therefore served by a PHP process it had no use for, and the static server
    was only ever a fallback - which contradicted the Guide, where static
    hosting is described as a first-class workflow rather than a fallback.
    """
    if not getattr(profile, "needs_php", True):
        return RuntimeDecision(backend_kind="static", reason=f"no_php_needed_for_{profile.kind}")

    if php_available:
        return RuntimeDecision(backend_kind="php", reason=f"php_available_for_{profile.kind}")

    return RuntimeDecision(backend_kind="static", reason="php_unavailable")
