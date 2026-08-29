import os
import subprocess
import sys
import unittest
from pathlib import Path


class PackageImportTests(unittest.TestCase):
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
        self.assertEqual(process.returncode, 0, process.stderr)
