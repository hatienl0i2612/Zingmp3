from pathlib import Path

import pytest

from zingmp3_cli.downloader import Downloader


class TestDownloader:
    def test_prefers_lossless_audio(self):
        info = {
            "id": "test",
            "formats": [
                {"format_id": "320", "tbr": 320, "protocol": "https"},
                {"format_id": "lossless", "protocol": "https"},
            ],
        }
        assert Downloader.best_format(info)["format_id"] == "lossless"

    def test_prefers_highest_video_resolution(self):
        info = {
            "id": "test",
            "formats": [
                {"format_id": "hls-360", "height": 360, "protocol": "m3u8"},
                {"format_id": "hls-720", "height": 720, "protocol": "m3u8"},
            ],
        }
        assert Downloader.best_format(info)["format_id"] == "hls-720"

    def test_download_finishes_before_requesting_the_next_entry(self, tmp_path, capsys):
        events = []

        def entries():
            events.append("resolve-one")
            yield self._media("one")
            events.append("resolve-two")
            yield self._media("two")

        downloader = Downloader(client=None)
        downloader._download_one = lambda media_format, target, **kwargs: events.append(
            f"download-{media_format['url']}"
        )
        downloads = downloader.iter_downloads(entries(), tmp_path, is_playlist=True)
        assert events == []
        assert isinstance(next(downloads), Path)
        assert events == ["resolve-one", "download-one"]
        assert isinstance(next(downloads), Path)
        assert events == [
            "resolve-one",
            "download-one",
            "resolve-two",
            "download-two",
        ]
        with pytest.raises(StopIteration):
            next(downloads)
        assert capsys.readouterr().err == "\n"

    def test_parses_ffmpeg_progress_time(self):
        assert Downloader._ffmpeg_progress_seconds("out_time_us", "1500000") == 1.5
        assert Downloader._ffmpeg_progress_seconds("out_time", "01:02:03.5") == 3723.5
        assert Downloader._ffmpeg_progress_seconds("speed", "1.0x") is None

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
