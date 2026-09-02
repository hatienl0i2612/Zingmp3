import pytest

from extractors import ExtractorRegistry
from zingmp3_cli.client import ZingMp3Client
from zingmp3_cli.exceptions import ZingMp3Error


@pytest.fixture
def registry():
    return ExtractorRegistry(ZingMp3Client())


@pytest.mark.parametrize(
    ("url", "expected_kind"),
    (
        ("https://zingmp3.vn/bai-hat/X/ZWZB9WAB.html", "zingmp3"),
        ("https://zingmp3.vn/video-clip/X/ZO8ZF7C7.html", "zingmp3"),
        ("https://zingmp3.vn/embed/song/ZWZEI76B?start=false", "zingmp3"),
        ("https://zingmp3.vn/album/X/ZOC7WUZC.html", "zingmp3:album"),
        ("https://mp3.zing.vn/playlist/X/IWCAACCB.html", "zingmp3:album"),
        ("https://zingmp3.vn/zing-chart", "zingmp3:chart-home"),
        ("https://zingmp3.vn/moi-phat-hanh", "zingmp3:chart-home"),
        ("https://zingmp3.vn/top100", "zingmp3:chart-home"),
        (
            "https://zingmp3.vn/zing-chart-tuan/X/IWZ9Z08I.html",
            "zingmp3:week-chart",
        ),
        (
            "https://zingmp3.vn/the-loai-video/Viet-Nam/IWZ9Z08I.html",
            "zingmp3:chart-music-video",
        ),
        ("https://zingmp3.vn/Mr-Siro/bai-hat", "zingmp3:user"),
        ("https://zingmp3.vn/new-release/album", "zingmp3:user"),
        ("https://zingmp3.vn/hub/Nhac-Moi/IWZ9Z0CA.html", "zingmp3:hub"),
        ("https://zingmp3.vn/liveradio/IWZ979UB.html", "zingmp3:liveradio"),
    ),
)
def test_all_current_url_kinds_are_classified(registry, url, expected_kind):
    extractor, _ = registry.match(url)
    assert extractor.KIND == expected_kind


@pytest.mark.parametrize(
    "url",
    ("https://example.com/song", "https://zingmp3.vn/unknown"),
)
def test_rejects_unsupported_urls(registry, url):
    with pytest.raises(ZingMp3Error):
        registry.match(url)


def test_accepts_markdown_link_input(registry):
    url = (
        "[Zing MP3](https://zingmp3.vn/album/"
        "Anh-Khang-Hits-Collection-Anh-Khang/AKw4CWcI4D2E.html)"
    )
    extractor, values = registry.match(url)
    assert extractor.KIND == "zingmp3:album"
    assert values["id"] == "AKw4CWcI4D2E"
