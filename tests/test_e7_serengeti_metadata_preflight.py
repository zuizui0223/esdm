"""Purely synthetic tests for HTTP HEAD-only E7 preflight."""
import unittest
from urllib.error import HTTPError
from scripts.e7_serengeti_metadata_preflight import SEASONS, head_one, metadata_url, run


class FakeResponse:
    status = 200
    def __init__(self, size):
        self.headers={"Content-Length": str(size), "ETag": '"s0abc"', "Last-Modified": "Mon, 19 Oct 2026 01:00:00 GMT"}
    def info(self): return self.headers
    def getcode(self): return self.status
    def __enter__(self): return self
    def __exit__(self, *a): return False


def okay(req, *, timeout):
    assert req.get_method()=="HEAD"
    assert req.full_url.startswith("https://lilawildlife.blob.core.windows.net/")
    return FakeResponse(128_000)


class TestSerengetiTransport(unittest.TestCase):
    def test_fixed_seasons_and_urls(self):
        self.assertEqual(SEASONS, (1,6,11))
        self.assertTrue(metadata_url(1).endswith("/SnapshotSerengetiS01.json.zip"))
        self.assertTrue(metadata_url(11).endswith("/SnapshotSerengetiS11.json.zip"))
        with self.assertRaises(ValueError):
            metadata_url(12)

    def test_only_request_headers_without_opening_biological_rows(self):
        result=run(opener=okay)
        self.assertEqual(result["status"],"RESPONSE_BLIND_HEAD_PASS")
        self.assertEqual(result["biological_bytes_downloaded"],0)
        self.assertEqual(result["source_json_rows_read"],0)
        self.assertEqual(len(result["records"]),3)
        self.assertEqual(result["records"][1]["content_bytes_reported"],128000)

    def test_failed_auth_or_missing_blob_is_transport_not_ecology(self):
        def blocked(req, *, timeout):
            raise HTTPError(req.full_url,403,"forbidden",None,None)
        result=run(opener=blocked)
        self.assertEqual(result["status"],"RESPONSE_BLIND_TRANSPORT_STOP")
        self.assertTrue(all(r["http_status"]==403 for r in result["records"]))
        self.assertEqual(result["source_json_rows_read"],0)


if __name__=="__main__":
    unittest.main()
