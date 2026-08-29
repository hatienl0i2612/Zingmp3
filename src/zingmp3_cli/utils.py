"""Small data and URL helpers without network side effects."""

import re
import urllib.parse
from typing import Any

from .constants import DOMAIN


def first(*values: Any) -> Any:
    """Return the first non-empty value."""
    return next((value for value in values if value not in (None, "", [], {})), None)


def as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def number_in(value: Any) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def absolute_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("//"):
        return f"https:{url}"
    return urllib.parse.urljoin(f"{DOMAIN}/", url)


def links(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [
        url
        for item in items
        if isinstance(item, dict) and (url := absolute_url(item.get("link")))
    ]


def section_items(data: dict[str, Any], section_id: str) -> list[dict[str, Any]]:
    for section in data.get("sections") or []:
        if isinstance(section, dict) and section.get("sectionId") == section_id:
            return [
                item for item in section.get("items") or [] if isinstance(item, dict)
            ]
    return []


def safe_filename(value: str) -> str:
    value = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "_", value).strip(" .")
    return value[:180] or "untitled"


def normalize_input_url(value: str) -> str:
    """Unwrap URLs copied as Markdown links or angle-bracket autolinks."""
    value = value.strip()
    markdown_link = re.fullmatch(r"\[[^]]*]\((https?://[^)]+)\)", value)
    if markdown_link:
        return markdown_link.group(1)
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1].strip()
    return value
