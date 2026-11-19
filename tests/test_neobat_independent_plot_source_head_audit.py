"""Source-free tests for exact HEAD-only independent botanical source probes."""
from __future__ import annotations
import unittest
import urllib.error
from scripts import neobat_independent_plot_source_head_audit as m


class FakeResponse:
    status=200
    headers={"Content-Type":"application/zip","Content-Length":"1234567",
             "ETag":'"locked"'}
    def __init__(self):self.url="https://idata.idiv.de/ddm/Data/DownloadZip/3474?version=5047"
    def geturl(self):return self.url
    def __enter__(self):return self
    def __exit__(self,*args):pass


class TestHeads(unittest.TestCase):
    def test_no_get_and_no_biological_data_opened(self):
        def fake(request,timeout):
            self.assertEqual(request.get_method(),"HEAD")
            self.assertLessEqual(timeout,18)
            return FakeResponse()
        row=m.probe("frozen","https://idata.idiv.de/ddm/Data/DownloadZip/3474?version=5047",
                    opener=fake)
        self.assertEqual(row["status"],"HEAD_HTTP_RESPONSE_ONLY")
        self.assertEqual(row["content_length"],"1234567")
        self.assertEqual(row["biological_response_bytes_read"],0)
        self.assertFalse(row["full_dataset_downloaded"])

    def test_denied_access_is_not_promoted(self):
        def denied(request,timeout):
            raise urllib.error.HTTPError(request.full_url,403,"Forbidden",None,None)
        row=m.probe("restricted","https://repository.si.edu/valid",opener=denied)
        self.assertEqual(row["status"],"HEAD_HTTP_STOP")
        self.assertEqual(row["http_status"],403)
        self.assertEqual(row["biological_response_bytes_read"],0)

    def test_fixed_source_denominator(self):
        self.assertEqual(len(m.SOURCES),4)
        self.assertEqual(len({name for name,url in m.SOURCES}),4)
        self.assertTrue(all(url.startswith("https://") for name,url in m.SOURCES))


if __name__=="__main__":
    unittest.main()
