"""HLS manifest parsing shared by media and live extractors."""

import re
import urllib.parse
from typing import Any

from .client import ZingMp3Client
from .exceptions import ZingMp3Error
from .utils import as_int


def extract_m3u8_formats(
    client: ZingMp3Client, manifest_url: str
) -> list[dict[str, Any]]:
    """Resolve a master manifest or preserve a media manifest as one format."""
    try:
        text = client.request(manifest_url).text
    except ZingMp3Error:
        return [_fallback_format(manifest_url)]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    formats = []
    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:") or index + 1 >= len(lines):
            continue
        attributes = _parse_attributes(line.split(":", 1)[1])
        resolution = attributes.get("RESOLUTION", "").split("x")
        height = as_int(resolution[-1]) if len(resolution) == 2 else None
        bandwidth = as_int(attributes.get("BANDWIDTH")) or 0
        formats.append(
            {
                "format_id": f"hls-{height or len(formats)}",
                "ext": "mp4",
                "height": height,
                "tbr": bandwidth // 1000 or None,
                "url": urllib.parse.urljoin(manifest_url, lines[index + 1]),
                "protocol": "m3u8",
            }
        )
    return formats or [_fallback_format(manifest_url)]


def _parse_attributes(value: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2) or match.group(3)
        for match in re.finditer(r'([A-Z0-9-]+)=(?:"([^"]*)"|([^,]*))(?:,|$)', value)
    }


def _fallback_format(manifest_url: str) -> dict[str, Any]:
    return {
        "format_id": "hls",
        "ext": "mp4",
        "url": manifest_url,
        "protocol": "m3u8",
    }
