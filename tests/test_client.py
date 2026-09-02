from urllib.parse import parse_qs, urlsplit

import pytest

from zingmp3_cli.client import ZingMp3Client
from zingmp3_cli.constants import API_KEY, API_VERSION
from zingmp3_cli.exceptions import ZingMp3Error


class TestZingMp3Client:
    def test_api_signature_has_current_required_fields(self):
        url = ZingMp3Client.build_api_url("bai-hat", {"id": "ZWZB9WAB"})
        query = parse_qs(urlsplit(url).query)

        assert query["apiKey"] == [API_KEY]
        assert query["version"] == [API_VERSION]
        assert len(query["sig"][0]) == 128

    def test_custom_headers_are_applied(self):
        client = ZingMp3Client(headers=["X-Test: custom value"])
        assert client.session.headers["X-Test"] == "custom value"

    def test_invalid_header_is_rejected(self):
        with pytest.raises(ZingMp3Error):
            ZingMp3Client(headers=["invalid"])
