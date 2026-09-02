import os
import subprocess
import sys
from pathlib import Path


class TestPackageImports:
    def test_extractors_can_be_imported_first(self):
        environment = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
        process = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from extractors import ExtractorRegistry; "
                    "from zingmp3_cli import ZingMp3Client; "
                    "ExtractorRegistry(ZingMp3Client())"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        assert process.returncode == 0, process.stderr
