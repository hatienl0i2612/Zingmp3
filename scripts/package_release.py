"""Package a standalone executable and create its SHA-256 checksum."""

from __future__ import annotations

import argparse
import hashlib
import re
import tarfile
import zipfile
from pathlib import Path

VERSION_PATTERN = re.compile(r"v\d+\.\d+\.\d+")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--output-directory", default="release", type=Path)
    return parser


def create_archive(binary: Path, output: Path, platform: str) -> Path:
    """Create a ZIP on Windows/macOS or a tarball on Linux."""
    stem = output / f"zingmp3-{platform}"
    if platform.startswith("linux-") or "-linux-" in platform:
        archive = Path(f"{stem}.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(binary, arcname=binary.name)
        return archive

    archive = Path(f"{stem}.zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.write(binary, arcname=binary.name)
    return archive


def write_checksum(archive: Path) -> Path:
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_name(f"{archive.name}.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return checksum


def main() -> None:
    args = build_parser().parse_args()
    if not VERSION_PATTERN.fullmatch(args.version):
        raise ValueError("Release version must match vMAJOR.MINOR.PATCH")
    if not args.binary.is_file():
        raise FileNotFoundError(f"Executable was not found: {args.binary}")

    args.output_directory.mkdir(parents=True, exist_ok=True)
    platform = f"{args.version}-{args.platform}"
    archive = create_archive(args.binary, args.output_directory, platform)
    checksum = write_checksum(archive)
    print(archive)
    print(checksum)


if __name__ == "__main__":
    main()
