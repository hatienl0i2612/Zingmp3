"""Home, weekly, and music-video chart extractors."""

import re
from typing import Any, ClassVar

from zingmp3_cli.exceptions import ZingMp3Error
from zingmp3_cli.utils import links

from .base import BaseExtractor, PaginatedExtractor


class ChartHomeExtractor(BaseExtractor):
    KIND = "zingmp3:chart-home"
    CHART_IDS: ClassVar[set[str]] = {
        "zing-chart",
        "moi-phat-hanh",
        "top100",
        "podcast-discover",
    }

    def match(self, path: str) -> dict[str, str] | None:
        chart_id = path.strip("/")
        return {"id": chart_id} if chart_id in self.CHART_IDS else None

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        chart_id = values["id"]
        if chart_id == "podcast-discover":
            raise ZingMp3Error("The current extractor has error with this URL")
        data = self.client.call_api(chart_id, {"id": chart_id})
        if chart_id == "top100":
            items = [
                item
                for group in data or []
                if isinstance(group, dict)
                for item in group.get("items") or []
                if isinstance(item, dict)
            ]
        elif chart_id == "zing-chart":
            items = (data.get("RTChart") or {}).get("items") or []
        else:
            items = data.get("items") or []
        return self.playlist(
            chart_id,
            chart_id,
            links(items),
            extractor=self.KIND,
        )


class WeekChartExtractor(BaseExtractor):
    KIND = "zingmp3:week-chart"
    PATTERN = re.compile(r"^/zing-chart-tuan/[^/?#]+/(?P<id>\w+)(?:\.html)?/?$")

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        data = self.client.call_api("zing-chart-tuan", {"id": values["id"]})
        return self.playlist(
            values["id"],
            f"zing-chart-{data.get('country', '')}",
            links(data.get("items")),
            extractor=self.KIND,
        )


class VideoChartExtractor(PaginatedExtractor):
    KIND = "zingmp3:chart-music-video"
    PATTERN = re.compile(
        r"^/the-loai-video/(?P<region>[^/?#]+)/"
        r"(?P<id>[^./?#]+)(?:\.html)?/?$"
    )

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        return self.playlist(
            values["id"],
            f"the-loai-video_{values['region']}",
            self.paged_urls(values["id"], "the-loai-video"),
            extractor=self.KIND,
        )
