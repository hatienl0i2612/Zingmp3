"""High-level recursive metadata crawler."""

from collections.abc import Iterable, Iterator
from typing import Any

from extractors import ExtractorRegistry

from .client import ZingMp3Client
from .exceptions import ZingMp3Error
from .utils import normalize_input_url


class ZingMp3Crawler:
    """Resolve a URL and recursively expand collection entries."""

    MAX_PLAYLIST_DEPTH = 10

    def __init__(
        self,
        *,
        client: ZingMp3Client | None = None,
        cookies: str | None = None,
        cookies_from_browser: str | None = None,
        headers: Iterable[str] = (),
        timeout: float = 30,
    ) -> None:
        self.client = client or ZingMp3Client(
            cookies=cookies,
            cookies_from_browser=cookies_from_browser,
            headers=headers,
            timeout=timeout,
        )
        self.registry = ExtractorRegistry(self.client)

    def extract(
        self, url: str, *, resolve: bool = True, _depth: int = 0
    ) -> dict[str, Any]:
        if _depth > self.MAX_PLAYLIST_DEPTH:
            raise ZingMp3Error("Maximum playlist resolution depth exceeded")

        url = normalize_input_url(url)
        result = self.registry.extract(url)
        result.setdefault("webpage_url", url)
        if resolve and result.get("_type") == "playlist":
            result["entries"] = self._resolve_entries(
                result.pop("_entry_urls", []), _depth
            )
            result["entry_count"] = len(result["entries"])
        return result

    def _resolve_entries(
        self, entry_urls: list[str], depth: int
    ) -> list[dict[str, Any]]:
        resolved = []
        for entry_url in entry_urls:
            try:
                resolved.append(self.extract(entry_url, _depth=depth + 1))
            except ZingMp3Error as error:
                # One unavailable or VIP item must not invalidate a collection.
                resolved.append(
                    {"_type": "error", "webpage_url": entry_url, "error": str(error)}
                )
        return resolved

    def iter_media(
        self, result: dict[str, Any], *, _depth: int = 0
    ) -> Iterator[dict[str, Any]]:
        """Resolve collection entries one at a time as the consumer requests them."""
        if _depth > self.MAX_PLAYLIST_DEPTH:
            raise ZingMp3Error("Maximum playlist resolution depth exceeded")

        result_type = result.get("_type")
        if result_type in {"media", "live", "error"}:
            yield result
            return
        if result_type != "playlist":
            return

        if "entries" in result:
            for entry in result.get("entries") or []:
                yield from self.iter_media(entry, _depth=_depth + 1)
            return

        for entry_url in result.get("_entry_urls") or []:
            try:
                entry = self.extract(entry_url, resolve=False, _depth=_depth + 1)
            except ZingMp3Error as error:
                yield {
                    "_type": "error",
                    "webpage_url": entry_url,
                    "error": str(error),
                }
                continue
            yield from self.iter_media(entry, _depth=_depth + 1)
