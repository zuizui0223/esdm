#!/usr/bin/env python3
"""S14 independently held-out 14-reserve African mammal recorded-diel comparison.

The 2024 LILA Safari release is distinct from E7's Serengeti source, which is
explicitly excluded (project SER). Projects/clock bins/species eligibility and
park support were frozen in SAFARI14_CROSSPARK_DIEL_FROZEN_DESIGN.md before
the first S14 animal response. No wildlife images or raw camera IDs exported.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import re
import sys
import tempfile
import zipfile

import ijson

DISCOVERY = ("APN", "CDB", "ENO", "KAR", "KGA", "KRU", "LEC")
VALIDATION = ("MAD", "MLP", "MTZ", "NIA", "PLN", "RUA", "TSW")
EXCLUDED_OVERLAP_PROJECT = "SER"
SOURCE_URL = ("https://storage.googleapis.com/public-datasets-lila/"
              "snapshot-safari-2024-expansion/snapshot_safari_2024_metadata.zip")
MIN_CAMERA_EVENTS = 8
MIN_CAMERAS_PER_PROJECT_PAIR = 5
MIN_PARKS_PER_PARTITION = 3
TOP_TAXA = 12
PINNED_SOURCE_SHA256 = "2327ffec714f6460eff7307efc32c32c61c6805dbcab8334d4d6485eeb079ac1"

# Prespecified recognizable wild African mammal labels; all others are
# excluded, not manually reclassified after seeing diel results.
NAMES = (
    "aardvark aardwolf baboon batEaredFox buffalo bushbuck caracal cheetah "
    "civet dikDik duiker eland elephant gazelleGrants gazelleThomsons genet "
    "giraffe hare hartebeest hippopotamus honeyBadger hyenaSpotted "
    "hyenaStriped impala jackal klipspringer kudu leopard lion lionFemale "
    "lionMale lionCub mongoose nyala oryx pangolin porcupine reedbuck "
    "rhinoceros rodents sable serval springbok steenbok topi vervetMonkey "
    "warthog waterbuck wildcat wildebeest zebra zorilla"
)
MAMMAL_LABELS = {re.sub(r"[^a-z]", "", x.lower()): x for x in NAMES.split()}
for synonym in ("lionfemale", "lionmale", "lioncub"):
    MAMMAL_LABELS[synonym] = "lion"


def normalize_name(label: str) -> str | None:
    return MAMMAL_LABELS.get(re.sub(r"[^a-z]", "", str(label).lower()))


def clock_bin(hour: int) -> str | None:
    if hour >= 21 or hour < 4:
        return "night"
    if 10 <= hour < 16:
        return "midday"
    return None


def project_from_filename(filename: str) -> str | None:
    prefix = str(filename).split("/", 1)[0].strip().upper()
    if prefix == EXCLUDED_OVERLAP_PROJECT:
        return "EXCLUDED_SER"
    return prefix if prefix in DISCOVERY + VALIDATION else None


def source_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


# One source JSON may contain bare NaN in optional annotations. For
# high-memory-efficiency incremental parsing, normalize *numeric value
# tokens only* into valid JSON null, preserving all original ZIP bytes
# untouched and retaining original source digest. No count, category,
# timestamp or location field is inferred from this conversion.
NONFINITE = re.compile(rb"(:[ \t\r\n]*)(?:NaN|-?Infinity)([ \t\r\n]*[,}\]])")


def normalise_json_stream(input_file, output_file, chunksize=4*1024*1024):
    pending = b""
    changed = 0
    while True:
        chunk = input_file.read(chunksize)
        if not chunk:
            break
        blob = pending + chunk
        if len(blob) <= 256:
            pending = blob
            continue
        cut = len(blob) - 256
        # Do not break an already-visible nonfinite numeric token.
        for found in NONFINITE.finditer(blob):
            if found.start() < cut < found.end():
                cut = found.start()
                break
        head, pending = blob[:cut], blob[cut:]
        head, n = NONFINITE.subn(lambda m: m.group(1)+b"null"+m.group(2), head)
        changed += n
        output_file.write(head)
    end, n = NONFINITE.subn(lambda m: m.group(1)+b"null"+m.group(2), pending)
    output_file.write(end)
    changed += n
    return changed


def _one_json_zip(path: Path, dest: Path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith(".json") and not n.endswith("/")]
        if len(names) != 1:
            raise ValueError("metadata ZIP must contain exactly one COCO JSON member")
        with archive.open(names[0]) as reader, dest.open("wb") as writer:
            return normalise_json_stream(reader, writer)


def _first_datetime(value):
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def collect_metadata(archive: Path) -> tuple[Counter, Counter, dict]:
    """Parse metadata only; hold image-to-sequence keys, not image content."""
    input_digest = source_sha256(archive)
    if input_digest != PINNED_SOURCE_SHA256:
        raise ValueError("Safari 2024 source archive SHA256 differs from first downloaded archive")
    qc = Counter()
    with tempfile.TemporaryDirectory() as temp:
        normalized = Path(temp)/"source_normalized.json"
        qc["nonfinite_json_tokens_normalized"] = _one_json_zip(archive, normalized)
        categories = {}
        with normalized.open("rb") as src:
            for cat in ijson.items(src, "categories.item"):
                categories[str(cat["id"])] = normalize_name(cat.get("name",""))
        qc["categories_listed"] = len(categories)
        if len(categories) < 30:
            raise ValueError("source category schema implausibly sparse")

        img_to_seq = {}
        first_time = {}
        location_ids = set()
        seen_projects = Counter()
        sampled_image_field_names = set()
        sampled_filename_head_components = Counter()
        sampled_presence = Counter()
        with normalized.open("rb") as src:
            for im in ijson.items(src, "images.item"):
                qc["images_seen"] += 1
                if qc["images_seen"] <= 50:
                    sampled_image_field_names.update(im)
                    sampled_filename_head_components[str(im.get("file_name", "")).split("/",1)[0]] += 1
                    for name in ("seq_id","location","datetime","file_name","id","date_captured"):
                        if im.get(name) not in (None, ""):
                            sampled_presence[name] += 1
                project = project_from_filename(im.get("file_name", ""))
                if project == "EXCLUDED_SER":
                    qc["excluded_SER_images"] += 1
                    continue
                if project is None:
                    qc["unknown_project_images"] += 1
                    continue
                seq = str(im.get("seq_id", "")).strip()
                loc = str(im.get("location", "")).strip()
                imageid = str(im.get("id", "")).strip()
                moment = _first_datetime(im.get("datetime"))
                if not seq or not loc or not imageid or moment is None:
                    qc["image_missing_sequence_location_time"] += 1
                    continue
                project = sys.intern(project)
                loc = sys.intern(loc)
                seq = sys.intern(seq)
                key = (project, loc, seq)
                if imageid in img_to_seq and img_to_seq[imageid] != key:
                    raise ValueError("one image ID maps to contradictory camera/sequence metadata")
                img_to_seq[imageid] = key
                old = first_time.get(key)
                if old is None or moment < old:
                    first_time[key] = moment
                seen_projects[project] += 1
                location_ids.add((project,loc))
        qc["source_projects_with_valid_image_metadata"] = len(seen_projects)
        qc["unique_project_camera_keys"] = len(location_ids)
        qc["distinct_included_sequences_with_time"] = len(first_time)
        qc["source_project_image_counts"] = dict(sorted(seen_projects.items()))
        if len(first_time) == 0:
            print("RESPONSE_BLIND_SAFARI_SCHEMA_DIAGNOSTIC="+json.dumps({
                "sampled_image_fields":sorted(sampled_image_field_names),
                "sampled_file_name_first_components":dict(sampled_filename_head_components),
                "sampled_presence_of_fixed_fields":dict(sampled_presence),
                "source_images_seen":qc["images_seen"],
                "unknown_project_images":qc["unknown_project_images"],
                "missing_sequence_location_time":qc["image_missing_sequence_location_time"],
                "recognized_camera_keys":len(location_ids),
            },sort_keys=True),flush=True)
            raise ValueError("no identified camera+sequence timestamps")

        seen = set()
        total_by_camera_species = Counter()
        clock_by_camera_species = Counter()
        observed_labels = Counter()
        with normalized.open("rb") as src:
            for anno in ijson.items(src, "annotations.item"):
                qc["annotation_rows_seen"] += 1
                species = categories.get(str(anno.get("category_id", "")))
                if not species:
                    qc["nonwhitelisted_or_nonwild_annotation"] += 1
                    continue
                imageid = str(anno.get("image_id", "")).strip()
                key = img_to_seq.get(imageid)
                if key is None:
                    qc["annotation_missing_valid_image"] += 1
                    continue
                seqspecies = (key, species)
                if seqspecies in seen:
                    qc["duplicate_burst_image_species_label"] += 1
                    continue
                seen.add(seqspecies)
                project, location, _sequence = key
                total_by_camera_species[(project,location,species)] += 1
                clock = clock_bin(first_time[key].hour)
                observed_labels[species] += 1
                qc["unique_wildlife_sequence_species_all_hours"] += 1
                if clock is None:
                    qc["excluded_dawn_dusk_other_hours"] += 1
                    continue
                clock_by_camera_species[(project,location,species,clock)] += 1
                qc["unique_wildlife_sequence_species_focal_hours"] += 1
        qc["included_recognized_mammal_labels"] = len(observed_labels)
        qc["whitelisted_mammal_sequence_species_counts"] = dict(sorted(observed_labels.items()))
    return total_by_camera_species, clock_by_camera_species, {
        "input_source_zip_sha256": input_digest,
        "quality": dict(qc),
    }


def select_panel(full_counts: Counter) -> list[str]:
    """Only discovery park/camera occurrence, not clock-time or holdout."""
    support = defaultdict(lambda: defaultdict(set))
    all_events = Counter()
    for (project, camera, animal), n in full_counts.items():
        if project not in DISCOVERY:
            continue
        all_events[animal] += n
        if n >= MIN_CAMERA_EVENTS:
            support[animal][project].add(camera)
    species = sorted(
        all_events, key=lambda animal: (
            -sum(len(cameras)>=MIN_CAMERAS_PER_PROJECT_PAIR for cameras in support[animal].values()),
            -sum(map(len,support[animal].values())),
            -all_events[animal], animal
        )
    )
    return species[:TOP_TAXA]


def _project_effect(counts: Counter, animal1: str, animal2: str, project: str) -> dict:
    cameras = {camera for (p,camera,species,clock) in counts
               if p==project and species in (animal1,animal2)}
    values = []
    for camera in cameras:
        ni = counts[(project,camera,animal1,"night")]
        di = counts[(project,camera,animal1,"midday")]
        nj = counts[(project,camera,animal2,"night")]
        dj = counts[(project,camera,animal2,"midday")]
        if (ni+di)<MIN_CAMERA_EVENTS or (nj+dj)<MIN_CAMERA_EVENTS:
            continue
        odds = math.log((ni+0.5)/(di+0.5)) - math.log((nj+0.5)/(dj+0.5))
        values.append(odds)
    return {
        "informative_camera_count": len(values),
        "status": "DESCRIPTIVE_CAMERA_COMPARABLE" if len(values)>=MIN_CAMERAS_PER_PROJECT_PAIR else "NOT_ESTIMABLE",
        "median_camera_relative_log_nocturnality": median(values) if len(values)>=MIN_CAMERAS_PER_PROJECT_PAIR else None,
    }


def _partition(park_rows: dict[str,dict], projects: tuple[str,...]) -> dict:
    qualified = [(p,park_rows[p]["median_camera_relative_log_nocturnality"])
                 for p in projects if park_rows[p]["status"]=="DESCRIPTIVE_CAMERA_COMPARABLE"]
    values = [x for _,x in qualified]
    out = {
        "eligible_projects":len(values),
        "status":"DESCRIPTIVE_TRANSFER_PARTITION" if len(values)>=MIN_PARKS_PER_PARTITION else "INSUFFICIENT_CROSSPARK_SUPPORT",
        "median_of_equal_project_medians":median(values) if len(values)>=MIN_PARKS_PER_PARTITION else None,
        "leave_one_project_out":{
            "all_computable":False,"min":None,"max":None,"sign_stable":False,
        }
    }
    if len(values)>=MIN_PARKS_PER_PARTITION+1:
        loo=[median(values[:i]+values[i+1:]) for i in range(len(values))]
        original=out["median_of_equal_project_medians"]
        out["leave_one_project_out"] = {
            "all_computable":True,"min":min(loo),"max":max(loo),
            "sign_stable":original!=0 and (
                all(v>0 for v in loo) if original>0 else all(v<0 for v in loo)
            )
        }
    return out


def pair_results(counts: Counter, roster: list[str]) -> dict:
    from itertools import combinations
    allrows = []
    for a,b in combinations(sorted(roster),2):
        perpark={p:_project_effect(counts,a,b,p) for p in DISCOVERY+VALIDATION}
        discovery = _partition(perpark, DISCOVERY)
        validation = _partition(perpark, VALIDATION)
        comparable = (discovery["status"]==validation["status"]=="DESCRIPTIVE_TRANSFER_PARTITION")
        old,new=discovery["median_of_equal_project_medians"],validation["median_of_equal_project_medians"]
        same=bool(comparable and old*new>0)
        robust=bool(same and discovery["leave_one_project_out"]["sign_stable"]
                    and validation["leave_one_project_out"]["sign_stable"])
        allrows.append({
            "species_1":a,"species_2":b,"all_14_projects":perpark,
            "discovery":discovery,"validation":validation,
            "comparable_both":comparable,
            "discovery_validation_same_direction":same,
            "same_direction_survives_leave_one_project":robust,
        })
    paired=[r for r in allrows if r["comparable_both"]]
    skill = None
    if paired:
        baseline=math.fsum(r["validation"]["median_of_equal_project_medians"]**2 for r in paired)
        if baseline>0:
            error=math.fsum(
                (r["validation"]["median_of_equal_project_medians"] -
                 r["discovery"]["median_of_equal_project_medians"])**2 for r in paired)
            skill=1-error/baseline
    return {
        "all_unordered_pairs":len(allrows),
        "discovery_estimable_pairs":sum(r["discovery"]["status"]=="DESCRIPTIVE_TRANSFER_PARTITION" for r in allrows),
        "validation_estimable_pairs":sum(r["validation"]["status"]=="DESCRIPTIVE_TRANSFER_PARTITION" for r in allrows),
        "both_estimable_pairs":len(paired),
        "pair_direction_concordant":sum(r["discovery_validation_same_direction"] for r in paired),
        "leave_one_project_robust_direction_concordant":sum(r["same_direction_survives_leave_one_project"] for r in paired),
        "discovery_effect_on_validation_relative_skill_vs_zero":skill,
        "full_66_pair_matrix":allrows,
    }


def run(source_zip: Path):
    full,clock,receipt=collect_metadata(source_zip)
    qc=receipt["quality"]
    if qc["source_projects_with_valid_image_metadata"] < 12:
        raise ValueError("too few non-SER source projects; source schema/camera identity incomplete")
    panel=select_panel(full)
    if len(panel)<2:
        raise ValueError("too few discovery-supported wild mammal taxa")
    print("FROZEN_S14_DISCOVERY_PANEL_BEFORE_VALIDATION="+json.dumps(panel),flush=True)
    results=pair_results(clock,panel)
    return {
        "schema_version":1,
        "status":"S14_CROSS_RESERVE_RECORDED_DIEL_RANKING_DESCRIPTIVE_RESULT",
        "source":{"url":SOURCE_URL,"original_zip_sha256":receipt["input_source_zip_sha256"],
                  "no_wildlife_images_downloaded":True},
        "design":{
            "excluded_E7_overlap_project":"SER","discovery_projects":list(DISCOVERY),
            "heldout_validation_projects":list(VALIDATION),
            "species_selected_by_discovery_only_full_day_camera_presence":True,
            "selected_taxon_panel":panel,"fixed_max_taxa":TOP_TAXA,
            "min_sequences_per_species_in_one_diel_camera":MIN_CAMERA_EVENTS,
            "min_shared_cameras_per_project":MIN_CAMERAS_PER_PROJECT_PAIR,
            "min_projects_per_partition":MIN_PARKS_PER_PARTITION,
            "night":"21:00–03:59","midday":"10:00–15:59",
            "fixed_Jeffreys_half_record_continuity_correction":True
        },
        "quality":qc,
        "results":results,
        "limitations":{
            "different_park_networks_are_not_replicated_sensor_calibration":True,
            "camera_effort_and_species_differential_detection_not_identified":True,
            "time_year_environment_not_matched_across_parks":True,
            "species_pair_edges_share_species_and_cameras_not_independent_trials":True,
            "ecological_causal_processes_not_identified":True,
            "source_Serengeti_E7_project_excluded":True,
            "previous_E4_E5_E7_E7C_results_changed":False,
            "E5_original_qualified_datasets":0,"E5_G4_passed":False,
            "no_event_level_pvalues_or_CIs":True
        }
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "selected_taxa":result["design"]["selected_taxon_panel"],
        "source_sha256":result["source"]["original_zip_sha256"],
        "images_seen":result["quality"]["images_seen"],
        "nonoverlap_projects":result["quality"]["source_projects_with_valid_image_metadata"],
        "discovery_pairs":result["results"]["discovery_estimable_pairs"],
        "validation_pairs":result["results"]["validation_estimable_pairs"],
        "both_comparable":result["results"]["both_estimable_pairs"],
        "direction_concordant":result["results"]["pair_direction_concordant"],
        "project_leaveoneout_stable":result["results"]["leave_one_project_robust_direction_concordant"],
        "transfer_skill":result["results"]["discovery_effect_on_validation_relative_skill_vs_zero"],
    },sort_keys=True))


if __name__=="__main__":
    main()
