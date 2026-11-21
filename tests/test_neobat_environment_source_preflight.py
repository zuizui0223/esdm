"""Pure synthetic source metadata tests for NeoBat environmental predictor preflight."""
from __future__ import annotations
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from scripts import neobat_environment_source_preflight as g


def tif(crs="EPSG:4326",bands=1):
    with MemoryFile() as mem:
        with mem.open(driver="GTiff",height=128,width=128,count=bands,dtype="int16",
                      crs=crs,transform=from_origin(-75,6,.01,.01),nodata=-9999) as ds:
            for band in range(1,bands+1):
                ds.write(np.zeros((128,128),dtype=np.int16),band)
        return mem.read()


class TestEnvironmentalSource(unittest.TestCase):
    def test_well_formed_terrain_geotiff(self):
        m=g.raster_meta(tif())
        self.assertEqual(m["crs"],"EPSG:4326")
        self.assertEqual(m["band_count"],1)
        self.assertEqual(m["nodata"],-9999)
        self.assertEqual(m["width"],128)

    def test_wrong_crs_and_band_number_stop(self):
        with self.assertRaisesRegex(RuntimeError,"TERRAIN_RASTER_BAND_OR_CRS"):
            g.raster_meta(tif(crs="EPSG:3857"))
        with self.assertRaisesRegex(RuntimeError,"TERRAIN_RASTER_BAND_OR_CRS"):
            g.raster_meta(tif(bands=2))

    def test_two_original_download_hashes_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            def fake_download(url,target,limit=None):
                with zipfile.ZipFile(target,"w") as z:
                    z.writestr(g.ELEV_MEMBER,tif())
                contents=target.read_bytes()
                return hashlib.sha256(contents).hexdigest(),len(contents)
            with patch.object(g.climate,"checksum_download",side_effect=fake_download):
                result=g.terrain_source_pin(Path(directory))
        self.assertEqual(result["download_count"],2)
        self.assertEqual(result["metadata"]["crs"],"EPSG:4326")

    def test_terrain_sha_drift_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            counter=[0]
            def fake_download(url,target,limit=None):
                counter[0]+=1
                with zipfile.ZipFile(target,"w") as z:
                    z.writestr(g.ELEV_MEMBER,tif()+bytes([counter[0]]))
                raw=target.read_bytes()
                return hashlib.sha256(raw).hexdigest(),len(raw)
            with patch.object(g.climate,"checksum_download",side_effect=fake_download):
                with self.assertRaisesRegex(RuntimeError,"TWO_GET_SHA_DRIFT"):
                    g.terrain_source_pin(Path(directory))


if __name__=="__main__":
    unittest.main()
