from zingmp3_cli.crawler import ZingMp3Crawler


class FakeRegistry:
    def __init__(self):
        self.calls = []

    def extract(self, url):
        self.calls.append(url)
        if url.endswith("/album"):
            return {
                "_type": "playlist",
                "id": "album",
                "_entry_urls": [
                    "https://zingmp3.vn/song/one",
                    "https://zingmp3.vn/song/two",
                ],
            }
        return {"_type": "media", "id": url.rsplit("/", 1)[-1], "formats": [{}]}


def make_crawler():
    crawler = object.__new__(ZingMp3Crawler)
    crawler.registry = FakeRegistry()
    return crawler


class TestCrawlerResolution:
    def test_lazy_iterator_resolves_only_the_requested_entry(self):
        crawler = make_crawler()
        root = crawler.extract("https://zingmp3.vn/album", resolve=False)
        entries = crawler.iter_media(root)

        assert crawler.registry.calls == ["https://zingmp3.vn/album"]
        assert next(entries)["id"] == "one"
        assert crawler.registry.calls == [
            "https://zingmp3.vn/album",
            "https://zingmp3.vn/song/one",
        ]
        assert next(entries)["id"] == "two"

    def test_eager_extract_resolves_every_entry(self):
        crawler = make_crawler()
        result = crawler.extract("https://zingmp3.vn/album")

        assert [entry["id"] for entry in result["entries"]] == ["one", "two"]
        assert crawler.registry.calls == [
            "https://zingmp3.vn/album",
            "https://zingmp3.vn/song/one",
            "https://zingmp3.vn/song/two",
        ]
