"""Build a single-file executable with its own FFmpeg binary."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import imageio_ffmpeg
import PyInstaller.__main__

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIRECTORY = PROJECT_ROOT / "build"
DIST_DIRECTORY = PROJECT_ROOT / "dist"


def stage_ffmpeg() -> Path:
    """Copy imageio-ffmpeg's platform binary under the runtime filename."""
    source = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"FFmpeg binary was not found: {source}")

    executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    destination = BUILD_DIRECTORY / "vendor" / executable
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if os.name != "nt":
        destination.chmod(destination.stat().st_mode | 0o111)
    return destination


def pyinstaller_arguments(ffmpeg: Path) -> list[str]:
    """Create PyInstaller arguments for the portable release build."""
    return [
        str(PROJECT_ROOT / "scripts" / "standalone_entry.py"),
        "--name=zingmp3",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--noupx",
        f"--distpath={DIST_DIRECTORY}",
        f"--workpath={BUILD_DIRECTORY / 'pyinstaller'}",
        f"--specpath={BUILD_DIRECTORY / 'spec'}",
        f"--paths={PROJECT_ROOT / 'src'}",
        f"--add-binary={ffmpeg}{os.pathsep}.",
        "--hidden-import=browser_cookie3",
    ]


def main() -> None:
    PyInstaller.__main__.run(pyinstaller_arguments(stage_ffmpeg()))


if __name__ == "__main__":
    main()
