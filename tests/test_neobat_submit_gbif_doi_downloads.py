"""Offline-only guards. No genuine GBIF request is sent by tests."""
from __future__ import annotations
import copy, hashlib, json, os, pathlib, tempfile, unittest
from unittest.mock import patch
from urllib.error import HTTPError
import io
from scripts import neobat_submit_gbif_doi_downloads as submit

def fixtures():
    bats=[{"bat":f"Bat{i} species{i}","status":"GBIF_COUNTS_ONLY",
           "match":{"usageKey":100+i}} for i in range(26)]
    plants=[{"plant":f"Plant{i} species{i}","status":"GBIF_PLANT_COUNTS_ONLY",
             "match":{"usageKey":2000+i}} for i in range(255)]
    countries=["AR","BO","BR","BZ","CL","CO","CR","CU","CW","DO","EC","GF","GT","GY","HN","HT","JM","MX","NI","PA","PE","PR","PY","SR","SV","TT","UY","VE","BS"]
    def pred(keys):
        return {"type":"and","predicates":[
            {"type":"in","key":"TAXON_KEY","values":list(map(str,keys))},
            {"type":"equals","key":"HAS_COORDINATE","value":"true"},
            {"type":"equals","key":"HAS_GEOSPATIAL_ISSUE","value":"false"},
            {"type":"equals","key":"OCCURRENCE_STATUS","value":"PRESENT"},
            {"type":"greaterThanOrEquals","key":"YEAR","value":"2000"},
            {"type":"lessThanOrEquals","key":"YEAR","value":"2025"},
            {"type":"in","key":"COUNTRY","values":countries}
        ]}
    draft={
        "status":"DRAFT_NOT_DISPATCHED",
        "download_request_templates":{
            "bat":{"format":"SIMPLE_CSV","predicate":pred(range(100,126)),"sendNotification":False},
            "plant":{"format":"SIMPLE_CSV","predicate":pred(range(2000,2255)),"sendNotification":False}
        }
    }
    return draft,{"records":bats},{"plants":plants}

class TestGBIFSubmission(unittest.TestCase):
    def test_verified_exact_taxa_and_secret_not_in_schema(self):
        d,b,p=fixtures()
        result=submit.prepare(d,b,p,"test-user","user@example.test")
        self.assertEqual(len(result),2)
        self.assertEqual(result["bat"]["creator"],"test-user")
        self.assertEqual(result["plant"]["notificationAddresses"],["user@example.test"])
        self.assertNotIn("checklistKey",result["bat"])
        self.assertEqual(len(next(q for q in result["plant"]["predicate"]["predicates"]
                                if q["key"]=="TAXON_KEY")["values"]),255)

    def test_mismatch_taxon_denominator_and_key_rejected(self):
        d,b,p=fixtures()
        p["plants"].pop()
        with self.assertRaisesRegex(RuntimeError,"TAXON_DENOMINATOR_CHANGED"):
            submit.prepare(d,b,p,"x","x@example.test")
        d,b,p=fixtures()
        d["download_request_templates"]["bat"]["predicate"]["predicates"][0]["values"][0]="999"
        with self.assertRaisesRegex(RuntimeError,"TAXON_KEY_MISMATCH"):
            submit.prepare(d,b,p,"x","x@example.test")

    def test_unfrozen_filter_or_mixed_checklist_fails_closed(self):
        d,b,p=fixtures()
        d["download_request_templates"]["bat"]["predicate"]["predicates"][1]["value"]="false"
        with self.assertRaisesRegex(RuntimeError,"MISSING_OR_CHANGED_FILTER"):
            submit.prepare(d,b,p,"x","x@example.test")
        d,b,p=fixtures()
        d["download_request_templates"]["bat"]["predicate"]["predicates"][0]["checklistKey"]="CoL-key"
        with self.assertRaisesRegex(RuntimeError,"MIXED_TAXONOMY_NAMESPACE_STOP"):
            submit.prepare(d,b,p,"x","x@example.test")

    def test_pinned_source_git_blob_check(self):
        payload=b'{"example":1}\n'
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"source.json"
            p.write_bytes(payload)
            expected=submit.blob_sha(payload)
            self.assertEqual(submit.load_exact(str(p),expected)[0],{"example":1})
            with self.assertRaisesRegex(RuntimeError,"PINNED_INPUT_BLOB_MISMATCH"):
                submit.load_exact(str(p),"0"*40)

    def test_submit_basic_auth_only_to_GBIF_endpoint_and_receipt_not_secret(self):
        with patch.object(submit,"perform",return_value='9999924-261119000000000') as request:
            k,digest=submit.submit({"test":1},"user","secret")
        self.assertEqual(k,"9999924-261119000000000")
        self.assertEqual(len(digest),64)
        args,kwargs=request.call_args
        self.assertEqual(args[0],"https://api.gbif.org/v1/occurrence/download/request")
        self.assertEqual(kwargs["method"],"POST")
        self.assertIn("Authorization",kwargs["headers"])
        self.assertNotIn("secret",kwargs["data"].decode())

    def test_http_error_is_only_code_not_secrets(self):
        error=HTTPError("https://api.gbif.org",401,"Unauthorized",{},io.BytesIO(b"email=user@secret.test"))
        with patch.object(submit,"urlopen",side_effect=error):
            with self.assertRaisesRegex(RuntimeError,"GBIF_HTTP_401") as err:
                submit.perform("https://api.gbif.org/v1/occurrence/download/request")
        self.assertNotIn("secret.test",str(err.exception))

if __name__=="__main__":
    unittest.main()
