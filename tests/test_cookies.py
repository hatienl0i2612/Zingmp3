import requests

from zingmp3_cli.cookies import load_cookie_argument


class TestCookieLoading:
    def test_raw_cookie_header(self):
        session = requests.Session()
        load_cookie_argument(session, "foo=one; token=a=b")

        assert session.cookies.get("foo") == "one"
        assert session.cookies.get("token") == "a=b"

    def test_netscape_cookie_file(self, tmp_path):
        path = tmp_path / "cookies.txt"
        path.write_text(
            "# Netscape HTTP Cookie File\n.zingmp3.vn\tTRUE\t/\tTRUE\t0\tfoo\tbar\n",
            encoding="utf-8",
        )
        session = requests.Session()
        load_cookie_argument(session, str(path))

        assert session.cookies.get("foo") == "bar"
