"""Source-only WorldClim BIO1/BIO12 preflight for NeoBat model predictor pipeline."""
from __future__ import annotations
import argparse, hashlib, io, json, pathlib, tempfile, zipfile
from datetime import datetime,timezone
from urllib.request import Request, urlopen

SOURCE_URL="https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip"
ARCHIVE_SHA256="00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf"
BIO12_SHA256="1e823e951ace0186c6eadd7368b4d0385f8c51cc952282c0f2d640bf7790fea5"
RASTERS={"BIO1":"wc2.1_10m_bio_1.tif","BIO12":"wc2.1_10m_bio_12.tif"}
MAX_SOURCE_BYTES=250_000_000

def checksum_download(url,target,limit=MAX_SOURCE_BYTES):
    h=hashlib.sha256();total=0
    req=Request(url,headers={"User-Agent":"esdm-NeoBat-WorldClim-source-only/1.0"})
    with urlopen(req,timeout=170) as r,target.open("xb") as out:
        while True:
            part=r.read(1<<20)
            if not part:break
            total+=len(part)
            if total>limit:raise RuntimeError("CLIMATE_ARCHIVE_SIZE_STOP")
            h.update(part);out.write(part)
    return h.hexdigest(),total

def inspect_source(path):
    raw=path.read_bytes()
    archive_hash=hashlib.sha256(raw).hexdigest()
    if archive_hash!=ARCHIVE_SHA256:raise RuntimeError("WORLDCLIM_ARCHIVE_SHA_MISMATCH")
    from rasterio.io import MemoryFile  # rasterio required only after original hash qualifies
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        out={}
        for var,member in RASTERS.items():
            if z.namelist().count(member)!=1:raise RuntimeError("WORLDCLIM_MEMBER_NOT_UNIQUE:"+member)
            payload=z.read(member)
            sha=hashlib.sha256(payload).hexdigest()
            if var=="BIO12" and sha!=BIO12_SHA256:
                raise RuntimeError("WORLDCLIM_FROZEN_BIO12_MISMATCH")
            with MemoryFile(payload) as ds:
                with ds.open() as source:
                    if source.count!=1 or source.width<=0 or source.height<=0:
                        raise RuntimeError("WORLDCLIM_RASTER_SCHEMA_STOP")
                    if not source.crs or source.crs.to_epsg()!=4326:
                        raise RuntimeError("WORLDCLIM_RASTER_CRS_STOP")
                    out[var]={
                        "member":member,"sha256":sha,
                        "width":source.width,"height":source.height,
                        "band_count":source.count,
                        "crs":str(source.crs),
                        "transform":[float(x) for x in source.transform][:6],
                        "nodata":source.nodata,
                        "data_type":source.dtypes[0],
                        "band_scale":source.scales[0],
                        "band_offset":source.offsets[0],
                        "units":source.units[0],
                        "bounds":[float(v) for v in source.bounds],
                        "band_tags":source.tags(1)
                    }
        return out

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--out",default="docs/replication/neobat/worldclim_bio1_bio12_source_preflight.json")
    args=pa.parse_args()
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    receipt={"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),
             "status":"SOURCE_NOT_VERIFIED",
             "url":SOURCE_URL,"expected_archive_sha256":ARCHIVE_SHA256,
             "worldclim_reference_period":"1970-2000",
             "GBIF_bat_or_plant_rows_opened":0,"SDM_fits":0}
    try:
        with tempfile.TemporaryDirectory() as t:
            path=pathlib.Path(t)/"source.zip"
            sha,size=checksum_download(SOURCE_URL,path)
            receipt["actual_source_sha256"]=sha
            receipt["archive_size_bytes"]=size
            receipt["variables"]=inspect_source(path)
        receipt["status"]="SOURCE_GEOHEADER_QUALIFIED"
    except Exception as exc:
        receipt["status"]="WORLDCLIM_SOURCE_STOP"
        receipt["error_type"]=type(exc).__name__
        receipt["error_code"]=str(exc)[:200]
    out.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("WORLDCLIM_SOURCE_PREFLIGHT",receipt["status"],flush=True)
    return 0 if receipt["status"]=="SOURCE_GEOHEADER_QUALIFIED" else 3

if __name__=="__main__":raise SystemExit(main())
