"""Tests against real Zing MP3 URLs and APIs."""

import json
import unittest

from zingmp3_cli import ZingMp3Crawler


class LiveUrlExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crawler = ZingMp3Crawler(timeout=30)

    def test_song_video_and_embed_media(self):
        cases = (
            "https://zingmp3.vn/bai-hat/Xa-Mai-Xa-Bao-Thy/ZWZB9WAB.html",
            "https://zingmp3.vn/video-clip/Suong-Hoa-Dua-Loi-K-ICM-RYO/ZO8ZF7C7.html",
            "https://zingmp3.vn/embed/song/ZWZEI76B?start=false",
        )
        for url in cases:
            with self.subTest(url=url):
                self.assert_media(self.extract(url))

    def test_album(self):
        result = self.extract(
            "https://zingmp3.vn/album/Anh-Khang-Hits-Collection-Anh-Khang/"
            "AKw4CWcI4D2E.html"
        )
        self.assert_collection(result, "zingmp3:album")

    def test_chart_home_variants(self):
        cases = (
            "https://zingmp3.vn/zing-chart",
            "https://zingmp3.vn/moi-phat-hanh",
            "https://zingmp3.vn/top100",
        )
        for url in cases:
            with self.subTest(url=url):
                self.assert_collection(self.extract(url), "zingmp3:chart-home")

    def test_week_chart(self):
        result = self.extract(
            "https://zingmp3.vn/zing-chart-tuan/Bai-hat-Viet-Nam/IWZ9Z08I.html"
        )
        self.assert_collection(result, "zingmp3:week-chart")

    def test_music_video_chart(self):
        result = self.extract(
            "https://zingmp3.vn/the-loai-video/Viet-Nam/IWZ9Z08I.html"
        )
        self.assert_collection(result, "zingmp3:chart-music-video")

    def test_artist_branches(self):
        cases = (
            "https://zingmp3.vn/Mr-Siro/bai-hat",
            "https://zingmp3.vn/Mr-Siro/album",
            "https://zingmp3.vn/Mr-Siro/single",
            "https://zingmp3.vn/Mr-Siro/video",
        )
        for url in cases:
            with self.subTest(url=url):
                self.assert_collection(self.extract(url), "zingmp3:user")

    def test_new_release_branches(self):
        for release_type in ("song", "album"):
            url = f"https://zingmp3.vn/new-release/{release_type}"
            with self.subTest(url=url):
                self.assert_collection(self.extract(url), "zingmp3:user")

    def test_hub(self):
        result = self.extract("https://zingmp3.vn/hub/Nhac-Moi/IWZ9Z0CA.html")
        self.assert_collection(result, "zingmp3:hub")

    def test_live_radio(self):
        result = self.extract("https://zingmp3.vn/liveradio/IWZ979UB.html")
        self.assert_common_fields(result, "zingmp3:liveradio", "live")
        self.assertIs(result["is_live"], True)
        self.assert_formats(result)

    def extract(self, url):
        result = self.crawler.extract(url, resolve=False)
        # Verify that the public result can be emitted as valid JSON.
        return json.loads(json.dumps(result, ensure_ascii=False))

    def assert_media(self, result):
        self.assert_common_fields(result, "zingmp3", "media")
        self.assertIsInstance(result["duration"], int)
        self.assert_formats(result, allow_unavailable=True)

    def assert_collection(self, result, expected_kind):
        self.assert_common_fields(result, expected_kind, "playlist")
        self.assertIsInstance(result["_entry_urls"], list)
        self.assertGreater(len(result["_entry_urls"]), 0)
        for entry_url in result["_entry_urls"]:
            self.assertRegex(entry_url, r"^https?://")

    def assert_common_fields(self, result, expected_kind, result_type):
        self.assertEqual(result["_type"], result_type)
        self.assertEqual(result["extractor"], expected_kind)
        self.assertIsInstance(result["id"], str)
        self.assertTrue(result["id"])
        self.assertIsInstance(result["title"], str)
        self.assertTrue(result["title"])
        self.assertRegex(result["webpage_url"], r"^https?://")

    def assert_formats(self, result, *, allow_unavailable=False):
        self.assertIsInstance(result["formats"], list)
        if not result["formats"]:
            if not allow_unavailable:
                self.fail("Expected at least one playable format")
            self.assertEqual(result["availability"], "premium_only")
            self.assertIsInstance(result["format_error"], str)
            self.assertTrue(result["format_error"])
            return
        for media_format in result["formats"]:
            self.assertRegex(media_format["url"], r"^https?://")
