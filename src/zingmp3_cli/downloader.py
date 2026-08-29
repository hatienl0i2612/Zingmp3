"""Progressive HTTP and HLS media downloader."""

import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .client import ZingMp3Client
from .exceptions import ZingMp3Error
from .utils import as_int, safe_filename


class Downloader:
    """Select the best format and write resolved media to disk."""

    def __init__(self, client: ZingMp3Client) -> None:
        self.client = client
        self._cached_hls_options: list[str] | None = None

    @staticmethod
    def best_format(info: dict[str, Any]) -> dict[str, Any]:
        formats = info.get("formats") or []
        if not formats:
            raise ZingMp3Error(
                f"{info.get('title') or info.get('id')}: no downloadable format"
            )

        def score(media_format: dict[str, Any]) -> tuple[int, int, int, int]:
            return (
                int(media_format.get("format_id") == "lossless"),
                as_int(media_format.get("height")) or 0,
                as_int(media_format.get("tbr")) or 0,
                int(media_format.get("protocol") != "m3u8"),
            )

        return max(formats, key=score)

    def download(self, result: dict[str, Any], output: str | None) -> list[Path]:
        is_playlist = result.get("_type") == "playlist"
        return list(
            self.iter_downloads(
                self._iter_media(result), output, is_playlist=is_playlist
            )
        )

    def iter_downloads(
        self,
        entries: Iterable[dict[str, Any]],
        output: str | None,
        *,
        is_playlist: bool,
    ) -> Iterator[Path]:
        """Download each entry before requesting the next item from the iterable."""
        destination = Path(output).expanduser() if output else Path.cwd()
        if is_playlist:
            destination.mkdir(parents=True, exist_ok=True)

        found_media = False
        downloaded = False
        found_live = False
        media_index = 0
        for info in entries:
            if info.get("_type") == "error":
                print(
                    f"Skipping: {info.get('error') or 'extraction failed'}",
                    file=sys.stderr,
                )
                continue
            if info.get("_type") == "live":
                found_live = True
                self._show_live(info)
                continue
            if info.get("_type") != "media":
                continue
            found_media = True
            media_index += 1
            media_format = self._available_format(info, is_playlist)
            if media_format is None:
                continue
            target = self._target_path(
                info,
                media_format,
                destination,
                output,
                index=media_index,
                is_playlist=is_playlist,
            )
            self._download_one(media_format, target)
            downloaded = True
            yield target
        if found_live and not found_media:
            return
        if not found_media:
            raise ZingMp3Error("No media found to download")
        if not downloaded:
            raise ZingMp3Error("No downloadable media found")

    def _show_live(self, info: dict[str, Any]) -> None:
        print(
            f"LIVE: {info.get('title') or info.get('id')}\n"
            f"{self.best_format(info)['url']}",
            file=sys.stderr,
        )

    def _available_format(
        self, info: dict[str, Any], is_playlist: bool
    ) -> dict[str, Any] | None:
        try:
            return self.best_format(info)
        except ZingMp3Error as error:
            if not is_playlist:
                raise
            print(f"Skipping: {error}", file=sys.stderr)
            return None

    @staticmethod
    def _target_path(
        info: dict[str, Any],
        media_format: dict[str, Any],
        destination: Path,
        output: str | None,
        *,
        index: int,
        is_playlist: bool,
    ) -> Path:
        extension = media_format.get("ext") or "bin"
        title = safe_filename(info.get("title") or info["id"])
        default_name = f"{title} [{info['id']}].{extension}"
        is_directory = (
            is_playlist
            or destination.is_dir()
            or bool(output and output.endswith(("/", os.sep)))
        )
        if is_directory:
            prefix = f"{index:03d} - " if is_playlist else ""
            return destination / f"{prefix}{default_name}"
        return destination if output else Path.cwd() / default_name

    @staticmethod
    def _iter_media(result: dict[str, Any]) -> Iterator[dict[str, Any]]:
        if result.get("_type") in {"media", "live", "error"}:
            yield result
            return
        for entry in result.get("entries") or []:
            yield from Downloader._iter_media(entry)

    def _download_one(self, media_format: dict[str, Any], target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            print(f"Already exists, skipping: {target}", file=sys.stderr)
            return
        temporary = target.with_name(f".{target.stem}.part{target.suffix}")
        print(f"Downloading: {target}", file=sys.stderr)
        if media_format.get("protocol") == "m3u8":
            self._download_hls(media_format["url"], temporary)
        else:
            self._download_http(media_format["url"], temporary)
        temporary.replace(target)

    def _download_http(self, url: str, temporary: Path) -> None:
        response = self.client.request(url, stream=True)
        total = as_int(response.headers.get("Content-Length")) or 0
        received = 0
        try:
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    output.write(chunk)
                    received += len(chunk)
                    if total:
                        print(
                            f"\r{received * 100 / total:6.2f}%",
                            end="",
                            file=sys.stderr,
                        )
            if total:
                print(file=sys.stderr)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _download_hls(self, url: str, temporary: Path) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise ZingMp3Error("Downloading HLS requires ffmpeg in PATH")
        command = [ffmpeg, "-nostdin", "-loglevel", "error", "-y"]
        if headers := self._ffmpeg_headers():
            command.extend(["-headers", headers])
        command.extend(
            [
                *self._ffmpeg_hls_options(ffmpeg),
                "-i",
                url,
                "-c",
                "copy",
                str(temporary),
            ]
        )
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            temporary.unlink(missing_ok=True)
            raise ZingMp3Error(f"ffmpeg failed with exit code {completed.returncode}")

    def _ffmpeg_headers(self) -> str:
        headers = [
            f"{key}: {value}" for key, value in self.client.session.headers.items()
        ]
        cookie_header = "; ".join(
            f"{cookie.name}={cookie.value}" for cookie in self.client.session.cookies
        )
        if cookie_header:
            headers.append(f"Cookie: {cookie_header}")
        return "\r\n".join(headers) + "\r\n" if headers else ""

    def _ffmpeg_hls_options(self, ffmpeg: str) -> list[str]:
        if self._cached_hls_options is not None:
            return self._cached_hls_options
        probe = subprocess.run(
            [ffmpeg, "-hide_banner", "-h", "demuxer=hls"],
            check=False,
            capture_output=True,
            text=True,
        )
        help_text = f"{probe.stdout}\n{probe.stderr}"
        options = ["-allowed_extensions", "ALL"]
        if "allowed_segment_extensions" in help_text:
            options.extend(["-allowed_segment_extensions", "ALL"])
        if "extension_picky" in help_text:
            options.extend(["-extension_picky", "0"])
        self._cached_hls_options = options
        return options
