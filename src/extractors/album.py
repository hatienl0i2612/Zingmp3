"""Album and playlist extractor."""

import re
from typing import Any

from zingmp3_cli.utils import first, links

from .base import BaseExtractor


class AlbumExtractor(BaseExtractor):
    KIND = "zingmp3:album"
    PATTERN = re.compile(
        r"^/(?P<type>album|playlist)/[^/?#]+/(?P<id>\w+)(?:\.html)?/?$"
    )

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        data = self.client.call_api(values["type"], {"id": values["id"]})
        return self.playlist(
            first(data.get("id"), data.get("encodeId"), values["id"]),
            first(data.get("name"), data.get("title")),
            links((data.get("song") or {}).get("items")),
            extractor=self.KIND,
        )
