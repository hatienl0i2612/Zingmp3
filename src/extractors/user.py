"""Artist profile and new-release extractor."""

import re
from typing import Any

from zingmp3_cli.utils import links, section_items

from .base import PaginatedExtractor


class UserExtractor(PaginatedExtractor):
    KIND = "zingmp3:user"
    PATTERN = re.compile(
        r"^/(?P<alias>[^/?#]+)/"
        r"(?P<type>bai-hat|single|album|video|song)/?$"
    )

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        alias, url_type = values["alias"], values["type"]
        if alias == "new-release" and url_type in {"song", "album"}:
            identifier = f"{alias}-{url_type}"
            data = self.client.call_api("new-release", {"type": url_type})
            return self.playlist(
                identifier,
                identifier,
                links(data),
                extractor=self.KIND,
            )

        user = self.client.call_api("info-artist", {"alias": alias})
        if url_type in {"bai-hat", "video"}:
            entry_urls = self.paged_urls(user["id"], url_type)
        else:
            section_id = "aAlbum" if url_type == "album" else "aSingle"
            entry_urls = links(section_items(user, section_id))
        title = " - ".join(value for value in (user.get("name"), url_type) if value)
        return self.playlist(
            user["id"],
            title,
            entry_urls,
            extractor=self.KIND,
            description=user.get("biography"),
        )
