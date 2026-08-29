import unittest
from urllib.parse import parse_qs, urlsplit

from zingmp3_cli.client import ZingMp3Client
from zingmp3_cli.constants import API_KEY, API_VERSION
from zingmp3_cli.exceptions import ZingMp3Error


class ZingMp3ClientTests(unittest.TestCase):
    def test_api_signature_has_current_required_fields(self):
        url = ZingMp3Client.build_api_url("bai-hat", {"id": "ZWZB9WAB"})
        query = parse_qs(urlsplit(url).query)

        self.assertEqual(query["apiKey"], [API_KEY])
        self.assertEqual(query["version"], [API_VERSION])
        self.assertEqual(len(query["sig"][0]), 128)

    def test_custom_headers_are_applied(self):
        client = ZingMp3Client(headers=["X-Test: custom value"])
        self.assertEqual(client.session.headers["X-Test"], "custom value")

    def test_invalid_header_is_rejected(self):
        with self.assertRaises(ZingMp3Error):
            ZingMp3Client(headers=["invalid"])
