"""Cookie loading from files, raw headers, and installed browsers."""

import http.cookies
from pathlib import Path

import requests

from .exceptions import ZingMp3Error


def load_cookie_argument(session: requests.Session, value: str) -> None:
    """Load a Netscape jar or raw Cookie header from a path or literal value."""
    path = Path(value).expanduser()
    content = path.read_text(encoding="utf-8-sig") if path.is_file() else value

    if _load_netscape_cookies(session, content):
        return
    if _load_raw_cookie_header(session, content):
        return
    raise ZingMp3Error("Could not parse a Netscape cookie jar or Cookie header")


def _load_netscape_cookies(session: requests.Session, content: str) -> int:
    loaded = 0
    for line in content.splitlines():
        cookie_line = line.strip()
        if cookie_line.startswith("#HttpOnly_"):
            cookie_line = cookie_line[len("#HttpOnly_") :]
        elif not cookie_line or cookie_line.startswith("#"):
            continue
        columns = cookie_line.split("\t")
        if len(columns) < 7:
            continue
        domain, _, path, secure, _, name, value = columns[:7]
        session.cookies.set(
            name,
            value,
            domain=domain,
            path=path or "/",
            secure=secure.upper() == "TRUE",
        )
        loaded += 1
    return loaded


def _load_raw_cookie_header(session: requests.Session, content: str) -> int:
    raw_cookie = " ".join(
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.startswith("#")
    )
    if raw_cookie.lower().startswith("cookie:"):
        raw_cookie = raw_cookie.split(":", 1)[1].strip()

    parsed = http.cookies.SimpleCookie()
    parsed.load(raw_cookie)
    for morsel in parsed.values():
        session.cookies.set(morsel.key, morsel.value, domain=".zingmp3.vn", path="/")
    return len(parsed)


def load_browser_cookies(session: requests.Session, value: str) -> None:
    """Load Zing MP3 cookies through browser-cookie3."""
    try:
        import browser_cookie3
    except ImportError as error:
        raise ZingMp3Error(
            "--cookies-from-browser requires browser-cookie3; "
            "run: pip install browser-cookie3"
        ) from error

    browser, separator, cookie_file = value.partition(":")
    browser = browser.strip().lower().replace("-", "_")
    aliases = {"msedge": "edge", "opera-gx": "opera_gx"}
    loader = getattr(browser_cookie3, aliases.get(browser, browser), None)
    if not callable(loader):
        supported = (
            "brave, chrome, chromium, edge, firefox, opera, opera_gx, safari, vivaldi"
        )
        raise ZingMp3Error(
            f"Unsupported browser {browser!r}. Choose one of: {supported}"
        )

    kwargs = {"domain_name": "zingmp3.vn"}
    if separator and cookie_file:
        kwargs["cookie_file"] = str(Path(cookie_file).expanduser())
    try:
        session.cookies.update(loader(**kwargs))
    except Exception as error:
        raise ZingMp3Error(f"Could not read cookies from {browser}: {error}") from error
