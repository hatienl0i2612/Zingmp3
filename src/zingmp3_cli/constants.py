"""Constants shared by the API client and extractors."""

DOMAIN = "https://zingmp3.vn"
API_KEY = "X5BM3w8N7MKozC0B85o4KMlzLZKhV00y"
API_SECRET = b"acOrvUS15XRW2o9JksiK1KgQ6Vbds8ZW"
API_VERSION = "1.19.1"
SIGNED_PARAMS = frozenset({"ctime", "id", "type", "page", "count", "version"})
PER_PAGE = 50

API_SLUGS = {
    "bai-hat": "/api/v2/page/get/song",
    "embed": "/api/v2/page/get/song",
    "video-clip": "/api/v2/page/get/video",
    "lyric": "/api/v2/lyric/get/lyric",
    "song-streaming": "/api/v2/song/get/streaming",
    "liveradio": "/api/v2/livestream/get/info",
    "playlist": "/api/v2/page/get/playlist",
    "album": "/api/v2/page/get/playlist",
    "zing-chart": "/api/v2/page/get/chart-home",
    "zing-chart-tuan": "/api/v2/page/get/week-chart",
    "moi-phat-hanh": "/api/v2/page/get/newrelease-chart",
    "the-loai-video": "/api/v2/video/get/list",
    "info-artist": "/api/v2/page/get/artist",
    "user-list-song": "/api/v2/song/get/list",
    "user-list-video": "/api/v2/video/get/list",
    "hub": "/api/v2/page/get/hub-detail",
    "new-release": "/api/v2/chart/get/new-release",
    "top100": "/api/v2/page/get/top-100",
}

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Referer": f"{DOMAIN}/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    ),
}
