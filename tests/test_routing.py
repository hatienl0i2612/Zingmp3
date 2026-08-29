import unittest

from extractors import ExtractorRegistry
from zingmp3_cli.client import ZingMp3Client
from zingmp3_cli.exceptions import ZingMp3Error


class ExtractorRoutingTests(unittest.TestCase):
    def setUp(self):
        self.registry = ExtractorRegistry(ZingMp3Client())

    def test_all_current_url_kinds_are_classified(self):
        cases = {
            "https://zingmp3.vn/bai-hat/X/ZWZB9WAB.html": "zingmp3",
            "https://zingmp3.vn/video-clip/X/ZO8ZF7C7.html": "zingmp3",
            "https://zingmp3.vn/embed/song/ZWZEI76B?start=false": "zingmp3",
            "https://zingmp3.vn/album/X/ZOC7WUZC.html": "zingmp3:album",
            "https://mp3.zing.vn/playlist/X/IWCAACCB.html": "zingmp3:album",
            "https://zingmp3.vn/zing-chart": "zingmp3:chart-home",
            "https://zingmp3.vn/moi-phat-hanh": "zingmp3:chart-home",
            "https://zingmp3.vn/top100": "zingmp3:chart-home",
            "https://zingmp3.vn/zing-chart-tuan/X/IWZ9Z08I.html": (
                "zingmp3:week-chart"
            ),
            "https://zingmp3.vn/the-loai-video/Viet-Nam/IWZ9Z08I.html": (
                "zingmp3:chart-music-video"
            ),
            "https://zingmp3.vn/Mr-Siro/bai-hat": "zingmp3:user",
            "https://zingmp3.vn/new-release/album": "zingmp3:user",
            "https://zingmp3.vn/hub/Nhac-Moi/IWZ9Z0CA.html": "zingmp3:hub",
            "https://zingmp3.vn/liveradio/IWZ979UB.html": "zingmp3:liveradio",
        }
        for url, expected_kind in cases.items():
            with self.subTest(url=url):
                extractor, _ = self.registry.match(url)
                self.assertEqual(extractor.KIND, expected_kind)

    def test_rejects_unsupported_host(self):
        with self.assertRaises(ZingMp3Error):
            self.registry.match("https://example.com/song")

    def test_rejects_unknown_zing_url(self):
        with self.assertRaises(ZingMp3Error):
            self.registry.match("https://zingmp3.vn/unknown")

    def test_accepts_markdown_link_input(self):
        url = (
            "[Zing MP3](https://zingmp3.vn/album/"
            "Anh-Khang-Hits-Collection-Anh-Khang/AKw4CWcI4D2E.html)"
        )
        extractor, values = self.registry.match(url)
        self.assertEqual(extractor.KIND, "zingmp3:album")
        self.assertEqual(values["id"], "AKw4CWcI4D2E")
