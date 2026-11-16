#!/usr/bin/env python3
"""Read-only, post-outcome Safari14 fixed-margins park-pair contrasts.

Consumes only the SHA-pinned 2026-11-14 aggregate Actions ZIP. No imagery,
raw camera-by-species matrix, observations, re-randomization, or model fit.
The landscape/biome links are retrospective examples from public LILA park
DESCRIPTIONS; they are not pre-registered environmental covariates.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from zipfile import ZipFile

ARTIFACT_ID = 14107094556
ZIP_SHA256 = "a9f32536b4120c249abd57c59981e6cfcaab4deb19016b788a0000ac35bd06dc"
JSON_SHA256 = "4dcf8212510524dccefbfa250e05277fe55085f3b838c33a1c5f7fc8ee593b5e"
INNER_NAME = "SAFARI14_FIXED_MARGINS_NULL_RESULT.json"
SPLITS = {
    "discovery": ("APN", "CDB", "ENO", "KAR", "KGA", "KRU", "LEC"),
    "validation": ("MAD", "MTZ", "PLN", "RUA", "TSW"),
}
# The following links were identified after seeing the original contrasts.
# Their evidence is the 2024 LILA project-description page (not raw GPS/biome).
REPORTED_ECOLOGICAL_LINKS = {
    ("APN", "KRU"): "adjacent unfenced APNR-Kruger grid/woodland transect",
    ("CDB", "KAR"): "shared named Nama Karoo biome",
    ("KGA", "LEC"): "shared named Kalahari region",
}
SOURCE_PAGE = "https://lila.science/datasets/snapshot-safari-2024-expansion/"


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_pinned_archive(path: Path) -> dict:
    raw = path.read_bytes()
    if _digest(raw) != ZIP_SHA256:
        raise ValueError("original frozen Actions ZIP SHA256 mismatch")
    with ZipFile(path) as archive:
        if archive.namelist() != [INNER_NAME]:
            raise ValueError("unexpected frozen Actions ZIP member layout")
        content = archive.read(INNER_NAME)
    if _digest(content) != JSON_SHA256:
        raise ValueError("original frozen JSON SHA256 mismatch")
    return json.loads(content)


def _finite_unit(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: expected numeric beta value")
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label}: beta value outside [0, 1]")
    return value


def validate_partition(rows: list[dict], parks: tuple[str, ...]) -> list[dict]:
    expected = set(combinations(parks, 2))
    found = set()
    validated = []
    for row in rows:
        pair = (row["project_1"], row["project_2"])
        if pair not in expected or pair in found:
            raise ValueError(f"duplicate/unexpected park pair: {pair}")
        found.add(pair)
        a = _finite_unit(row["original_observed_sim_median"], f"{pair} observed")
        b = _finite_unit(row["null_sim_median"], f"{pair} null")
        excess = row["median_sim_excess_vs_null"]
        if isinstance(excess, bool) or not isinstance(excess, (int, float)) or not math.isfinite(excess):
            raise ValueError(f"{pair}: nonfinite excess")
        if not math.isclose(a - b, excess, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"{pair}: observed-null arithmetic mismatch")
        if row["null_pair_draws_estimable"] != 500:
            raise ValueError(f"{pair}: original null-pair support drift")
        validated.append({"pair": pair, "excess": float(excess), "observed": a, "null": b})
    if found != expected:
        raise ValueError(f"incomplete original park-pair support: {len(found)}/{len(expected)}")
    return validated


def summarize(rows: list[dict], parks: tuple[str, ...], *,
              linked: dict[tuple[str, str], str] | None = None) -> dict:
    """Reaggregates medians OF pair-level median excess, not the S14-FM main statistic."""
    linked = linked or {}
    allpairs = validate_partition(rows, parks)
    loo = []
    for removed in parks:
        retained = [x for x in allpairs if removed not in x["pair"]]
        loo.append({
            "omitted_park": removed,
            "remaining_pairs": len(retained),
            "positive_pairs": sum(x["excess"] > 0 for x in retained),
            "negative_pairs": sum(x["excess"] < 0 for x in retained),
            "median_of_pair_level_excess": median(x["excess"] for x in retained),
        })
    out = {
        "pair_count": len(allpairs),
        "positive_pair_count": sum(x["excess"] > 0 for x in allpairs),
        "negative_pair_count": sum(x["excess"] < 0 for x in allpairs),
        "median_of_pair_level_excess": median(x["excess"] for x in allpairs),
        "leave_one_park_out": loo,
        "leave_one_park_positive_count": sum(x["median_of_pair_level_excess"] > 0 for x in loo),
        "leave_one_park_min_median": min(x["median_of_pair_level_excess"] for x in loo),
        "leave_one_park_max_median": max(x["median_of_pair_level_excess"] for x in loo),
    }
    if linked:
        if not set(linked).issubset({x["pair"] for x in allpairs}):
            raise ValueError("ecological link not present in the expected original pairs")
        chosen = [x for x in allpairs if x["pair"] in linked]
        rest = [x for x in allpairs if x["pair"] not in linked]
        if not chosen or not rest:
            raise ValueError("ecological link comparison is not estimable")
        ranks = {x["pair"]: idx + 1 for idx, x in enumerate(
            sorted(allpairs, key=lambda r: (r["excess"], r["pair"])))}
        out["retrospective_named_landscape_links"] = {
            "status": "POST_OUTCOME_EXPLORATORY_NOT_CONFIRMED",
            "source": SOURCE_PAGE,
            "matched_pairs": [{"park_pair": list(x["pair"]), "source_description": linked[x["pair"]],
                               "observed_beta_sim_pair_median": x["observed"],
                               "null_beta_sim_pair_median": x["null"],
                               "pair_median_excess": x["excess"],
                               "low_excess_rank_among_all_pairs": ranks[x["pair"]]}
                              for x in chosen],
            "matched_pair_count": len(chosen),
            "unmatched_pair_count": len(rest),
            "matched_median_excess": median(x["excess"] for x in chosen),
            "unmatched_median_excess": median(x["excess"] for x in rest),
            "matched_minus_unmatched_median_excess": (
                median(x["excess"] for x in chosen) - median(x["excess"] for x in rest)),
        }
    return out


def analyze(original: dict) -> dict:
    if original.get("schema_version") != 1 or original.get("status") != "S14_POSTRESULT_CAMERA_SPECIES_FIXED_MARGIN_SENSITIVITY":
        raise ValueError("not the frozen S14-FM source schema")
    if original.get("source", {}).get("safari14_original_result_sha256") != "f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7":
        raise ValueError("upstream original S14 result drift")
    if not original.get("strong_descriptive_excess_in_both_partitions"):
        raise ValueError("upstream decision changed")
    if set(original["per_partition"]) != set(SPLITS):
        raise ValueError("unexpected partition universe")
    out = {}
    for group, parks in SPLITS.items():
        part = original["per_partition"][group]
        if part.get("fully_eligible_paired_draws") != 500:
            raise ValueError("upstream S14-FM paired-draw support drift")
        landscape = REPORTED_ECOLOGICAL_LINKS if group == "discovery" else {}
        out[group] = summarize(part["all_within_partition_park_pair_summaries"], parks, linked=landscape)
    return {
        "schema_version": 1,
        "status": "AGGREGATE_ONLY_POST_OUTCOME_PARK_PAIR_SENSITIVITY",
        "source": {"artifact_id": ARTIFACT_ID, "artifact_zip_sha256": ZIP_SHA256,
                   "inner_json_sha256": JSON_SHA256, "reopened_wildlife_source": False,
                   "downloaded_wildlife_images": False},
        "metric": "median across ORIGINAL park-pair medians of (observed beta_sim - fixed-margins null beta_sim)",
        "metric_not_original_primary_paired_draw_median": True,
        "partitions": out,
        "inference_limits": {
            "source_description_link_pairs_selected_after_outcomes_known": True,
            "source_descriptions_are_not_spatial_distance_or_biome_GIS_covariates": True,
            "park_pairs_not_independent": True,
            "leave_one_out_values_not_confidence_intervals": True,
            "no_new_ecological_process_or_detection_identified": True,
            "original_S14_FM_E4_E5_E7_E7C_decisions_unchanged": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = analyze(load_pinned_archive(args.source_zip))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({p: {"loo_positive": r["leave_one_park_positive_count"],
                          "loo_total": len(r["leave_one_park_out"])}
                      for p, r in summary["partitions"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
