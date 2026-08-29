#!/usr/bin/env python3

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

main = import_module("zingmp3_cli.cli").main


if __name__ == "__main__":
    raise SystemExit(main())
