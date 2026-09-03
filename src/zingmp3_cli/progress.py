"""Terminal progress renderers for direct and HLS downloads."""

from __future__ import annotations

from rich.console import Console
from rich.filesize import decimal
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskID,
    TaskProgressColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.text import Text

_BAR_WIDTH = 40


def _format_duration(value: float) -> str:
    seconds = max(int(value), 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class HlsStatusColumn(ProgressColumn):
    """Render FFmpeg media time, output size, and processing speed."""

    def render(self, task: Task) -> Text:
        elapsed = _format_duration(task.completed)
        duration = _format_duration(task.total) if task.total else "--:--"
        downloaded = decimal(int(task.fields.get("downloaded", 0)))
        speed = str(task.fields.get("media_speed") or "--x")
        return Text(f"{elapsed}/{duration}  {downloaded}  {speed}", style="cyan")


def _progress(*columns: ProgressColumn) -> Progress:
    console = Console(stderr=True)
    return Progress(
        *columns,
        console=console,
        disable=not console.is_terminal,
        refresh_per_second=10,
        expand=False,
    )


def http_download_progress(
    description: str, total: int | None
) -> tuple[Progress, TaskID]:
    """Create a byte-oriented progress bar for a direct HTTP transfer."""
    progress = _progress(
        SpinnerColumn(style="bright_cyan"),
        BarColumn(
            bar_width=_BAR_WIDTH,
            style="grey35",
            complete_style="bright_cyan",
            finished_style="green",
            pulse_style="cyan",
        ),
        TaskProgressColumn(),
        DownloadColumn(binary_units=True),
        TransferSpeedColumn(),
        TimeRemainingColumn(compact=True, elapsed_when_finished=True),
    )
    return progress, progress.add_task(description, total=total)


def hls_download_progress(
    description: str, duration: float | None
) -> tuple[Progress, TaskID]:
    """Create a media-time progress bar for an FFmpeg HLS transfer."""
    progress = _progress(
        SpinnerColumn(style="bright_magenta"),
        BarColumn(
            bar_width=_BAR_WIDTH,
            style="grey35",
            complete_style="bright_magenta",
            finished_style="green",
            pulse_style="magenta",
        ),
        TaskProgressColumn(),
        HlsStatusColumn(),
        TimeRemainingColumn(compact=True, elapsed_when_finished=True),
    )
    task_id = progress.add_task(
        description,
        total=duration,
        downloaded=0,
        media_speed="--x",
    )
    return progress, task_id


class HlsSegmentColumn(ProgressColumn):
    """Render completed segment count, downloaded size, and transfer speed."""

    def render(self, task: Task) -> Text:
        done = int(task.completed)
        total = int(task.total) if task.total else 0
        downloaded = decimal(int(task.fields.get("downloaded", 0)))
        speed = task.fields.get("segment_speed") or 0
        speed_text = f"{decimal(int(speed))}/s" if speed else "--"
        return Text(f"{done}/{total}  {downloaded}  {speed_text}", style="magenta")


def hls_segment_progress(description: str, total: int) -> tuple[Progress, TaskID]:
    """Create a segment-count progress bar for a parallel HLS transfer."""
    progress = _progress(
        SpinnerColumn(style="bright_magenta"),
        BarColumn(
            bar_width=_BAR_WIDTH,
            style="grey35",
            complete_style="bright_magenta",
            finished_style="green",
            pulse_style="magenta",
        ),
        TaskProgressColumn(),
        HlsSegmentColumn(),
        TimeRemainingColumn(compact=True, elapsed_when_finished=True),
    )
    return progress, progress.add_task(
        description, total=total, downloaded=0, segment_speed=0
    )
