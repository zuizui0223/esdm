"""Synthetic WorldClim source ZIP hash and GeoTIFF metadata tests only."""
from __future__ import annotations
import hashlib, importlib.util, pathlib, tempfile, unittest, zipfile
from unittest.mock import patch
from scripts import neobat_worldclim_source_preflight as w

HAS_RASTERIO=importlib.util.find_spec("rasterio") is not None

def source_fixture():
    import rasterio
    import numpy as np
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
    entries={}
    for name in w.RASTERS.values():
        with MemoryFile() as mem:
            with mem.open(driver="GTiff",height=2,width=2,count=1,dtype="int16",
                          crs="EPSG:4326",transform=from_origin(-70,10,0.2,0.2),
                          nodata=-9999) as f:
                f.write(np.full((1,2,2),250,dtype="int16"))
            entries[name]=mem.read()
    temp=tempfile.TemporaryDirectory()
    path=pathlib.Path(temp.name)/"source.zip"
    with zipfile.ZipFile(path,"w") as z:
        for name,data in entries.items():z.writestr(name,data)
    return temp,path,entries

class TestWorldClimSource(unittest.TestCase):
    @unittest.skipUnless(HAS_RASTERIO,"optional rasterio required")
    def test_expected_archive_and_frozen_bio12_then_new_bio1(self):
        temp,path,entries=source_fixture()
        try:
            with patch.object(w,"ARCHIVE_SHA256",hashlib.sha256(path.read_bytes()).hexdigest()), \
                 patch.object(w,"BIO12_SHA256",hashlib.sha256(entries[w.RASTERS["BIO12"]]).hexdigest()):
                result=w.inspect_source(path)
            self.assertEqual(set(result),{"BIO1","BIO12"})
            self.assertEqual(result["BIO1"]["crs"],"EPSG:4326")
            self.assertEqual(result["BIO12"]["band_count"],1)
            self.assertEqual(result["BIO1"]["width"],2)
        finally:temp.cleanup()

    def test_wrong_source_byte_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/"archive.zip"
            p.write_bytes(b"not the frozen climate bytes")
            with self.assertRaisesRegex(RuntimeError,"WORLDCLIM_ARCHIVE_SHA_MISMATCH"):
                w.inspect_source(p)

    @unittest.skipUnless(HAS_RASTERIO,"optional rasterio required")
    def test_bio12_changed_stops(self):
        temp,path,entries=source_fixture()
        try:
            with patch.object(w,"ARCHIVE_SHA256",hashlib.sha256(path.read_bytes()).hexdigest()), \
                 patch.object(w,"BIO12_SHA256","0"*64):
                with self.assertRaisesRegex(RuntimeError,"WORLDCLIM_FROZEN_BIO12_MISMATCH"):
                    w.inspect_source(path)
        finally:temp.cleanup()

if __name__=="__main__":
    unittest.main()
