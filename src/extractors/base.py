"""Base classes and shared pagination for extractors."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from zingmp3_cli.client import ZingMp3Client
from zingmp3_cli.constants import PER_PAGE
from zingmp3_cli.utils import as_int, links


class BaseExtractor(ABC):
    """Base interface implemented by every URL-family extractor."""

    KIND: ClassVar[str]
    PATTERN: ClassVar[re.Pattern[str] | None] = None

    def __init__(self, client: ZingMp3Client) -> None:
        self.client = client

    def match(self, path: str) -> dict[str, str] | None:
        if self.PATTERN is None:
            return None
        match = self.PATTERN.match(path)
        return match.groupdict() if match else None

    @abstractmethod
    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        """Extract metadata from a previously matched URL."""

    @staticmethod
    def playlist(
        identifier: str,
        title: str | None,
        entry_urls: list[str],
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "_type": "playlist",
            "id": identifier,
            "title": title,
            "_entry_urls": entry_urls,
            **extra,
        }


class PaginatedExtractor(BaseExtractor):
    """Shared paginated-list behavior used by video charts and artists."""

    def paged_urls(self, identifier: str, url_type: str) -> list[str]:
        entry_urls: list[str] = []
        for page in range(1, 10001):
            api_type, item_type = self._page_api(url_type)
            data = self.client.call_api(
                api_type,
                {
                    "id": identifier,
                    "type": item_type,
                    "page": page,
                    "count": PER_PAGE,
                },
            )
            page_urls = links(data.get("items"))
            entry_urls.extend(page_urls)
            total = as_int(data.get("total"))
            if (
                not data.get("hasMore")
                or not page_urls
                or (total is not None and len(entry_urls) >= total)
            ):
                break
        return entry_urls

    @staticmethod
    def _page_api(url_type: str) -> tuple[str, str]:
        if url_type == "bai-hat":
            return "user-list-song", "artist"
        if url_type == "video":
            return "user-list-video", "artist"
        return "the-loai-video", "genre"
