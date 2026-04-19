from urllib.parse import urlsplit

import webbrowser


def open_local_url(url: str) -> bool:
    if not url:
        return False

    parsed = urlsplit(url)
    if parsed.scheme != "http":
        return False

    if parsed.username is not None or parsed.password is not None:
        return False

    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return False

    try:
        port = parsed.port
    except ValueError:
        return False

    if port is None:
        return False

    return bool(webbrowser.open(url))
