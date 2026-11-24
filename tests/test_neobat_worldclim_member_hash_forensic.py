"""Source-only WorldClim archive hash diagnosis synthetic tests, no climate values."""
import hashlib, pathlib, tempfile, unittest, zipfile
from unittest.mock import patch
from scripts import neobat_worldclim_member_hash_forensic as f
from scripts import neobat_worldclim_source_preflight as w

class WorldClimHashAuditTests(unittest.TestCase):
    def test_archive_pin_required_but_inner_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"source.zip"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr(w.RASTERS["BIO1"],b"fake-bio1-header")
                z.writestr(w.RASTERS["BIO12"],b"fake-bio12-header")
            h=hashlib.sha256(p.read_bytes()).hexdigest()
            with patch.object(w,"ARCHIVE_SHA256",h),patch.object(w,"BIO12_SHA256","0"*64):
                out=f.inspect_members(p)
            self.assertTrue(out["archive_sha_matches_fixed_reference"])
            self.assertFalse(out["members"]["BIO12"]["matches_previous_pin"])
            self.assertIsNone(out["members"]["BIO1"]["matches_previous_pin"])
            self.assertTrue(out["no_ecological_responses_opened"])
            self.assertTrue(out["not_a_replacement_preflight"])

    def test_archive_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"source.zip"
            p.write_bytes(b"not-frozen-source")
            with self.assertRaisesRegex(ValueError,"FROZEN_WORLDCLIM_ARCHIVE_SHA_STOP"):
                f.inspect_members(p)

    def test_missing_member_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/"source.zip"
            with zipfile.ZipFile(p,"w") as z:z.writestr("only.zip",b"fake")
            h=hashlib.sha256(p.read_bytes()).hexdigest()
            with patch.object(w,"ARCHIVE_SHA256",h):
                with self.assertRaisesRegex(ValueError,"WORLDCLIM_MISSING_OR_DUPLICATE_MEMBER"):
                    f.inspect_members(p)

if __name__=="__main__":
    unittest.main()
