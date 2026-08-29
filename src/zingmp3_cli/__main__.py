"""Allow the package to run with ``python -m zingmp3_cli``."""

from .cli import main

raise SystemExit(main())
