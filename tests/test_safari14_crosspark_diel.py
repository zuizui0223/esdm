"""Synthetic, response-free checks for cross-reserve Safari diel comparison."""
from __future__ import annotations

from collections import Counter
import io
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

from scripts.safari14_crosspark_diel import (
    DISCOVERY, VALIDATION, EXCLUDED_OVERLAP_PROJECT, MAMMAL_LABELS,
    MIN_CAMERA_EVENTS, MIN_CAMERAS_PER_PROJECT_PAIR,
    MIN_PARKS_PER_PARTITION, TOP_TAXA,
    clock_bin, normalize_name, normalise_json_stream, project_from_filename,
    select_panel, _project_effect, _partition, pair_results, collect_metadata,
    source_sha256,
)


def test_exact_14_project_source_and_overlap_exclusion():
    assert len(DISCOVERY)==len(VALIDATION)==7
    assert len(set(DISCOVERY+VALIDATION))==14
    assert EXCLUDED_OVERLAP_PROJECT not in DISCOVERY+VALIDATION
    assert project_from_filename("KAR/KAR_S2/C01/photo.jpg")=="KAR"
    assert project_from_filename("SER/SER_S1/C01/photo.jpg")=="EXCLUDED_SER"
    assert project_from_filename("MISSING/image.jpg") is None
    assert (MIN_CAMERA_EVENTS, MIN_CAMERAS_PER_PROJECT_PAIR,MIN_PARKS_PER_PARTITION,TOP_TAXA)==(8,5,3,12)


def test_prespecified_clock_and_mammals_remove_humans_empties():
    assert all(clock_bin(h)=="night" for h in (0,1,2,3,21,22,23))
    assert all(clock_bin(h)=="midday" for h in (10,11,12,13,14,15))
    assert all(clock_bin(h) is None for h in (4,5,6,7,8,9,16,17,18,19,20))
    assert normalize_name("lionFemale") == "lion"
    assert normalize_name("LION MALE") == "lion"
    assert normalize_name("wildebeest") == "wildebeest"
    for category in ("empty","human","vehicle","otherBird","cattle","dog","unidentified"):
        assert normalize_name(category) is None


def test_streaming_source_nonfinite_numeric_normalizer():
    source=io.BytesIO(b'{"images":[{"id":"x","count": NaN,"other": Infinity, "value": -Infinity, "name":"zebra"}]}')
    result=io.BytesIO()
    n=normalise_json_stream(source,result,chunksize=53)
    decoded=json.loads(result.getvalue())
    assert n==3
    assert decoded["images"][0]["count"] is None
    assert decoded["images"][0]["other"] is None
    assert decoded["images"][0]["value"] is None
    assert decoded["images"][0]["name"]=="zebra"


def test_source_sequence_dedup_and_SER_exclusion():
    cats=[{"id":1,"name":"lionFemale"},{"id":2,"name":"zebra"},
          {"id":3,"name":"human"},{"id":4,"name":"empty"}]
    cats.extend({"id":100+i,"name":f"nonmammal{i}"} for i in range(26))
    images=[]
    annotations=[]
    index=0
    for project in ("KAR","SER","MAD"):
        for species,kind in ((1,"lion"),(2,"zebra"),(3,"human"),(4,"empty")):
            for frame in (1,2,3):
                index+=1
                images.append({
                    "id":str(index),"file_name":f"{project}/P1/C01/IMG{index}.jpg",
                    "location":"C01","seq_id":f"{project}-{kind}",
                    "datetime":"2024-07-15 22:00:00" if frame==1 else "2024-07-15 22:01:00"
                })
                annotations.append({"id":index,"image_id":str(index),
                                    "category_id":species,"count":float("nan")})
    with TemporaryDirectory() as tmp:
        archive=Path(tmp)/"source.zip"
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("data.json",json.dumps({
                "categories":cats,"images":images,"annotations":annotations
            }))
        full,clock,info=collect_metadata(archive, expected_source_sha256=source_sha256(archive))
    assert info["quality"]["images_seen"]==36
    assert info["quality"]["excluded_SER_images"]==12
    assert info["quality"]["nonfinite_json_tokens_normalized"]==36
    assert info["quality"]["unique_wildlife_sequence_species_all_hours"]==4
    assert len(full)==4
    assert full[("KAR","C01","lion")]==1
    assert full[("KAR","C01","zebra")]==1
    assert full[("MAD","C01","lion")]==1
    assert all(p!="SER" for p,loc,species in full)
    assert clock[("KAR","C01","lion","night")]==1


def test_discovery_panel_never_uses_heldout_counts_or_diel_direction():
    full=Counter()
    for project in DISCOVERY:
        for i in range(6):
            for mammal in ("zebra","buffalo"):
                full[(project,f"site{i}",mammal)]=8
    for project in VALIDATION:
        for i in range(100):
            full[(project,f"site{i}","elephant")]=200
    assert select_panel(full)==["buffalo","zebra"]
    assert "elephant" not in select_panel(full)


def _simulated_camera_night_records():
    clock=Counter()
    for project in DISCOVERY+VALIDATION:
        for camera in range(6):
            site=f"site{camera}"
            if project in DISCOVERY:
                values={"zebra":(9,1), "lion":(1,9)}
            else:
                values={"zebra":(1,9), "lion":(9,1)}
            for animal,(night,mid) in values.items():
                clock[(project,site,animal,"night")]=night
                clock[(project,site,animal,"midday")]=mid
    return clock


def test_full_park_heldout_contrast_and_66_pair_refusals():
    clock=_simulated_camera_night_records()
    p=_project_effect(clock,"lion","zebra","APN")
    q=_project_effect(clock,"lion","zebra","TSW")
    assert p["status"]=="DESCRIPTIVE_CAMERA_COMPARABLE"
    assert q["status"]=="DESCRIPTIVE_CAMERA_COMPARABLE"
    assert p["informative_camera_count"]==q["informative_camera_count"]==6
    assert p["median_camera_relative_log_nocturnality"]<0
    assert q["median_camera_relative_log_nocturnality"]>0
    allresults=pair_results(clock,["lion","zebra"])
    assert allresults["all_unordered_pairs"]==1
    assert allresults["discovery_estimable_pairs"]==1
    assert allresults["validation_estimable_pairs"]==1
    assert allresults["both_estimable_pairs"]==1
    assert allresults["pair_direction_concordant"]==0
    row=allresults["full_66_pair_matrix"][0]
    assert row["discovery"]["leave_one_project_out"]["all_computable"]
    assert row["validation"]["leave_one_project_out"]["all_computable"]
    assert row["discovery_validation_same_direction"] is False
    assert allresults["discovery_effect_on_validation_relative_skill_vs_zero"]<0


def test_missing_cameras_and_unobserved_biological_taxa_stay_missing():
    counts=Counter()
    for camera in range(4):
        counts[("KRU",f"site{camera}","zebra","night")]=20
        counts[("KRU",f"site{camera}","lion","midday")]=20
    estimate=_project_effect(counts,"lion","zebra","KRU")
    assert estimate["status"]=="NOT_ESTIMABLE"
    assert estimate["median_camera_relative_log_nocturnality"] is None
    par=_partition({"APN":estimate,"CDB":estimate,"ENO":estimate},("APN","CDB","ENO"))
    assert par["status"]=="INSUFFICIENT_CROSSPARK_SUPPORT"
