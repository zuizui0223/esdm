"""Offline source-only ZIP/DOI receipt tests. No actual GBIF downloads or events."""
from __future__ import annotations
import pathlib, tempfile, unittest, zipfile
from scripts import neobat_gbif_archive_header_preflight as g

B="0001156-261118162104854"
P="0001157-261118162104854"

def receipts():
    sub={"status":"BOTH_DOWNLOADS_REQUESTED","download_keys":{"bat":B,"plant":P}}
    p={"status":"BOTH_DOIS_VERIFIED_BY_PUBLIC_GBIF_METADATA",
       "downloads":{
        x:{"status":"SUCCEEDED","download_key":key,"doi":"10.15468/dl.abc123",
           "download_link":"https://api.gbif.org/v1/occurrence/download/request/"+key+".zip",
           "GBIF_total_records":300}
        for x,key in (("bat",B),("plant",P))}
      }
    return sub,p

class TestGBIFZipPreflight(unittest.TestCase):
    def test_two_exact_keys_and_dois_validated(self):
        r=g.verified_source(*receipts())
        self.assertEqual(set(r),{"bat","plant"})
        self.assertEqual(r["bat"]["download_key"],B)
        self.assertEqual(r["plant"]["doi"],"10.15468/dl.abc123")

    def test_no_premature_download_and_wrong_key_rejected(self):
        s,p=receipts()
        p["status"]="POLL_ONLY"
        with self.assertRaisesRegex(RuntimeError,"GBIF_DOIS_NOT_YET_VERIFIED"):
            g.verified_source(s,p)
        s,p=receipts()
        p["downloads"]["bat"]["download_key"]="wrong"
        with self.assertRaisesRegex(RuntimeError,"POLL_KEY_DOES_NOT_MATCH_SUBMISSION"):
            g.verified_source(s,p)

    def test_only_gbif_host_and_proper_doi(self):
        s,p=receipts()
        p["downloads"]["plant"]["download_link"]="https://evil.test/x.zip"
        with self.assertRaisesRegex(RuntimeError,"ARCHIVE_SOURCE_NOT_GBIF_API"):
            g.verified_source(s,p)
        s,p=receipts()
        p["downloads"]["bat"]["doi"]="10.1111/fake"
        with self.assertRaisesRegex(RuntimeError,"PUBLIC_DOI_NOT_VALID"):
            g.verified_source(s,p)

    def test_known_header_without_reading_rows(self):
        cols=["gbifID","datasetKey","taxonKey","countryCode",
              "decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters"]
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/"source.zip"
            with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("data.csv","\t".join(cols)+"\n"+"abc\tdef\t1\tBR\t0\t0\t30\n"*10)
            x=g.inspect_zip(path)
        self.assertEqual(x["header_columns"],cols)
        self.assertTrue(x["coordinate_uncertainty_column_present"])
        self.assertTrue(x["not_a_response_row_opening"])

    def test_missing_critical_column_is_not_forgiven(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/"source.zip"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("records.tsv","gbifID\ttaxonKey\tcountryCode\tdecimalLongitude\n"*10)
            with self.assertRaisesRegex(RuntimeError,"MISSING_CRITICAL_GBIF_COLUMNS"):
                g.inspect_zip(p)

if __name__=="__main__":
    unittest.main()
