"""Entrypoint used only by the standalone executable build."""

from zingmp3_cli.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
