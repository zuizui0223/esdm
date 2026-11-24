"""Offline DOI poll coverage; never calls authenticated GBIF POST."""
from __future__ import annotations
import unittest
from scripts import neobat_poll_gbif_doi_downloads as poll

K1="1234567-261119000000000"
K2="1234568-261119000000000"

class TestGBIFDOIPoll(unittest.TestCase):
    def test_no_keys_refuses_to_poll(self):
        with self.assertRaisesRegex(ValueError,"NO_ACCEPTED_SUBMISSIONS_RECORDED"):
            poll.poll_receipt({"status":"SUBMISSION_STOP","download_keys":{}})
        with self.assertRaisesRegex(ValueError,"NO_DOWNLOAD_KEYS"):
            poll.poll_receipt({"status":"BOTH_DOWNLOADS_REQUESTED","download_keys":{}})

    def test_exact_two_downloads_succeeded_mint_two_real_dois(self):
        submitted={"status":"BOTH_DOWNLOADS_REQUESTED","download_keys":{"bat":K1,"plant":K2}}
        def server(url):
            key=url.rsplit("/",1)[-1]
            return {"key":key,"status":"SUCCEEDED","doi":
                    "10.15468/dl.abc123" if key==K1 else "10.15468/dl.def456",
                    "totalRecords":123,"numberDatasets":5}
        result=poll.poll_receipt(submitted,http_get=server)
        self.assertEqual(result["status"],"BOTH_DOIS_VERIFIED_BY_PUBLIC_GBIF_METADATA")
        self.assertEqual(result["downloads"]["bat"]["doi"],"10.15468/dl.abc123")
        self.assertTrue(result["no_new_download_requests"])
        self.assertIsNone(result["ecological_result"])

    def test_running_does_not_claim_doi(self):
        submitted={"status":"BOTH_DOWNLOADS_REQUESTED","download_keys":{"bat":K1,"plant":K2}}
        result=poll.poll_receipt(submitted,http_get=lambda url:{
            "status":"RUNNING","key":url.rsplit("/",1)[-1],"doi":None})
        self.assertEqual(result["status"],"POLL_ONLY")
        self.assertIsNone(result["downloads"]["bat"]["doi"])
        self.assertFalse(result["downloads"]["bat"]["eligible_for_next_full_source_verification"])

    def test_unknown_status_does_not_promote(self):
        ret=poll.inspect_key(K1,lambda url:{"status":"GARBAGE","key":K1})
        self.assertEqual(ret["status"],"POLL_UNKNOWN_STATUS")

    def test_strict_valid_doi(self):
        self.assertIsNone(poll.clean_doi("https://github.com/"))
        self.assertIsNone(poll.clean_doi("10.1234/not-gbif"))
        self.assertEqual(poll.clean_doi("https://doi.org/10.15468/dl.abc123"),
                         "https://doi.org/10.15468/dl.abc123")

if __name__=="__main__":
    unittest.main()
