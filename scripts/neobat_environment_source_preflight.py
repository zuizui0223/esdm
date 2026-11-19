"""Response-blind NeoBat climate/elevation/forest *source header* verification.

No GBIF occurrence, original raster pixels or ecological model is saved.
WorldCover COG is one frozen tile *only*; it never qualifies a full forest map.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import tempfile
import zipfile
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from scripts import neobat_worldclim_source_preflight as climate

ELEV_URL="https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_elev.zip"
ELEV_MEMBER="wc2.1_10m_elev.tif"
FOREST_TILE_URL="https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N03W075_Map.tif"
MAX_ELEV_ZIP=30_000_000
DESIGN="docs/replication/NEOBAT_ABIOTIC_TERRAIN_FOREST_SOURCE_PREFLIGHT_FROZEN_20261119.md"


def raster_meta(payload):
    from rasterio.io import MemoryFile
    with MemoryFile(payload) as f:
        with f.open() as raster:
            if raster.count!=1 or raster.crs is None or raster.crs.to_epsg()!=4326:
                raise RuntimeError("TERRAIN_RASTER_BAND_OR_CRS_NOT_EPSG4326")
            if raster.width<100 or raster.height<100:
                raise RuntimeError("TERRAIN_RASTER_DIMENSIONS_INVALID")
            return {
                "width":raster.width,"height":raster.height,
                "crs":str(raster.crs),"band_count":raster.count,
                "transform":[float(x) for x in raster.transform][:6],
                "nodata":raster.nodata,
                "dtype":raster.dtypes[0],
                "units":raster.units[0],
                "bounds":[float(x) for x in raster.bounds]
            }


def terrain_source_pin(directory):
    one=directory/"elev_first.zip"
    two=directory/"elev_second.zip"
    h1,b1=climate.checksum_download(ELEV_URL,one,limit=MAX_ELEV_ZIP)
    h2,b2=climate.checksum_download(ELEV_URL,two,limit=MAX_ELEV_ZIP)
    if h1!=h2 or b1!=b2:raise RuntimeError("ELEVATION_ORIGINAL_SOURCE_TWO_GET_SHA_DRIFT")
    with zipfile.ZipFile(one) as z:
        members=[x for x in z.infolist() if x.filename.lower().endswith(".tif") and not x.is_dir()]
        if len(members)!=1 or pathlib.PurePosixPath(members[0].filename).name!=ELEV_MEMBER:
            raise RuntimeError("WORLDCLIM_ELEV_ORIGINAL_MEMBER_UNEXPECTED")
        if members[0].file_size>100_000_000:raise RuntimeError("WORLDCLIM_ELEV_MEMBER_SIZE_STOP")
        body=z.read(members[0])
    return {
        "status":"ELEVATION_TWO_IDENTICAL_ORIGINAL_DOWNLOADS_GEOHEADER_VERIFIED",
        "source_url":ELEV_URL,"download_count":2,
        "source_zip_sha256":h1,"source_zip_size_bytes":b1,
        "source_tiff_sha256":hashlib.sha256(body).hexdigest(),
        "source_member":ELEV_MEMBER,
        "metadata":raster_meta(body),
        "topographic_ruggedness_not_measured":True
    }


def forest_one_tile_probe():
    receipt={
       "status":"FOREST_SOURCE_TILE_NOT_VERIFIED",
       "product":"ESA WorldCover 2021 v200 10m class 10 tree cover",
       "tile_url":FOREST_TILE_URL,
       "tile_id":"N03W075",
       "full_17_country_forest_coverage_verified":False,
       "forest_cell_fraction_estimated":False
    }
    try:
        req=Request(FOREST_TILE_URL,method="HEAD",
                    headers={"User-Agent":"esdm-NeoBat-source-forest-preflight/1"})
        with urlopen(req,timeout=35) as resp:
            receipt["http_head_status"]=resp.status
            receipt["content_length"]=resp.headers.get("Content-Length")
            receipt["etag"]=resp.headers.get("ETag")
        # Range read checks that the public URL exposes original TIFF bytes.
        req=Request(FOREST_TILE_URL,
                    headers={"Range":"bytes=0-16383",
                             "User-Agent":"esdm-NeoBat-source-forest-preflight/1"})
        with urlopen(req,timeout=35) as resp:
            head=resp.read(16384)
            receipt["http_range_status"]=resp.status
            receipt["content_range"]=resp.headers.get("Content-Range")
        if not head.startswith((b"II*\x00",b"MM\x00*",b"II+\x00",b"MM\x00+")):
            raise RuntimeError("ESA_TILE_RANGE_NOT_TIFF")
        if receipt["http_range_status"]!=206:
            raise RuntimeError("ESA_TILE_NO_BYTE_RANGE_SUPPORT")
        receipt["status"]="ONE_ESA_WORLDCOVER_TILE_TIFF_RANGE_ACCESS_VERIFIED"
        # A header/range check still cannot establish remote raster
        # geotransform or forest fraction. Do not invent them.
    except Exception as exc:
        receipt["status"]="FOREST_ONE_TILE_SOURCE_STOP"
        receipt["error_type"]=type(exc).__name__
        receipt["error_code"]=str(exc)[:160]
    return receipt


def execute():
    from rasterio import __version__ as rasterio_version
    result={
        "schema_version":1,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "design":DESIGN,
        "status":"ENVIRONMENT_SOURCE_NOT_VERIFIED",
        "rasterio_version":rasterio_version,
        "GBIF_bat_or_plant_occurrence_rows_opened":0,
        "plant_models_fitted":0,
        "M3_minus_M1_auc":None,
        "M3_minus_N1_auc":None,
        "worldclim_period":"1970-2000",
        "ESA_worldcover_year":2021,
        "GBIF_occurrence_period":"2000-2025",
        "not_annual_contemporaneous_resources":True
    }
    with tempfile.TemporaryDirectory(prefix="neobat-source-abiotic-") as work:
        directory=pathlib.Path(work)
        archive=directory/"original_bio.zip"
        actual,size=climate.checksum_download(climate.SOURCE_URL,archive)
        if actual!=climate.ARCHIVE_SHA256:
            raise RuntimeError("ORIGINAL_WORLDCLIM_BIO_ZIP_SHA_STOP")
        variables=climate.inspect_source(archive)
        if set(variables)!=set(climate.RASTERS):
            raise RuntimeError("WORLDCLIM_CLIMATE_VARIABLES_NOT_COMPLETE")
        result["climate"]={
            "status":"PINNED_BIO1_BIO12_GEOHEADER_VERIFIED",
            "source_url":climate.SOURCE_URL,
            "original_zip_sha256":actual,
            "original_zip_size_bytes":size,
            "variables":variables
        }
        result["terrain"]=terrain_source_pin(directory)
    # Tile check is an independent diagnostic. Failure will NOT
    # mislabel already source-qualified BIO1/BIO12/elevation as failed.
    result["forest_tile_probe"]=forest_one_tile_probe()
    result["status"]="CLIMATE_AND_ELEVATION_SOURCE_GEOHEADERS_VERIFIED_FOREST_PILOT_DIAGNOSTIC"
    return result


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--out",default="docs/replication/neobat/abiotic_terrain_forest_source_preflight.json")
    args=pa.parse_args()
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    try: result=execute()
    except Exception as exc:
        result={"schema_version":1,
                "status":"ABIOTIC_TERRAIN_SOURCE_STOP",
                "error_type":type(exc).__name__,
                "error_code":str(exc)[:200],
                "no_bat_or_plant_responses_opened":True,
                "M3_minus_M1_auc":None}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_ENVIRONMENT_SOURCE",result["status"],flush=True)
    if "forest_tile_probe" in result:
        print("FOREST_ONE_TILE",result["forest_tile_probe"]["status"],flush=True)
    return 0 if result["status"]=="CLIMATE_AND_ELEVATION_SOURCE_GEOHEADERS_VERIFIED_FOREST_PILOT_DIAGNOSTIC" else 3


if __name__=="__main__":
    raise SystemExit(main())
