from fesium.core.browser import open_local_url


def test_open_local_url_rejects_empty_urls(monkeypatch):
    called = []
    monkeypatch.setattr("fesium.core.browser.webbrowser.open", lambda url: called.append(url))

    assert open_local_url("") is False
    assert called == []


def test_open_local_url_opens_valid_localhost_url(monkeypatch):
    called = []
    monkeypatch.setattr(
        "fesium.core.browser.webbrowser.open",
        lambda url: called.append(url) or True,
    )

    assert open_local_url("http://localhost:8000") is True
    assert called == ["http://localhost:8000"]


def test_open_local_url_rejects_spoofed_userinfo_url(monkeypatch):
    called = []
    monkeypatch.setattr(
        "fesium.core.browser.webbrowser.open",
        lambda url: called.append(url) or True,
    )

    assert open_local_url("http://localhost:8000@evil.com") is False
    assert called == []


def test_open_local_url_allows_loopback_ipv4_url(monkeypatch):
    called = []
    monkeypatch.setattr(
        "fesium.core.browser.webbrowser.open",
        lambda url: called.append(url) or True,
    )

    assert open_local_url("http://127.0.0.1:8000") is True
    assert called == ["http://127.0.0.1:8000"]
