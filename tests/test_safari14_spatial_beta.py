"""No-response/synthetic correctness checks for Safari14 spatial beta analysis."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

from scripts.safari14_spatial_beta import (
    DISCOVERY,VALIDATION,PROJECTS,EXCLUDED_SER,
    RAREFACTION_CAMERAS,TAXON_MIN_CAMERAS_WITH_RECORD,
    MIN_SEQUENCES_PER_CAMERA,RNG_SEED,RAREFACTION_DRAWS,
    normalize_mammal,project_from_name,load_camera_incidence,
    beta_components,analyze,
)


def test_fixed_parks_taxonomy_and_no_datetime_in_estimator():
    assert len(DISCOVERY)==len(VALIDATION)==7
    assert len(PROJECTS)==14
    assert EXCLUDED_SER not in PROJECTS
    assert project_from_name("SER/S1/C1/image.jpg")=="EXCLUDED_SER"
    assert project_from_name("KAR/S1/C1/image.jpg")=="KAR"
    assert project_from_name("NA/unknown.jpg") is None
    assert normalize_mammal("lionFemale")=="lion"
    assert normalize_mammal("lionCub")=="lion"
    for x in ("human","empty","vehicle","otherBird","cattle","dog"):
        assert normalize_mammal(x) is None
    assert (RAREFACTION_CAMERAS,TAXON_MIN_CAMERAS_WITH_RECORD,
            MIN_SEQUENCES_PER_CAMERA,RNG_SEED,RAREFACTION_DRAWS)==(10,2,30,20261111,500)


def test_baselga_nestedness_turnover_exact_additivity():
    sor,sim,sne=beta_components({"a","b","c"},{"a","b"})
    assert math.isclose(sor,.2)
    assert math.isclose(sim,0)
    assert math.isclose(sne,.2)
    sor,sim,sne=beta_components({"a","b"},{"a","c"})
    assert math.isclose(sor,.5)
    assert math.isclose(sim,.5)
    assert math.isclose(sne,0)
    sor,sim,sne=beta_components({"a"},{"b"})
    assert (sor,sim,sne)==(1,1,0)
    assert beta_components(set(),{"a"}) is None


def test_real_source_parser_accepts_missing_timestamps_and_sequence_dedups():
    categories=[{"id":1,"name":"lionFemale"},{"id":2,"name":"zebra"},
                {"id":3,"name":"empty"},{"id":4,"name":"human"}]
    categories.extend({"id":100+i,"name":f"unrecognized{i}"} for i in range(26))
    images=[]
    annotations=[]
    n=0
    for project in ("APN","SER","MAD"):
        for animal,code in (("lion",1),("zebra",2),("empty",3)):
            for frame in (1,2,3):
                n+=1
                images.append({"id":str(n),"file_name":f"{project}/S1/C1/IMG{n}.JPG",
                               "location":"C1","seq_id":f"{project}-{animal}","frame_num":frame})
                annotations.append({"id":n,"image_id":str(n),"category_id":code,
                                    "count":float("nan")})
    with TemporaryDirectory() as directory:
        source=Path(directory)/"safari.zip"
        with zipfile.ZipFile(source,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("sample.json",json.dumps({
                "categories":categories,"images":images,"annotations":annotations
            }))
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        camera,meta=load_camera_incidence(source,expected_sha256=digest)
    qc=meta["quality"]
    assert qc["total_image_metadata_records"]==27
    assert qc["excluded_E7_Serengeti_images"]==9
    assert qc["nonwild_unknown_or_domestic_annotations"]==6
    assert qc["recognized_wild_mammal_annotation_rows"]==12
    assert qc["valid_14project_distinct_triggered_sequences"]==6
    assert qc["number_of_camera_location_keys"]==2
    assert qc["all_source_cameras_by_project"]["APN"]==1
    assert qc["eligible_cameras_by_project"]["APN"]==0
    assert qc["matched_species_label_count"]==2


def _camera_sets():
    # Same 14 fixed parks, 10 cameras/park; overlapping baseline species
    # plus one park-unique taxon -> pure replacement and no nestedness.
    out=defaultdict(list)
    for project in PROJECTS:
        for camera in range(10):
            out[project].append((f"{project}-cam{camera}",{"zebra",f"unique_{project}"}))
    return out


def test_camera_equalization_and_beta_dominance_on_clean_synthetic_turnover():
    r=analyze(_camera_sets(),rarefactions=25,seed=RNG_SEED)
    assert r["status"]=="S14_OBSERVED_RESERVE_BETA_DIVERSITY_DESCRIPTIVE_RESULT"
    assert len(r["eligible_projects"])==14
    assert r["eligible_discovery_projects"]==7
    assert r["eligible_validation_projects"]==7
    assert len(r["all_91_park_pair_summaries"])==91
    for group,total in (("discovery",21),("validation",21),("cross",49)):
        part=r["beta_summary_by_project_partition"][group]
        assert part["valid_resampling_draws"]==25
        assert part["median_pair_count_per_draw"]==total
        assert part["turnover_dominant_draws"]==25
        assert math.isclose(part["median_pair_sor"],.5)
        assert math.isclose(part["median_pair_sim"],.5)
        assert math.isclose(part["median_pair_sne"],0)
    assert r["predeclared_turnover_dominant_in_both_splits"] is True


def test_nestedness_is_not_mislabeled_turnover():
    cameras=defaultdict(list)
    for project in PROJECTS:
        for i in range(10):
            taxa={"zebra","buffalo"} if project in ("APN","MAD") else {"zebra"}
            cameras[project].append((f"cam{i}",taxa))
    r=analyze(cameras,rarefactions=25,seed=21)
    assert r["predeclared_turnover_dominant_in_both_splits"] is False
    assert r["beta_summary_by_project_partition"]["discovery"]["median_pair_sim"]==0


def test_insufficient_project_support_refused_not_thresh_reduced():
    cameras=_camera_sets()
    for project in (*DISCOVERY[:3],*VALIDATION[:3]):
        cameras[project]=cameras[project][:9]
    r=analyze(cameras,rarefactions=8,seed=42)
    assert r["status"]=="INSUFFICIENT_DISCOVERY_VALIDATION_PARK_SUPPORT"
    assert r["eligible_discovery"]==4
    assert r["eligible_validation"]==4
    assert r["full_91_pair_universe"]==91
