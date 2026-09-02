# Zing MP3 CLI

A standalone Python CLI for crawling metadata and downloading media from Zing MP3.

## Requirements

- Source installation: Python 3.10+ and
  [`ffmpeg`](https://www.ffmpeg.org/) for HLS downloads
- Standalone release: no Python, packages, or separate FFmpeg installation

## Download the latest release

[Download the latest portable release](https://github.com/hatienl0i2612/zingmp3/releases/latest)
and select the archive for your system:

| Operating system | Asset name |
| --- | --- |
| Linux x86-64 | `zingmp3-v*-linux-x86_64.tar.gz` |
| Windows x86-64 | `zingmp3-v*-windows-x86_64.zip` |
| macOS Intel | `zingmp3-v*-macos-x86_64.zip` |
| macOS Apple Silicon | `zingmp3-v*-macos-arm64.zip` |

Extract the archive. On Linux and macOS, make the binary executable and run it:

```bash
chmod +x zingmp3
./zingmp3 --help
./zingmp3 'https://zingmp3.vn/bai-hat/.../ID.html'
```

On Windows, open PowerShell in the extracted directory:

```powershell
.\zingmp3.exe --help
.\zingmp3.exe "https://zingmp3.vn/bai-hat/.../ID.html"
```

The portable executable already includes Python, all required packages, and FFmpeg.

## Installation from source

Install the locked dependencies and the project into `.venv` with
[`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
```

Run the CLI without activating the virtual environment:

```bash
uv run zingmp3 --help
uv run zingmp3 --json 'https://zingmp3.vn/bai-hat/.../ID.html'
```

Alternatively, activate the environment and use the installed console command
directly:

```bash
source .venv/bin/activate
zingmp3 --help
```

The root `zingmp3.py` remains available as a backward-compatible development
entrypoint:

```bash
python zingmp3.py --help
```

## Usage

```bash
zingmp3 'https://zingmp3.vn/bai-hat/.../ID.html'
zingmp3 --json 'https://zingmp3.vn/album/.../ID.html'
zingmp3 --output ./downloads 'https://zingmp3.vn/Mr-Siro/bai-hat'
zingmp3 --cookies-file cookies.txt 'URL'
zingmp3 --cookies 'zmp3_rqid=...; zmp3_sid=...' 'URL'
zingmp3 --cookies-from-browser chrome 'URL'
zingmp3 -H 'Origin: https://zingmp3.vn' -H 'X-Test: value' 'URL'
```

`--json` resolves the entire collection before writing complete metadata to stdout.
Download mode resolves one collection entry, downloads it immediately, and only then
continues to the next entry. The CLI chooses lossless audio first, then the highest
resolution or bitrate. `--output` is a destination file for one media URL or a
destination directory for a collection. For live radio, it is ignored and the stream
URL is printed instead.

## Supported URL families

- Songs, music videos, and embeds
- Albums and playlists
- Zing chart, new-release chart, and Top 100
- Weekly charts
- Music-video charts
- Artist songs, singles, albums, and videos
- New releases
- Hubs
- Live radio

## Unit tests

```bash
uv run pytest
```

## Code quality

Check lint errors and verify formatting without changing files:

```bash
uv run ruff check src scripts tests zingmp3.py
uv run ruff format --check src scripts tests zingmp3.py
```

Format the source code and tests:

```bash
uv run ruff format src scripts tests zingmp3.py
```

Apply safe automatic lint fixes when available:

```bash
uv run ruff check --fix src scripts tests zingmp3.py
```
