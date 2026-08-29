import tempfile
import unittest
from pathlib import Path

from zingmp3_cli.downloader import Downloader


class DownloaderTests(unittest.TestCase):
    def test_prefers_lossless_audio(self):
        info = {
            "id": "test",
            "formats": [
                {"format_id": "320", "tbr": 320, "protocol": "https"},
                {"format_id": "lossless", "protocol": "https"},
            ],
        }
        self.assertEqual(Downloader.best_format(info)["format_id"], "lossless")

    def test_prefers_highest_video_resolution(self):
        info = {
            "id": "test",
            "formats": [
                {"format_id": "hls-360", "height": 360, "protocol": "m3u8"},
                {"format_id": "hls-720", "height": 720, "protocol": "m3u8"},
            ],
        }
        self.assertEqual(Downloader.best_format(info)["format_id"], "hls-720")

    def test_download_finishes_before_requesting_the_next_entry(self):
        events = []

        def entries():
            events.append("resolve-one")
            yield self._media("one")
            events.append("resolve-two")
            yield self._media("two")

        downloader = Downloader(client=None)
        downloader._download_one = lambda media_format, target: events.append(
            f"download-{media_format['url']}"
        )
        with tempfile.TemporaryDirectory() as directory:
            downloads = downloader.iter_downloads(
                entries(), directory, is_playlist=True
            )
            self.assertEqual(events, [])
            self.assertIsInstance(next(downloads), Path)
            self.assertEqual(events, ["resolve-one", "download-one"])
            self.assertIsInstance(next(downloads), Path)
            self.assertEqual(
                events,
                ["resolve-one", "download-one", "resolve-two", "download-two"],
            )
            with self.assertRaises(StopIteration):
                next(downloads)

    @staticmethod
    def _media(identifier):
        return {
            "_type": "media",
            "id": identifier,
            "title": identifier,
            "formats": [
                {
                    "format_id": "128",
                    "ext": "mp3",
                    "tbr": 128,
                    "protocol": "https",
                    "url": identifier,
                }
            ],
        }
