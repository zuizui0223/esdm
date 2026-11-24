"""NeoBat frozen 3-plant Colombia-heldout *plant-only* transfer pilot.

Reads original DOI plant ZIP and original WorldClim climate/elevation sources,
fits fixed logistic plant-vs-other-plant target-group pseudo-background.
Never exports raw coordinates, cell IDs, occurrence rows or model samples.
No bat SDM, M1-M3 comparison or independent validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import pathlib
import tempfile
from collections import defaultdict,Counter
from contextlib import ExitStack
from datetime import datetime,timezone
import zipfile

from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED
from scripts.neobat_spatial_cell_pilot import LATAM
from scripts import neobat_worldclim_source_preflight as wc

ROOT=pathlib.Path("docs/replication")
D=ROOT/"neobat"
HOLDOUT="CO"
SENTINELS=("Cecropia obtusifolia","Ficus insipida","Piper aduncum")
V2_HASH="41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
ELEV_URL="https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_elev.zip"
ELEV_SHA="6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd"
ELEV_MEMBER="wc2.1_10m_elev.tif"
DESIGN=str(ROOT/"NEOBAT_COUNTRY_EXCLUDED_PLANT_SDM_PILOT_FROZEN_20261119.md")


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def verified_v2_names():
    d=read(D/"v2_106plant_reference_input_gate.json")
    names=d["v2_fixed_plant_names"]
    if d["status"]!="SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY" or \
       len(names)!=106 or set(SENTINELS).difference(names):
        raise RuntimeError("FROZEN_V2_PLANT_UNIVERSE_CHANGED")
    digest=hashlib.sha256(("\n".join(names)+"\n").encode("utf-8")).hexdigest()
    if digest!=V2_HASH or digest!=d["v2_fixed_plant_universe_sha256"]:
        raise RuntimeError("FROZEN_106_UNIVERSE_HASH_MISMATCH")
    return names


def country_cell_taxa(plant_cells):
    """Within-memory observed plant taxon set per (source country,25km cell)."""
    observed=defaultdict(lambda:defaultdict(set))
    for (plant,country),mapping in plant_cells.items():
        for cell in mapping:
            observed[country][cell].add(plant)
    return observed


def make_labeled_cells(country_cells,taxon,country,excluded_cells=frozenset()):
    """Require other-taxon source coverage in both + and pseudo-bg groups."""
    output=[]
    for cell,all_taxa in country_cells.get(country,{}).items():
        if cell in excluded_cells:
            continue
        n_other=len(all_taxa)-int(taxon in all_taxa)
        if n_other<=0:
            # Prevent a trivial target-group effort artifact: positive-only
            # cells with no other target-group detections cannot enter.
            continue
        output.append((cell,int(taxon in all_taxa),math.log1p(n_other)))
    return output


def verify_raster_sources(directory):
    from rasterio.io import MemoryFile
    biozip=directory/"bio_original.zip"
    elevzip=directory/"elev_original.zip"
    bio_sha, _=wc.checksum_download(wc.SOURCE_URL,biozip)
    if bio_sha!=wc.ARCHIVE_SHA256:raise RuntimeError("ORIGINAL_WORLDCLIM_BIO_ARCHIVE_SHA_DRIFT")
    _=wc.inspect_source(biozip)
    elev_sha,_=wc.checksum_download(ELEV_URL,elevzip,limit=30_000_000)
    if elev_sha!=ELEV_SHA:raise RuntimeError("ORIGINAL_WORLDCLIM_ELEV_ARCHIVE_SHA_DRIFT")
    members={}
    with zipfile.ZipFile(biozip) as z:
        for key,member in wc.RASTERS.items():
            if z.namelist().count(member)!=1:
                raise RuntimeError("WORLDCLIM_BIO_MEMBER_SCHEMA_STOP")
            members[key]=z.read(member)
    with zipfile.ZipFile(elevzip) as z:
        if z.namelist().count(ELEV_MEMBER)!=1:
            raise RuntimeError("WORLDCLIM_ELEV_MEMBER_SCHEMA_STOP")
        members["ELEV"]=z.read(ELEV_MEMBER)
    return members,{"climate_zip_sha256":bio_sha,"elevation_zip_sha256":elev_sha,
                    "sample_resolution":"WorldClim v2.1 10arcmin",
                    "climate_baseline":"1970-2000","elevation_is_not_ruggedness":True}


def open_source_rasters(stack,members):
    from rasterio.io import MemoryFile
    output={}
    for key,body in members.items():
        mem=stack.enter_context(MemoryFile(body))
        raster=stack.enter_context(mem.open())
        if raster.count!=1 or raster.crs is None or raster.crs.to_epsg()!=4326:
            raise RuntimeError("WORLDCLIM_RASTER_SCHEMA_CRS_STOP_"+key)
        output[key]=raster
    if len(output)!=3:raise RuntimeError("FROZEN_3_ABIOTIC_RASTERS_INCOMPLETE")
    return output


def extract_environment(cell,raster_sources,transformer,cache):
    """Single center pixel per 25km EPSG:6933 cell; no cell identifiers exported."""
    if cell in cache:return cache[cell]
    ix,iy=cell
    lon,lat=transformer.transform((ix+0.5)*25000,(iy+0.5)*25000)
    if not math.isfinite(lon) or not math.isfinite(lat):
        cache[cell]=None;return None
    env=[]
    import numpy as np
    for key in ("BIO1","BIO12","ELEV"):
        ds=raster_sources[key]
        val=next(ds.sample([(lon,lat)],masked=True))[0]
        if np.ma.is_masked(val):
            cache[cell]=None;return None
        number=float(val)
        if not math.isfinite(number) or (ds.nodata is not None and number==ds.nodata):
            cache[cell]=None;return None
        env.append(number)
    cache[cell]=tuple(env)
    return cache[cell]


def dataframe_rows(labeled,rasters,transformer,cache):
    rows=[]
    missing=0
    for cell,label,effort in labeled:
        environmental=extract_environment(cell,rasters,transformer,cache)
        if environmental is None:
            missing+=1
            continue
        rows.append((label,(*environmental,effort)))
    return rows,missing


def train_and_score(train,test):
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler
    Xtrain=np.asarray([x for _,x in train],dtype=float)
    ytrain=np.asarray([int(y) for y,_ in train],dtype=int)
    Xtest=np.asarray([x for _,x in test],dtype=float)
    ytest=np.asarray([int(y) for y,_ in test],dtype=int)
    if Xtrain.shape[1]!=4 or Xtest.shape[1]!=4:
        raise ValueError("CROSSFIT_EXPECTS_THREE_ABIOTIC_ONE_EFFORT_COLUMNS")
    if len(set(ytrain))!=2 or len(set(ytest))!=2:
        raise ValueError("TRAIN_OR_TEST_HAS_SINGLE_CLASS")
    if not np.all(np.isfinite(Xtrain)) or not np.all(np.isfinite(Xtest)):
        raise ValueError("NONFINITE_PREDICTOR")
    scores={}
    for name,selected in (("abiotic_only",(0,1,2)),
                          ("abiotic_plus_other_plant_effort",(0,1,2,3))):
        train_sel=Xtrain[:,selected]
        test_sel=Xtest[:,selected]
        scaler=StandardScaler().fit(train_sel)  # training country cells only
        model=LogisticRegression(
            C=1.0,class_weight="balanced",max_iter=400,
            solver="lbfgs",random_state=20261119)
        model.fit(scaler.transform(train_sel),ytrain)
        value=model.decision_function(scaler.transform(test_sel))
        scores[name]=float(roc_auc_score(ytest,value))
    return scores


def three_sentinels(plant_cells,raster_sources,countries):
    from pyproj import Transformer
    data=country_cell_taxa(plant_cells)
    if HOLDOUT not in data or not data[HOLDOUT]:
        raise RuntimeError("HELDOUT_COUNTRY_NOT_IN_SOURCE")
    # A cell occurring in heldout CO must NEVER be used to train
    # another-country plant predictor even when the coarse 25km cell
    # straddles international boundaries.
    excluded=set(data[HOLDOUT])
    transformer=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    cache={}
    results=[]
    for taxon in SENTINELS:
        train_labeled=[]
        for country in countries:
            if country==HOLDOUT:continue
            train_labeled.extend(make_labeled_cells(
                data,taxon,country,excluded_cells=excluded))
        test_labeled=make_labeled_cells(data,taxon,HOLDOUT)
        train,missingtrain=dataframe_rows(train_labeled,raster_sources,transformer,cache)
        test,missingtest=dataframe_rows(test_labeled,raster_sources,transformer,cache)
        p_train=sum(y for y,_ in train); b_train=len(train)-p_train
        p_test=sum(y for y,_ in test); b_test=len(test)-p_test
        row={
            "plant":taxon,"holdout_country":HOLDOUT,
            "train_positive_recorded_25km_cells":p_train,
            "train_other_plant_target_background_cells":b_train,
            "test_positive_recorded_25km_cells":p_test,
            "test_other_plant_target_background_cells":b_test,
            "train_abiotic_nodata_excluded_cells":missingtrain,
            "test_abiotic_nodata_excluded_cells":missingtest,
            "test_country_source_rows_used_for_any_training":False,
            "training_spatial_cells_overlapping_heldout":0,
            "effort_covariate_from_other_plant_taxa_only":True,
            "heldout_target_background_is_not_true_plant_absence":True,
            "AUC_abiotic_only":None,
            "AUC_abiotic_plus_otherplant_effort":None
        }
        if min(p_train,b_train)<20 or min(p_test,b_test)<5:
            row["status"]="PILOT_COUNTRY_FOLD_QUANTITY_STOP"
        else:
            auc=train_and_score(train,test)
            row["AUC_abiotic_only"]=auc["abiotic_only"]
            row["AUC_abiotic_plus_otherplant_effort"]=auc["abiotic_plus_other_plant_effort"]
            row["status"]="EXPLORATORY_PLANT_COUNTRY_CROSSFIT_AUC"
        results.append(row)
    return results


def execute():
    _=verified_v2_names()
    roster=read(D/"NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json")
    original=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")
    country_universe=original["GBIF_29_country_universe"]
    if len(country_universe)!=29 or HOLDOUT not in country_universe or \
       len(roster["strict_84_candidate_folds"])!=84:
        raise RuntimeError("FROZEN_COUNTRY_OR_BAT_ROSTER_CHANGED")
    src=verified_source(read(D/"gbif_download_submission.json"),
                        read(D/"gbif_download_doi_poll.json"))
    header=read(D/"gbif_archive_header_preflight.json")
    source_qc=read(D/"gbif_full_source_qc.json")
    names=name_map(read(D/"gbif_search_preflight.json"),
                   read(D/"plant_search_preflight.json"))
    with tempfile.TemporaryDirectory(prefix="neobat-crossfit-plant-source-") as temp:
        directory=pathlib.Path(temp)
        plant_path=directory/"plant_original.zip"
        if src["plant"]["doi"]!=EXPECTED["plant"]["doi"] or \
           src["plant"]["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
            raise RuntimeError("PLANT_DOI_OR_SOURCE_COUNT_CHANGED")
        receipt=safe_archive(src["plant"]["url"],plant_path)
        if receipt["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           receipt["sha256"]!=header["files"]["plant"]["sha256"]:
            raise RuntimeError("PLANT_ORIGINAL_ZIP_SHA_CHANGED")
        cells=strict_cell_records(plant_path,group="plant",
            source=header["files"]["plant"],
            accepted=names["plant"],expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,source_qc)
        members,metadata=verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=open_source_rasters(stack,members)
            fitted=three_sentinels(cells,rasters,country_universe)
    return {
      "schema_version":1,
      "status":"EXPLORATORY_COUNTRY_EXCLUDED_3PLANT_PILOT_COMPLETE",
      "created_utc":datetime.now(timezone.utc).isoformat(),
      "frozen_design":DESIGN,
      "source_plant_DOI":EXPECTED["plant"]["doi"],
      "source_plant_original_zip_sha256":receipt["sha256"],
      "raster_source":metadata,
      "frozen_v2_106_plant_universe_sha256":V2_HASH,
      "heldout_country":HOLDOUT,
      "frozen_sentinel_species":list(SENTINELS),
      "sentinels_evaluated":sum(x["status"]=="EXPLORATORY_PLANT_COUNTRY_CROSSFIT_AUC" for x in fitted),
      "sentinels_quantity_stopped":sum(x["status"]=="PILOT_COUNTRY_FOLD_QUANTITY_STOP" for x in fitted),
      "all_frozen_sentinels_preserved":True,
      "is_not_106_plant_full_17country_crossfit":True,
      "plant_target_group_background_is_not_true_absence":True,
      "independent_unopened_validation":False,
      "no_raw_plant_rows_or_cells_or_raster_pixels_persisted":True,
      "no_bat_GBIF_response_opened":True,
      "M3_minus_M1_bat_auc":None,
      "M3_minus_N1_bat_auc":None,
      "plants":fitted
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="build/neobat/plant_colombia_crossfit_pilot.json")
    args=parser.parse_args();out=pathlib.Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=execute()
    except Exception as exc:
        result={"schema_version":1,
                "status":"PLANT_COUNTRY_CROSSFIT_PILOT_SOURCE_OR_MODEL_STOP",
                "error_type":type(exc).__name__,
                "error_code":str(exc)[:230],
                "no_bat_model_tested":True,"M3_minus_M1_bat_auc":None}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_PLANT_CROSSFIT_PILOT",result["status"],flush=True)
    if "plants" in result:
        for p in result["plants"]:
            print("PLANT_PILOT",p["plant"],p["status"],
                  "n_train_pos",p["train_positive_recorded_25km_cells"],
                  "n_test_pos",p["test_positive_recorded_25km_cells"],
                  "AUC_bio",p["AUC_abiotic_only"],flush=True)
    return 0 if result["status"]=="EXPLORATORY_COUNTRY_EXCLUDED_3PLANT_PILOT_COMPLETE" else 3


if __name__=="__main__":
    raise SystemExit(main())
