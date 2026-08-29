"""Hub extractor."""

import re
from typing import Any

from zingmp3_cli.utils import links, section_items

from .base import BaseExtractor


class HubExtractor(BaseExtractor):
    KIND = "zingmp3:hub"
    PATTERN = re.compile(r"^/hub/[^/?#]+/(?P<id>[^./?#]+)(?:\.html)?/?$")

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        data = self.client.call_api("hub", {"id": values["id"]})
        return self.playlist(
            values["id"],
            data.get("title"),
            links(section_items(data, "hub")),
            extractor=self.KIND,
            description=data.get("description"),
        )
