"""Song, music-video, and embed extractor."""

import re
from typing import Any

from zingmp3_cli.hls import extract_m3u8_formats
from zingmp3_cli.utils import absolute_url, as_int, first, number_in

from .base import BaseExtractor


class MediaExtractor(BaseExtractor):
    KIND = "zingmp3"
    PATTERN = re.compile(
        r"^/(?P<type>bai-hat|video-clip)/[^/?#]+/(?P<id>\w+)(?:\.html)?/?$"
    )
    EMBED_PATTERN = re.compile(r"^/embed/[^/?#]+/(?P<id>\w+)(?:\.html)?/?$")

    def match(self, path: str) -> dict[str, str] | None:
        if values := super().match(path):
            return values
        match = self.EMBED_PATTERN.match(path)
        return {"type": "embed", **match.groupdict()} if match else None

    def extract(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        url_type, media_id = values["type"], values["id"]
        item = self.client.call_api(url_type, {"id": media_id})
        item_id = item.get("encodeId") or media_id
        source = (
            item.get("streaming")
            if url_type == "video-clip"
            else self.client.call_api("song-streaming", {"id": item_id}, fatal=False)
        )
        formats = self._formats(source or {})
        lyric = item.get("lyric") or (
            self.client.call_api("lyric", {"id": item_id}, fatal=False) or {}
        ).get("file")
        return self._metadata(item, item_id, formats, lyric)

    def _formats(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        formats: list[dict[str, Any]] = []
        for format_id, value in source.items():
            if not value or value == "VIP":
                continue
            if format_id not in {"mp4", "hls"}:
                formats.append(
                    {
                        "format_id": str(format_id),
                        "ext": "flac" if format_id == "lossless" else "mp3",
                        "tbr": as_int(format_id),
                        "url": absolute_url(value),
                        "vcodec": "none",
                        "protocol": "https",
                    }
                )
                continue
            if not isinstance(value, dict):
                continue
            formats.extend(self._video_formats(format_id, value))
        return formats

    def _video_formats(
        self, format_id: str, sources: dict[str, Any]
    ) -> list[dict[str, Any]]:
        formats = []
        for resolution, source_url in sources.items():
            if not source_url:
                continue
            media_url = absolute_url(source_url)
            if format_id == "hls":
                hls_formats = extract_m3u8_formats(self.client, media_url)
                for hls_format in hls_formats:
                    height = number_in(resolution) or number_in(media_url)
                    if height and not hls_format.get("height"):
                        hls_format["height"] = height
                        if hls_format.get("format_id") == "hls":
                            hls_format["format_id"] = f"hls-{height}"
                formats.extend(hls_formats)
            else:
                formats.append(
                    {
                        "format_id": f"mp4-{resolution}",
                        "ext": "mp4",
                        "height": number_in(resolution),
                        "url": media_url,
                        "protocol": "https",
                    }
                )
        return formats

    @staticmethod
    def _metadata(
        item: dict[str, Any],
        item_id: str,
        formats: list[dict[str, Any]],
        lyric: str | None,
    ) -> dict[str, Any]:
        artists = [
            artist.get("name")
            for artist in item.get("artists") or []
            if artist.get("name")
        ]
        album = item.get("album") or {}
        album_artists = [
            artist.get("name")
            for artist in album.get("artists") or []
            if artist.get("name")
        ]
        title = first(item.get("title"), item.get("alias"))
        format_error = None
        if not formats:
            format_error = (
                item.get("msg")
                or "This content requires a VIP account or is geo-restricted"
            )
        return {
            "_type": "media",
            "extractor": MediaExtractor.KIND,
            "id": item_id,
            "title": title,
            "thumbnail": first(item.get("thumbnail"), item.get("thumbnailM")),
            "duration": as_int(item.get("duration")),
            "track": title,
            "artist": first(
                item.get("artistsNames"),
                item.get("artists_names"),
                artists[0] if artists else None,
            ),
            "artists": artists or None,
            "album": first(
                album.get("name"),
                album.get("title"),
                (item.get("genres") or [{}])[0].get("name"),
            ),
            "album_artist": first(
                album.get("artistsNames"),
                album.get("artists_names"),
                album_artists[0] if album_artists else None,
            ),
            "album_artists": album_artists or None,
            "formats": formats,
            "availability": "premium_only" if not formats else None,
            "format_error": format_error,
            "subtitles": {"origin": [{"url": lyric, "ext": "lrc"}]} if lyric else None,
        }
