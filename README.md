# Zing MP3 CLI

A standalone Python CLI for crawling metadata and downloading media from Zing MP3.

## Requirements

- Python 3.10+
- [`ffmpeg`](https://www.ffmpeg.org/) for HLS downloads

## Installation

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
uv run python -m unittest discover -s tests -v
```

## Code quality

Check lint errors and verify formatting without changing files:

```bash
uvx ruff check src zingmp3.py tests
uvx ruff format --check src zingmp3.py tests
```

Format the source code and tests:

```bash
uvx ruff format src zingmp3.py tests
```

Apply safe automatic lint fixes when available:

```bash
uvx ruff check --fix src zingmp3.py tests
```
