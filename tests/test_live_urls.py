"""Tests against real Zing MP3 URLs and APIs."""

import json
import re

import pytest

from zingmp3_cli import ZingMp3Crawler


@pytest.fixture(scope="module")
def crawler():
    return ZingMp3Crawler(timeout=30)


@pytest.mark.parametrize(
    "url",
    (
        "https://zingmp3.vn/bai-hat/Xa-Mai-Xa-Bao-Thy/ZWZB9WAB.html",
        "https://zingmp3.vn/video-clip/Suong-Hoa-Dua-Loi-K-ICM-RYO/ZO8ZF7C7.html",
        "https://zingmp3.vn/embed/song/ZWZEI76B?start=false",
    ),
)
def test_song_video_and_embed_media(crawler, url):
    assert_media(extract(crawler, url))


def test_album(crawler):
    result = extract(
        crawler,
        "https://zingmp3.vn/album/Anh-Khang-Hits-Collection-Anh-Khang/"
        "AKw4CWcI4D2E.html",
    )
    assert_collection(result, "zingmp3:album")


@pytest.mark.parametrize(
    "url",
    (
        "https://zingmp3.vn/zing-chart",
        "https://zingmp3.vn/moi-phat-hanh",
        "https://zingmp3.vn/top100",
    ),
)
def test_chart_home_variants(crawler, url):
    assert_collection(extract(crawler, url), "zingmp3:chart-home")


def test_week_chart(crawler):
    result = extract(
        crawler,
        "https://zingmp3.vn/zing-chart-tuan/Bai-hat-Viet-Nam/IWZ9Z08I.html",
    )
    assert_collection(result, "zingmp3:week-chart")


def test_music_video_chart(crawler):
    result = extract(
        crawler,
        "https://zingmp3.vn/the-loai-video/Viet-Nam/IWZ9Z08I.html",
    )
    assert_collection(result, "zingmp3:chart-music-video")


@pytest.mark.parametrize(
    "url",
    (
        "https://zingmp3.vn/Mr-Siro/bai-hat",
        "https://zingmp3.vn/Mr-Siro/album",
        "https://zingmp3.vn/Mr-Siro/single",
        "https://zingmp3.vn/Mr-Siro/video",
    ),
)
def test_artist_branches(crawler, url):
    assert_collection(extract(crawler, url), "zingmp3:user")


@pytest.mark.parametrize("release_type", ("song", "album"))
def test_new_release_branches(crawler, release_type):
    url = f"https://zingmp3.vn/new-release/{release_type}"
    assert_collection(extract(crawler, url), "zingmp3:user")


def test_hub(crawler):
    result = extract(crawler, "https://zingmp3.vn/hub/Nhac-Moi/IWZ9Z0CA.html")
    assert_collection(result, "zingmp3:hub")


def test_live_radio(crawler):
    result = extract(crawler, "https://zingmp3.vn/liveradio/IWZ979UB.html")
    assert_common_fields(result, "zingmp3:liveradio", "live")
    assert result["is_live"] is True
    assert_formats(result)


def extract(crawler, url):
    result = crawler.extract(url, resolve=False)
    # Verify that the public result can be emitted as valid JSON.
    return json.loads(json.dumps(result, ensure_ascii=False))


def assert_media(result):
    assert_common_fields(result, "zingmp3", "media")
    assert isinstance(result["duration"], int)
    assert_formats(result, allow_unavailable=True)


def assert_collection(result, expected_kind):
    assert_common_fields(result, expected_kind, "playlist")
    assert isinstance(result["_entry_urls"], list)
    assert result["_entry_urls"]
    for entry_url in result["_entry_urls"]:
        assert re.match(r"^https?://", entry_url)


def assert_common_fields(result, expected_kind, result_type):
    assert result["_type"] == result_type
    assert result["extractor"] == expected_kind
    assert isinstance(result["id"], str)
    assert result["id"]
    assert isinstance(result["title"], str)
    assert result["title"]
    assert re.match(r"^https?://", result["webpage_url"])


def assert_formats(result, *, allow_unavailable=False):
    assert isinstance(result["formats"], list)
    if not result["formats"]:
        assert allow_unavailable, "Expected at least one playable format"
        assert result["availability"] == "premium_only"
        assert isinstance(result["format_error"], str)
        assert result["format_error"]
        return
    for media_format in result["formats"]:
        assert re.match(r"^https?://", media_format["url"])
