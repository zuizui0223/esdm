#!/usr/bin/env python3
"""Post-publication descriptive Findlay CCTV passage detection stages.

Only the two exactly pinned FOX/BADGER source CSVs may be accessed. This is
explicitly *not* a response-blind E5 transfer validation or preregistration.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen
import argparse

EXPECTED_ID = "e5-findlay-known-pass-stage-descriptive-v1"
SOURCE_COMMIT = "abc72f535bb59ebed202fb7acca852fc1647e97a"
SOURCE_REPO = "melaniefindlay/CT-Detection"
BINS = ("near_le_1m", "mid_1_to_3m", "far_gt_3m")
SPECIES = ("BADGER", "FOX")


def git_blob_sha(blob: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest()


def download_pinned_file(spec: dict) -> bytes:
    if spec["name"] not in ("TRIGGER_FOX_BADGER.csv", "REGISTRATION_FOX_BADGER.csv"):
        raise ValueError("unfrozen file requested")
    url = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/{spec['name']}"
    req = Request(url, headers={"User-Agent": "esdm-Findlay-pass-stage/1"})
    with urlopen(req, timeout=60) as response:
        blob = response.read(spec["bytes"] + 1)
    if len(blob) != spec["bytes"] or git_blob_sha(blob) != spec["sha"]:
        raise ValueError("pinned source bytes/blob SHA mismatch")
    return blob


def parse_binary(x: str) -> int | None:
    s = x.strip()
    return int(s) if s in ("0", "1") else None


def distance_bin(x: str) -> str | None:
    try:
        d = float(x)
    except (ValueError, TypeError):
        return None
    if not math.isfinite(d) or d <= 0:
        return None
    if d <= 1:
        return BINS[0]
    if d <= 3:
        return BINS[1]
    return BINS[2]


def count_records(blob: bytes, *, mode: str) -> tuple[dict, dict]:
    if mode not in ("trigger", "registration"):
        raise ValueError("unrecognized stage")
    reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig"), newline=""))
    required = {"SPECIES", "ORIENT", "DIST", "TRIGGER"}
    if mode == "registration":
        required.add("CAPTURE")
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("pinned source header lacks stage fields")
    counters = defaultdict(Counter)
    qc = Counter()
    for row in reader:
        qc["all_rows"] += 1
        if row.get("SPECIES", "").strip().upper() not in SPECIES:
            qc["other_species"] += 1
            continue
        if row.get("ORIENT", "").strip().upper() != "L":
            qc["not_lateral"] += 1
            continue
        key = distance_bin(row.get("DIST", ""))
        if key is None:
            qc["invalid_distance"] += 1
            continue
        trigger = parse_binary(row.get("TRIGGER", ""))
        if trigger is None:
            qc["invalid_trigger"] += 1
            continue
        if mode == "registration" and trigger != 1:
            qc["registration_untriggered_excluded"] += 1
            continue
        if mode == "registration":
            capture = parse_binary(row.get("CAPTURE", ""))
            if capture is None:
                qc["invalid_capture"] += 1
                continue
        species = row["SPECIES"].strip().upper()
        stat = counters[(species, key)]
        stat["denominator"] += 1
        stat["numerator"] += capture if mode == "registration" else trigger
        qc["eligible_rows"] += 1
    return counters, dict(qc)


def summarize(contract: dict, input_bytes: dict[str, bytes]) -> dict:
    if contract["contract_id"] != EXPECTED_ID:
        raise ValueError("contract ID drift")
    if contract["status"] != "FROZEN_RETROSPECTIVE_PUBLISHED_DIRECTION_EXPOSED_NOT_AUTHORIZED":
        raise ValueError("contract status drift")
    if contract["source"]["commit"] != SOURCE_COMMIT:
        raise ValueError("source commit drift")
    files = contract["source"]["files"]
    if [x["name"] for x in files] != ["TRIGGER_FOX_BADGER.csv", "REGISTRATION_FOX_BADGER.csv"]:
        raise ValueError("file list altered")
    for spec in files:
        blob = input_bytes[spec["name"]]
        if len(blob) != spec["bytes"] or git_blob_sha(blob) != spec["sha"]:
            raise ValueError("source file blob mismatch")
    trig, tqc = count_records(input_bytes[files[0]["name"]], mode="trigger")
    reg, rqc = count_records(input_bytes[files[1]["name"]], mode="registration")
    minref = contract["cohort_rules"]["minimum_reference_passes_per_bin"]
    mintrigger = contract["cohort_rules"]["minimum_triggered_passes_per_bin"]
    stage_rows = []
    by_species = {}
    for species in SPECIES:
        cells = {}
        for b in BINS:
            t = trig[(species, b)]
            r = reg[(species, b)]
            n_ref, n_trigger = t["denominator"], t["numerator"]
            n_reg, n_registered = r["denominator"], r["numerator"]
            cohorts_align = n_trigger == n_reg
            supported = n_ref >= minref and n_reg >= mintrigger
            ptrig = n_trigger / n_ref if n_ref else None
            preg = n_registered / n_reg if n_reg else None
            ptotal = ptrig * preg if supported and cohorts_align else None
            row = {
                "species":species,"distance_bin":b,
                "cctv_reference_passes":n_ref,
                "triggered_reference_passes":n_trigger,
                "registration_eligible_triggered_rows":n_reg,
                "registered_images":n_registered,
                "triggered_cohorts_align":cohorts_align,
                "predeclared_support_sufficient":supported,
                "p_trigger":ptrig,"p_registration_given_trigger":preg,
                "p_composite_given_pass":ptotal,
            }
            stage_rows.append(row)
            cells[b] = row
        near,far = cells[BINS[0]],cells[BINS[-1]]
        required = (near,far)
        if not all(x["triggered_cohorts_align"] for x in required):
            contrast = {"status":"COHORT_NONCOMPARABLE"}
        elif not all(x["predeclared_support_sufficient"] for x in required):
            contrast = {"status":"INSUFFICIENT_BIN_SUPPORT"}
        elif not all(
            x[k] is not None and x[k] > 0
            for x in required
            for k in ("p_trigger","p_registration_given_trigger","p_composite_given_pass")
        ):
            contrast = {"status":"ZERO_PROBABILITY_LOG_UNDEFINED"}
        else:
            lt = math.log(far["p_trigger"]/near["p_trigger"])
            lr = math.log(
                far["p_registration_given_trigger"]/near["p_registration_given_trigger"]
            )
            lc = math.log(
                far["p_composite_given_pass"]/near["p_composite_given_pass"]
            )
            assert abs(lc-(lt+lr)) < 1e-10
            if abs(lt) <= 1e-12 or abs(lr) <= 1e-12:
                status = "DESCRIPTIVE_STAGE_STABILITY"
            else:
                status = ("DESCRIPTIVE_OPPOSING_STAGES" if lt*lr < 0
                          else "DESCRIPTIVE_SAME_DIRECTION_STAGES")
            denom = abs(lt)+abs(lr)
            contrast = {
                "status":status,
                "log_far_vs_near_trigger":lt,
                "log_far_vs_near_registration":lr,
                "log_far_vs_near_composite":lc,
                "compensation_index":1-abs(lc)/denom if denom else None,
            }
        by_species[species] = contrast
    return {
        "schema_version":1,
        "route_id":EXPECTED_ID,
        "status":"RETROSPECTIVE_DESCRIPTIVE_COMPLETED_NO_E5_GATE_PROMOTION",
        "source_commit":SOURCE_COMMIT,
        "fixed_distance_bins":list(BINS),
        "stage_cells":stage_rows,
        "primary_far_vs_near_by_species":by_species,
        "exclusion_counts":{"trigger":tqc,"registration":rqc},
        "boundary":{
            "published_direction_exposed_before_contract":True,
            "biological_CSVs_decoded_for_this_separate_route":2,
            "no_model_fitted":True,
            "no_inferential_confidence_interval":True,
            "no_geographic_transfer_claim":True,
            "original_E5_G4_passed":False,
            "original_E5_qualified_candidates":0,
            "wildpig_and_rhode_frozen_outcomes_unchanged":True,
            "raw_event_records_uploaded":False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    inputs = {x["name"]:download_pinned_file(x) for x in contract["source"]["files"]}
    result = summarize(contract, inputs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
