import threading
from pathlib import Path

import pytest

from zingmp3_cli.downloader import Downloader
from zingmp3_cli.exceptions import ZingMp3Error


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

    def test_parses_hls_media_playlist(self):
        text = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-TARGETDURATION:6\n"
            "#EXTINF:6.0,\n"
            "seg1.ts\n"
            "#EXTINF:6.0,\n"
            "seg2.ts\n"
            "#EXT-X-ENDLIST\n"
        )
        assert Downloader._parse_hls_playlist(text, "http://host/path/") == (
            None,
            ["http://host/path/seg1.ts", "http://host/path/seg2.ts"],
        )

    def test_parses_hls_fmp4_init_segment(self):
        text = '#EXT-X-MAP:URI="init.mp4"\n#EXTINF:6.0,\nseg1.m4s\n'
        init, segments = Downloader._parse_hls_playlist(text, "http://host/")
        assert init == "http://host/init.mp4"
        assert segments == ["http://host/seg1.m4s"]

    def test_hls_playlist_with_encryption_falls_back(self):
        text = '#EXT-X-KEY:METHOD=AES-128,URI="key"\n#EXTINF:6.0,\nseg1.ts\n'
        assert Downloader._parse_hls_playlist(text, "http://host/") is None

    def test_hls_playlist_with_byterange_falls_back(self):
        text = "#EXT-X-BYTERANGE:1000@0\nseg1.mp4\n"
        assert Downloader._parse_hls_playlist(text, "http://host/") is None

    def test_empty_hls_playlist_falls_back(self):
        assert Downloader._parse_hls_playlist("#EXTM3U\n", "http://host/") is None

    def test_selects_highest_bandwidth_variant(self):
        text = (
            "#EXTM3U\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=360x640\n"
            "360.m3u8\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=720x1280\n"
            "720.m3u8\n"
        )
        assert (
            Downloader._select_variant(text, "http://host/master.m3u8")
            == "http://host/720.m3u8"
        )

    def test_hls_job_dirs_are_unique_per_run(self, tmp_path):
        temporary = tmp_path / ".video.part.mp4"
        first = Downloader._hls_job_dir(temporary)
        second = Downloader._hls_job_dir(temporary)
        assert first != second
        assert first.parent == tmp_path / ".zmp3"
        assert second.parent == tmp_path / ".zmp3"

    def test_download_segments_writes_files_and_concat_list(self, tmp_path):
        downloader = Downloader(client=None)
        job_dir = tmp_path / ".zmp3" / "job"

        def fake_save(url, path):
            path.write_bytes(url.encode())
            return len(url)

        downloader._save_segment = fake_save
        downloader._download_segments(
            "http://host/init.mp4",
            ["http://host/a.ts", "http://host/b.ts"],
            job_dir,
            description="test",
        )
        assert (job_dir / "init.mp4").read_bytes() == b"http://host/init.mp4"
        assert (job_dir / "000000.ts").read_bytes() == b"http://host/a.ts"
        assert (job_dir / "000001.ts").read_bytes() == b"http://host/b.ts"
        assert (job_dir / "list.txt").read_text().splitlines() == [
            "file 'init.mp4'",
            "file '000000.ts'",
            "file '000001.ts'",
        ]

    def test_failed_hls_download_removes_segments_folder(self, tmp_path):
        downloader = Downloader(client=None)
        temporary = tmp_path / ".video.part.mp4"
        downloader._load_media_playlist = lambda url, depth=2: ("seg1.ts\n", url)
        downloader._parse_hls_playlist = lambda text, base: (
            None,
            ["http://host/seg1.ts"],
        )

        def fail(url, path):
            raise ZingMp3Error("boom")

        downloader._save_segment = fail
        with pytest.raises(ZingMp3Error):
            downloader._download_hls(
                "http://host/video.m3u8",
                temporary,
                description="test",
                duration=None,
            )
        assert not temporary.exists()
        assert list((tmp_path / ".zmp3").iterdir()) == []

    def test_interrupted_hls_download_removes_segments_folder(self, tmp_path):
        downloader = Downloader(client=None)
        temporary = tmp_path / ".video.part.mp4"
        downloader._load_media_playlist = lambda url, depth=2: ("seg1.ts\n", url)
        downloader._parse_hls_playlist = lambda text, base: (
            None,
            ["http://host/seg0.ts", "http://host/seg1.ts"],
        )
        release = threading.Event()

        def fake_save(url, path):
            if url.endswith("seg0.ts"):
                raise KeyboardInterrupt
            release.wait(timeout=5)
            path.write_bytes(b"data")
            return 4

        downloader._save_segment = fake_save
        try:
            with pytest.raises(KeyboardInterrupt):
                downloader._download_hls(
                    "http://host/video.m3u8",
                    temporary,
                    description="test",
                    duration=None,
                )
            assert not temporary.exists()
            assert list((tmp_path / ".zmp3").iterdir()) == []
        finally:
            release.set()

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
