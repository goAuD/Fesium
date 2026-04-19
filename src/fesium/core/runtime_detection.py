from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDecision:
    backend_kind: str
    reason: str


def decide_runtime_backend(profile, php_available: bool) -> RuntimeDecision:
    if php_available:
        return RuntimeDecision(
            backend_kind="php",
            reason=f"php_available_for_{profile.kind}",
        )

    return RuntimeDecision(backend_kind="static", reason="php_unavailable")
