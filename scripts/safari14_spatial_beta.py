#!/usr/bin/env python3
"""Safari14 binary camera mammal beta diversity: turnover vs nestedness.

Independent spatial endpoint frozen 2026-11-11 after a separate diel source
schema STOP. The LILA 2024 metadata lacks timestamps but has site/sequence/
species labels. Excludes SER (E7 source), images, unverified cameras and all
individual camera/sequence IDs from exported results. Does not estimate true
occupancy, operational exposure, climate effects or E5 detector calibration.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
import re
from statistics import median
import sys
import tempfile
import zipfile

import ijson

SOURCE_URL = ("https://storage.googleapis.com/public-datasets-lila/"
              "snapshot-safari-2024-expansion/snapshot_safari_2024_metadata.zip")
PINNED_ZIP_SHA256 = "2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1"
DISCOVERY = ("APN","CDB","ENO","KAR","KGA","KRU","LEC")
VALIDATION = ("MAD","MLP","MTZ","NIA","PLN","RUA","TSW")
PROJECTS = DISCOVERY + VALIDATION
EXCLUDED_SER = "SER"
MIN_SEQUENCES_PER_CAMERA = 30
RAREFACTION_CAMERAS = 10
TAXON_MIN_CAMERAS_WITH_RECORD = 2
RAREFACTION_DRAWS = 500
RNG_SEED = 20261111
MIN_PARKS_PER_SPLIT = 5
SUCCESS_DRAW_FRACTION = 0.95

# Fixed recognized wild African mammal labels, without changing taxa based on
# observed occurrence/turnover patterns in the open file.
NAME_UNIVERSE = (
    "aardvark aardwolf baboon batEaredFox buffalo bushbuck caracal cheetah "
    "civet dikDik duiker eland elephant gazelleGrants gazelleThomsons genet "
    "giraffe hare hartebeest hippopotamus honeyBadger hyenaSpotted "
    "hyenaStriped impala jackal klipspringer kudu leopard lion lionFemale "
    "lionMale lionCub mongoose nyala oryx pangolin porcupine reedbuck "
    "rhinoceros rodents sable serval springbok steenbok topi vervetMonkey "
    "warthog waterbuck wildcat wildebeest zebra zorilla"
)
MAMMAL_LABELS = {re.sub(r"[^a-z]","",x.lower()):x for x in NAME_UNIVERSE.split()}
for synonym in ("lionmale","lionfemale","lioncub"):
    MAMMAL_LABELS[synonym]="lion"

NONFINITE = re.compile(rb"(:[ \t\r\n]*)(?:NaN|-?Infinity)([ \t\r\n]*[,}\]])")


def normalize_mammal(name: str) -> str | None:
    return MAMMAL_LABELS.get(re.sub(r"[^a-z]","",str(name).lower()))


def project_from_name(path: str) -> str | None:
    prefix=str(path).split("/",1)[0].strip().upper()
    if prefix==EXCLUDED_SER:
        return "EXCLUDED_SER"
    return prefix if prefix in PROJECTS else None


def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_json(stream, writer, chunksize=4*1024*1024) -> int:
    """Deterministic numeric-NaN repair before ijson, never alters archive."""
    pending=b""
    count=0
    while True:
        chunk=stream.read(chunksize)
        if not chunk:
            break
        b=pending+chunk
        if len(b)<=256:
            pending=b
            continue
        cut=len(b)-256
        for found in NONFINITE.finditer(b):
            if found.start()<cut<found.end():
                cut=found.start()
                break
        a,pending=b[:cut],b[cut:]
        a,n=NONFINITE.subn(lambda m:m.group(1)+b"null"+m.group(2),a)
        writer.write(a)
        count+=n
    end,n=NONFINITE.subn(lambda m:m.group(1)+b"null"+m.group(2),pending)
    writer.write(end)
    return count+n


def prepare_source(archive_path: Path, normalized_path: Path,
                   *, expected_sha256: str = PINNED_ZIP_SHA256) -> dict:
    digest=sha256(archive_path)
    if digest != expected_sha256:
        raise ValueError("official Safari 2024 ZIP digest differs from pinned source")
    with zipfile.ZipFile(archive_path) as z:
        members=[n for n in z.namelist() if n.endswith(".json") and not n.endswith("/")]
        if len(members)!=1:
            raise ValueError("expected exactly one COCO metadata JSON file")
        with z.open(members[0]) as source, normalized_path.open("wb") as target:
            nonfinite=normalized_json(source,target)
    return {"zip_sha256":digest,"nonfinite_numeric_tokens_normalized":nonfinite,
            "normalized_json_bytes":normalized_path.stat().st_size}


def load_camera_incidence(archive_path: Path, *,
                          expected_sha256: str = PINNED_ZIP_SHA256):
    qc=Counter()
    with tempfile.TemporaryDirectory() as directory:
        normalized=Path(directory)/"safari14_normalized.json"
        pinned=prepare_source(archive_path,normalized,expected_sha256=expected_sha256)
        category_map={}
        with normalized.open("rb") as inp:
            for c in ijson.items(inp,"categories.item"):
                category_map[str(c["id"])]=normalize_mammal(c.get("name",""))
        if len(category_map)<30:
            raise ValueError("source categories implausibly sparse")
        qc["all_published_taxon_categories"]=len(category_map)
        image_camera={}
        seen_seq=set()
        camera_seq_count=Counter()
        seen_project_images=Counter()
        with normalized.open("rb") as inp:
            for image in ijson.items(inp,"images.item"):
                qc["total_image_metadata_records"]+=1
                project=project_from_name(image.get("file_name",""))
                if project=="EXCLUDED_SER":
                    qc["excluded_E7_Serengeti_images"]+=1
                    continue
                if project is None:
                    qc["unknown_project_prefix_images"]+=1
                    continue
                camera=str(image.get("location","")).strip()
                sequence=str(image.get("seq_id","")).strip()
                imageid=str(image.get("id","")).strip()
                if not camera or not sequence or not imageid:
                    qc["missing_camera_sequence_or_image_id"]+=1
                    continue
                project=sys.intern(project)
                camera=sys.intern(camera)
                sequence=sys.intern(sequence)
                point=(project,camera)
                if imageid in image_camera and image_camera[imageid]!=point:
                    raise ValueError("same image ID assigned inconsistent cameras")
                image_camera[imageid]=point
                key=(project,camera,sequence)
                if key not in seen_seq:
                    seen_seq.add(key)
                    camera_seq_count[point]+=1
                seen_project_images[project]+=1
        if not seen_seq:
            raise ValueError("no source sequence/camera identifiers")
        qc["valid_14project_image_rows"]=sum(seen_project_images.values())
        qc["valid_14project_distinct_triggered_sequences"]=len(seen_seq)
        qc["number_of_camera_location_keys"]=len(camera_seq_count)
        qc["image_records_by_project"]=dict(sorted(seen_project_images.items()))
        del seen_seq

        observed=defaultdict(set)
        matched_mammal_annotations=Counter()
        with normalized.open("rb") as inp:
            for item in ijson.items(inp,"annotations.item"):
                qc["all_annotations"]+=1
                taxon=category_map.get(str(item.get("category_id","")))
                if taxon is None:
                    qc["nonwild_unknown_or_domestic_annotations"]+=1
                    continue
                site=image_camera.get(str(item.get("image_id","")).strip())
                if site is None:
                    qc["whitelisted_annotation_without_eligible_camera"]+=1
                    continue
                observed[site].add(taxon)
                matched_mammal_annotations[taxon]+=1
                qc["recognized_wild_mammal_annotation_rows"]+=1
        qc["matched_species_label_count"]=len(matched_mammal_annotations)
        qc["matched_wild_mammal_annotation_rows_by_label"]=dict(sorted(matched_mammal_annotations.items()))
        if len(observed)==0:
            raise ValueError("no matched wild mammal labels in predeclared projects")

    camera_by_project=defaultdict(list)
    for (project,camera),opportunities in camera_seq_count.items():
        if opportunities>=MIN_SEQUENCES_PER_CAMERA:
            camera_by_project[project].append((camera,observed.get((project,camera),set())))
    for project in PROJECTS:
        camera_by_project[project].sort(key=lambda x:x[0])
    qc["eligible_cameras_by_project"]={
        p:len(camera_by_project[p]) for p in PROJECTS
    }
    qc["all_source_cameras_by_project"]={
        p:sum(project==p for project,camera in camera_seq_count)
        for p in PROJECTS
    }
    return camera_by_project, {"source":pinned,"quality":dict(qc)}


def beta_components(a: set[str], b: set[str]) -> tuple[float,float,float] | None:
    """Baselga 2010 pairwise Sørensen = turnover + nestedness."""
    if not a or not b:
        return None
    shared=len(a & b)
    unique_a=len(a-b)
    unique_b=len(b-a)
    total=2*shared+unique_a+unique_b
    denom=shared+min(unique_a,unique_b)
    if total==0 or denom==0:
        return None
    sor=(unique_a+unique_b)/total
    sim=min(unique_a,unique_b)/denom
    sne=sor-sim
    if min(sor,sim,sne)<-1e-12 or not math.isclose(sor,sim+sne,abs_tol=1e-12):
        raise ValueError("beta diversity decomposition not additive")
    return sor,sim,max(0.0,sne)


def _labels_at_sample(sample) -> set[str]:
    positives=Counter()
    for camera,labels in sample:
        for taxon in labels:
            positives[taxon]+=1
    return {taxon for taxon,n in positives.items() if n>=TAXON_MIN_CAMERAS_WITH_RECORD}


def _group_summary(vals) -> dict:
    if not vals:
        return {"median_sor":None,"median_sim":None,"median_sne":None,
                "turnover_dominates":None,"pairs_estimable":0}
    return {
        "median_sor":median(x[0] for x in vals),
        "median_sim":median(x[1] for x in vals),
        "median_sne":median(x[2] for x in vals),
        "turnover_dominates":median(x[1] for x in vals)>median(x[2] for x in vals),
        "pairs_estimable":len(vals),
    }


def analyze(camera_by_project: dict, *, rarefactions=RAREFACTION_DRAWS,
            seed=RNG_SEED) -> dict:
    eligible=tuple(p for p in PROJECTS if len(camera_by_project[p])>=RAREFACTION_CAMERAS)
    discovery_eligible=sum(p in eligible for p in DISCOVERY)
    validation_eligible=sum(p in eligible for p in VALIDATION)
    if discovery_eligible<MIN_PARKS_PER_SPLIT or validation_eligible<MIN_PARKS_PER_SPLIT:
        return {
            "status":"INSUFFICIENT_DISCOVERY_VALIDATION_PARK_SUPPORT",
            "eligible_parks":list(eligible),
            "eligible_discovery":discovery_eligible,
            "eligible_validation":validation_eligible,
            "full_91_pair_universe":len(PROJECTS)*(len(PROJECTS)-1)//2,
            "all_park_camera_counts":{p:len(camera_by_project[p]) for p in PROJECTS}
        }
    randomizer=random.Random(seed)
    park_summarized={p:{"observed_species_full_eligible_camera_pool":len(
        {name for _,labels in camera_by_project[p] for name in labels}),
        "eligible_camera_count":len(camera_by_project[p]),
        "rarefied_detected_species_counts":[]} for p in PROJECTS}
    pair_summarized={
        (a,b):{"sor":[],"sim":[],"sne":[],"nonempty_draws":0,"turnover_dominated_draws":0}
        for a,b in combinations(PROJECTS,2)
    }
    by_group={group:{"sor":[],"sim":[],"sne":[],"dominated":0,"valid_draws":0,"pair_numbers":[]}
        for group in ("discovery","validation","cross")}
    for _ in range(rarefactions):
        sets={}
        for p in eligible:
            sample=randomizer.sample(camera_by_project[p],RAREFACTION_CAMERAS)
            sets[p]=_labels_at_sample(sample)
            park_summarized[p]["rarefied_detected_species_counts"].append(len(sets[p]))
        groups={"discovery":[],"validation":[],"cross":[]}
        for a,b in combinations(PROJECTS,2):
            if a not in sets or b not in sets:
                continue
            value=beta_components(sets[a],sets[b])
            if value is None:
                continue
            item=pair_summarized[a,b]
            for n,z in zip(("sor","sim","sne"),value):
                item[n].append(z)
            item["nonempty_draws"]+=1
            item["turnover_dominated_draws"]+=int(value[1]>value[2])
            group=("discovery" if a in DISCOVERY and b in DISCOVERY else
                   "validation" if a in VALIDATION and b in VALIDATION else "cross")
            groups[group].append(value)
        for group,vals in groups.items():
            if not vals:
                continue
            s=_group_summary(vals)
            item=by_group[group]
            for n in ("sor","sim","sne"):
                item[n].append(s["median_"+n])
            item["valid_draws"]+=1
            item["dominated"]+=int(s["turnover_dominates"])
            item["pair_numbers"].append(s["pairs_estimable"])
    def overall_report(x):
        return {
            "valid_resampling_draws":x["valid_draws"],
            "turnover_dominant_draws":x["dominated"],
            "turnover_dominant_fraction":x["dominated"]/x["valid_draws"] if x["valid_draws"] else None,
            "median_pair_count_per_draw":median(x["pair_numbers"]) if x["pair_numbers"] else None,
            **{"median_pair_"+n:median(x[n]) if x[n] else None
               for n in ("sor","sim","sne")},
        }
    pairs=[]
    for a,b in combinations(PROJECTS,2):
        item=pair_summarized[a,b]
        pairs.append({
            "project_1":a,"project_2":b,
            "group":("discovery" if a in DISCOVERY and b in DISCOVERY else
                     "validation" if a in VALIDATION and b in VALIDATION else "cross"),
            "eligible_both":a in eligible and b in eligible,
            "valid_resampling_draws":item["nonempty_draws"],
            "median_sor":median(item["sor"]) if item["sor"] else None,
            "median_sim":median(item["sim"]) if item["sim"] else None,
            "median_sne":median(item["sne"]) if item["sne"] else None,
            "fraction_draws_turnover_gt_nestedness":(
                item["turnover_dominated_draws"]/item["nonempty_draws"]
                if item["nonempty_draws"] else None),
        })
    park_summary={}
    for p in PROJECTS:
        data=park_summarized[p]
        rare=data["rarefied_detected_species_counts"]
        park_summary[p]={
            "eligible_cameras":data["eligible_camera_count"],
            "observed_species_full_eligible_camera_pool":data["observed_species_full_eligible_camera_pool"],
            "median_10_camera_detected_species":median(rare) if rare else None,
            "min_10_camera_detected_species":min(rare) if rare else None,
            "max_10_camera_detected_species":max(rare) if rare else None,
        }
    result={
        "status":"S14_OBSERVED_RESERVE_BETA_DIVERSITY_DESCRIPTIVE_RESULT",
        "eligible_projects":list(eligible),
        "eligible_discovery_projects":discovery_eligible,
        "eligible_validation_projects":validation_eligible,
        "project_summary":park_summary,
        "beta_summary_by_project_partition":{
            group:overall_report(item) for group,item in by_group.items()},
        "all_91_park_pair_summaries":pairs,
    }
    a=result["beta_summary_by_project_partition"]
    result["predeclared_turnover_dominant_in_both_splits"] = bool(
        all(a[g]["valid_resampling_draws"]==rarefactions and
            a[g]["turnover_dominant_draws"]>=math.ceil(SUCCESS_DRAW_FRACTION*rarefactions)
            for g in ("discovery","validation"))
    )
    return result


def run(source_zip: Path, *, expected_sha256=PINNED_ZIP_SHA256):
    cameras,provenance=load_camera_incidence(source_zip,expected_sha256=expected_sha256)
    result=analyze(cameras)
    return {
        "schema_version":1,
        "programme_id":"S14_SPATIAL_BETA_MAMMAL_ASSEMBLAGES",
        "source":{"public_metadata_url":SOURCE_URL,
                  "original_zip_sha256":provenance["source"]["zip_sha256"],
                  "nonfinite_numeric_tokens_normalized":provenance["source"]["nonfinite_numeric_tokens_normalized"],
                  "no_image_files_downloaded":True},
        "design":{
            "excluded_E7_Serengeti_project":"SER",
            "discovery_projects":list(DISCOVERY),
            "validation_projects":list(VALIDATION),
            "min_sequences_per_camera":MIN_SEQUENCES_PER_CAMERA,
            "equal_camera_draw_size":RAREFACTION_CAMERAS,
            "taxon_required_observed_in_sampled_cameras":TAXON_MIN_CAMERAS_WITH_RECORD,
            "resampling_draws":RAREFACTION_DRAWS,
            "pseudorandom_seed":RNG_SEED,
            "min_eligible_reserves_per_split":MIN_PARKS_PER_SPLIT,
            "fixed_turnover_dominant_draw_fraction":SUCCESS_DRAW_FRACTION,
            "beta_component_formula":"Baselga 2010 pairwise sor=sim+sne",
            "no_timestamp_or_diel_claim":True,
        },
        "quality":provenance["quality"],
        "results":result,
        "claim_boundary":{
            "conditional_on_observed_camera_wild_mammal_labels":True,
            "sequence_count_proxy_not_actual_operating_effort":True,
            "same_source_project_dependent_camera_sampling":True,
            "no_species_specific_detection_calibrated":True,
            "no_causal_climate_habitat_or_species_interaction_effect":True,
            "random_camera_draws_not_independent_ecological_replicates":True,
            "none_of_E4_E5_E7_E7C_modified":True,
            "E5_G4_passed":False,"E5_original_qualified_candidates":0,
        },
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=run(args.zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    b=result["results"]
    print(json.dumps({
        "status":b["status"],
        "original_zip_sha256":result["source"]["original_zip_sha256"],
        "all_image_rows":result["quality"]["total_image_metadata_records"],
        "all_recognized_annotation_rows":result["quality"]["recognized_wild_mammal_annotation_rows"],
        "eligible_projects":b.get("eligible_projects"),
        "eligible_discovery":b.get("eligible_discovery_projects"),
        "eligible_validation":b.get("eligible_validation_projects"),
        "beta_partition":b.get("beta_summary_by_project_partition"),
        "turnover_dominates_both":b.get("predeclared_turnover_dominant_in_both_splits"),
    },sort_keys=True))


if __name__=="__main__":
    main()
