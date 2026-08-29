"""Signed Zing MP3 API client."""

import hashlib
import hmac
import urllib.parse
from collections.abc import Iterable
from typing import Any

import requests

from .constants import (
    API_KEY,
    API_SECRET,
    API_SLUGS,
    API_VERSION,
    DEFAULT_HEADERS,
    DOMAIN,
    SIGNED_PARAMS,
)
from .cookies import load_browser_cookies, load_cookie_argument
from .exceptions import ZingMp3Error


class ZingMp3Client:
    """Own the HTTP session, authentication state, and API signing logic."""

    def __init__(
        self,
        *,
        cookies: str | None = None,
        cookies_from_browser: str | None = None,
        headers: Iterable[str] = (),
        timeout: float = 30,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.timeout = timeout
        self._explicit_cookies = bool(cookies or cookies_from_browser)
        self._initialized = False

        self._apply_headers(headers)
        if cookies:
            load_cookie_argument(self.session, cookies)
        if cookies_from_browser:
            load_browser_cookies(self.session, cookies_from_browser)

    def _apply_headers(self, headers: Iterable[str]) -> None:
        for raw_header in headers:
            key, separator, value = raw_header.partition(":")
            if not separator or not key.strip():
                raise ZingMp3Error(
                    f"Invalid header: {raw_header!r}; expected 'Key: Value'"
                )
            self.session.headers[key.strip()] = value.strip()

    @staticmethod
    def build_api_url(url_type: str, params: dict[str, Any]) -> str:
        try:
            api_slug = API_SLUGS[url_type]
        except KeyError as error:
            raise ZingMp3Error(
                f"No API route is configured for URL type {url_type!r}"
            ) from error

        all_params = {**params, "ctime": "1", "version": API_VERSION}
        sign_params = {
            key: value
            for key, value in sorted(all_params.items())
            if key in SIGNED_PARAMS and value not in (None, "")
        }
        hash_input = "".join(
            f"{urllib.parse.quote(str(key), safe='')}="
            f"{urllib.parse.quote(str(value), safe='')}"
            for key, value in sign_params.items()
        )
        digest = hashlib.sha256(hash_input.encode()).hexdigest()
        signature = hmac.new(
            API_SECRET, f"{api_slug}{digest}".encode(), hashlib.sha512
        ).hexdigest()
        query = urllib.parse.urlencode(
            {**all_params, "apiKey": API_KEY, "sig": signature}
        )
        return f"{DOMAIN}{api_slug}?{query}"

    def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        if self._explicit_cookies:
            return

        # Zing returns a visitor cookie on this harmless API request.
        try:
            response = self.session.get(
                self.build_api_url("bai-hat", {"id": ""}), timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException:
            pass

    def request(self, url: str, **kwargs: Any) -> requests.Response:
        try:
            response = self.session.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            raise ZingMp3Error(f"HTTP request failed: {error}") from error

    def call_api(
        self, url_type: str, params: dict[str, Any], *, fatal: bool = True
    ) -> Any:
        self.initialize()
        response = self.request(self.build_api_url(url_type, params))
        try:
            payload = response.json()
        except requests.JSONDecodeError as error:
            if not fatal:
                return {}
            raise ZingMp3Error(f"The {url_type} API returned invalid JSON") from error

        data = payload.get("data") if isinstance(payload, dict) else None
        if data not in (None, ""):
            return data
        if not fatal:
            return {}
        message = payload.get("msg") if isinstance(payload, dict) else None
        raise ZingMp3Error(message or f"The {url_type} API returned no data")
