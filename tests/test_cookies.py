import tempfile
import unittest
from pathlib import Path

import requests

from zingmp3_cli.cookies import load_cookie_argument


class CookieLoadingTests(unittest.TestCase):
    def test_raw_cookie_header(self):
        session = requests.Session()
        load_cookie_argument(session, "foo=one; token=a=b")

        self.assertEqual(session.cookies.get("foo"), "one")
        self.assertEqual(session.cookies.get("token"), "a=b")

    def test_netscape_cookie_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cookies.txt"
            path.write_text(
                "# Netscape HTTP Cookie File\n"
                ".zingmp3.vn\tTRUE\t/\tTRUE\t0\tfoo\tbar\n",
                encoding="utf-8",
            )
            session = requests.Session()
            load_cookie_argument(session, str(path))

        self.assertEqual(session.cookies.get("foo"), "bar")
