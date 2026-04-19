import webbrowser


def open_local_url(url: str) -> bool:
    if not url:
        return False

    if not url.startswith("http://localhost:") and not url.startswith("http://127.0.0.1:"):
        return False

    return bool(webbrowser.open(url))
