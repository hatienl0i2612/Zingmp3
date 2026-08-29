"""Public package interface for Zing MP3 CLI."""

from importlib import import_module
from typing import Any

__all__ = ["Downloader", "ZingMp3Client", "ZingMp3Crawler", "ZingMp3Error"]
__version__ = "1.0.0"

_PUBLIC_OBJECTS = {
    "Downloader": (".downloader", "Downloader"),
    "ZingMp3Client": (".client", "ZingMp3Client"),
    "ZingMp3Crawler": (".crawler", "ZingMp3Crawler"),
    "ZingMp3Error": (".exceptions", "ZingMp3Error"),
}


def __getattr__(name: str) -> Any:
    """Load public objects lazily to keep package initialization acyclic."""
    try:
        module_name, object_name = _PUBLIC_OBJECTS[name]
    except KeyError as error:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from error
    value = getattr(import_module(module_name, __name__), object_name)
    globals()[name] = value
    return value
