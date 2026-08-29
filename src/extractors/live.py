"""Live-radio extractor."""

import re
from typing import Any

from zingmp3_cli.exceptions import ZingMp3Error
from zingmp3_cli.hls import extract_m3u8_formats
from zingmp3_cli.utils import as_int, first

from .base import BaseExtractor


class LiveRadioExtractor(BaseExtractor):
    KIND = "zingmp3:liveradio"
    PATTERN = re.compile(r"^/liveradio/(?P<id>\w+)(?:\.html)?/?$")

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        data = self.client.call_api("liveradio", {"id": values["id"]})
        manifest_url = data.get("streaming")
        if not manifest_url:
            raise ZingMp3Error("This radio station is currently offline")
        return {
            "_type": "live",
            "extractor": self.KIND,
            "id": values["id"],
            "title": data.get("title"),
            "description": data.get("description"),
            "thumbnail": first(
                data.get("thumbnail"),
                data.get("thumbnailM"),
                data.get("thumbnailV"),
                data.get("thumbnailH"),
            ),
            "view_count": as_int(data.get("activeUsers")),
            "like_count": as_int(data.get("totalReaction")),
            "is_live": True,
            "formats": extract_m3u8_formats(self.client, manifest_url),
        }
