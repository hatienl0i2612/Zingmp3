"""Progressive HTTP and HLS media downloader."""

import os
import shutil
import subprocess
import sys
from collections import deque
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .client import ZingMp3Client
from .exceptions import ZingMp3Error
from .progress import hls_download_progress, http_download_progress
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
            if downloaded:
                print(file=sys.stderr)
            self._download_one(
                media_format,
                target,
                duration=as_int(info.get("duration")),
            )
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

    def _download_one(
        self,
        media_format: dict[str, Any],
        target: Path,
        *,
        duration: int | None = None,
    ) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            print(f"Already exists, skipping: {target}", file=sys.stderr)
            return
        temporary = target.with_name(f".{target.stem}.part{target.suffix}")
        print(f"Downloading: {target}", file=sys.stderr)
        if media_format.get("protocol") == "m3u8":
            self._download_hls(
                media_format["url"],
                temporary,
                description=target.name,
                duration=duration,
            )
        else:
            self._download_http(media_format["url"], temporary, description=target.name)
        temporary.replace(target)

    def _download_http(self, url: str, temporary: Path, *, description: str) -> None:
        response = self.client.request(url, stream=True)
        total = as_int(response.headers.get("Content-Length"))
        progress, task_id = http_download_progress(description, total)
        try:
            with progress, temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    output.write(chunk)
                    progress.advance(task_id, len(chunk))
                if total:
                    progress.update(task_id, completed=total)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        finally:
            response.close()

    def _download_hls(
        self,
        url: str,
        temporary: Path,
        *,
        description: str,
        duration: int | None,
    ) -> None:
        ffmpeg = self._find_ffmpeg()
        if not ffmpeg:
            raise ZingMp3Error(
                "Downloading HLS requires ffmpeg in PATH or the standalone bundle"
            )
        command = [
            ffmpeg,
            "-nostdin",
            "-loglevel",
            "error",
            "-progress",
            "pipe:1",
            "-nostats",
            "-y",
        ]
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
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        progress, task_id = hls_download_progress(description, duration)
        error_lines: deque[str] = deque(maxlen=10)
        try:
            if process.stdout is None:
                raise ZingMp3Error("Could not read ffmpeg progress output")
            with progress:
                for raw_line in process.stdout:
                    line = raw_line.strip()
                    key, separator, value = line.partition("=")
                    if not separator:
                        if line:
                            error_lines.append(line)
                        continue
                    seconds = self._ffmpeg_progress_seconds(key, value)
                    if seconds is not None:
                        completed = min(seconds, duration) if duration else seconds
                        progress.update(task_id, completed=completed)
                    elif key == "total_size":
                        downloaded = as_int(value)
                        if downloaded is not None:
                            progress.update(task_id, downloaded=downloaded)
                    elif key == "speed":
                        progress.update(task_id, media_speed=value)
                return_code = process.wait()
                if not return_code and duration:
                    progress.update(task_id, completed=duration)
        except BaseException:
            if process.poll() is None:
                process.terminate()
            process.wait()
            temporary.unlink(missing_ok=True)
            raise
        finally:
            if process.stdout is not None:
                process.stdout.close()
        if return_code:
            temporary.unlink(missing_ok=True)
            detail = f": {error_lines[-1]}" if error_lines else ""
            raise ZingMp3Error(f"ffmpeg failed with exit code {return_code}{detail}")

    @staticmethod
    def _ffmpeg_progress_seconds(key: str, value: str) -> float | None:
        if key in {"out_time_us", "out_time_ms"}:
            microseconds = as_int(value)
            if microseconds is None:
                return None
            return max(microseconds / 1_000_000, 0)
        if key != "out_time":
            return None
        try:
            hours, minutes, seconds = value.split(":", 2)
            return max(float(hours) * 3600 + float(minutes) * 60 + float(seconds), 0)
        except ValueError:
            return None

    @staticmethod
    def _find_ffmpeg() -> str | None:
        """Find FFmpeg bundled by PyInstaller, then fall back to PATH."""
        executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        bundle_directory = getattr(sys, "_MEIPASS", None)
        if bundle_directory:
            bundled_ffmpeg = Path(bundle_directory) / executable
            if bundled_ffmpeg.is_file():
                return str(bundled_ffmpeg)
        return shutil.which("ffmpeg")

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
