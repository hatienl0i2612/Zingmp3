import unittest
from unittest.mock import patch

from zingmp3_cli.cli import build_parser, main


class CliTests(unittest.TestCase):
    def test_cookies_file_alias(self):
        args = build_parser().parse_args(
            ["--cookies-file", "cookies.txt", "https://zingmp3.vn/top100"]
        )
        self.assertEqual(args.cookies, "cookies.txt")

    def test_repeatable_headers(self):
        args = build_parser().parse_args(
            [
                "-H",
                "X-One: 1",
                "--headers",
                "X-Two: 2",
                "https://zingmp3.vn/top100",
            ]
        )
        self.assertEqual(args.headers, ["X-One: 1", "X-Two: 2"])

    @patch("zingmp3_cli.cli.Downloader")
    @patch("zingmp3_cli.cli.ZingMp3Crawler")
    def test_download_mode_requests_a_shallow_result(
        self, crawler_class, downloader_class
    ):
        crawler = crawler_class.return_value
        crawler.extract.return_value = {"_type": "playlist", "_entry_urls": []}
        crawler.iter_media.return_value = iter(())
        downloader_class.return_value.iter_downloads.return_value = iter(())

        self.assertEqual(main(["https://zingmp3.vn/top100"]), 0)

        crawler.extract.assert_called_once_with(
            "https://zingmp3.vn/top100", resolve=False
        )
        crawler.iter_media.assert_called_once_with(crawler.extract.return_value)

    @patch("zingmp3_cli.cli.ZingMp3Crawler")
    def test_json_mode_requests_a_fully_resolved_result(self, crawler_class):
        crawler = crawler_class.return_value
        crawler.extract.return_value = {"_type": "playlist", "entries": []}

        with patch("builtins.print"):
            self.assertEqual(main(["--json", "https://zingmp3.vn/top100"]), 0)

        crawler.extract.assert_called_once_with("https://zingmp3.vn/top100")
