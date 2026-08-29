"""Ordered URL-to-extractor registry."""

import urllib.parse
from typing import Any, ClassVar

from zingmp3_cli.client import ZingMp3Client
from zingmp3_cli.exceptions import ZingMp3Error
from zingmp3_cli.utils import normalize_input_url

from .album import AlbumExtractor
from .base import BaseExtractor
from .charts import ChartHomeExtractor, VideoChartExtractor, WeekChartExtractor
from .hub import HubExtractor
from .live import LiveRadioExtractor
from .media import MediaExtractor
from .user import UserExtractor


class ExtractorRegistry:
    """Select the first extractor that recognizes a normalized URL path."""

    ALLOWED_HOSTS: ClassVar[frozenset[str]] = frozenset(
        {"zingmp3.vn", "www.zingmp3.vn", "mp3.zing.vn"}
    )

    def __init__(self, client: ZingMp3Client) -> None:
        self.extractors: tuple[BaseExtractor, ...] = (
            MediaExtractor(client),
            AlbumExtractor(client),
            ChartHomeExtractor(client),
            WeekChartExtractor(client),
            VideoChartExtractor(client),
            UserExtractor(client),
            HubExtractor(client),
            LiveRadioExtractor(client),
        )

    def match(self, url: str) -> tuple[BaseExtractor, dict[str, str]]:
        url = normalize_input_url(url)
        parsed = urllib.parse.urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in self.ALLOWED_HOSTS
        ):
            raise ZingMp3Error("The URL must belong to zingmp3.vn or mp3.zing.vn")
        path = parsed.path.rstrip("/") or "/"
        for extractor in self.extractors:
            if values := extractor.match(path):
                return extractor, values
        raise ZingMp3Error("Unsupported Zing MP3 URL type")

    def extract(self, url: str) -> dict[str, Any]:
        extractor, values = self.match(url)
        return extractor.extract(url, values)
