"""Validate and summarize all prelisted BIEN countries without pooling AUCs.

Only aggregate public receipts are read. The two prior CR/PA files are pinned
byte-for-byte; new country membership and original training counts are checked.
Detailed taxon/frame results remain in their untouched input receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess


COUNTRIES = ("BR", "CR", "EC", "GF", "GT", "HN", "NI", "PA", "PE", "SV")
NEW_COUNTRIES = tuple(c for c in COUNTRIES if c not in ("CR", "PA"))
MODES = ("primary_2000_2025", "known_precision_2000_2025", "historical_undated_descriptive")
STATUSES = ("EVALUABLE_EXPLORATORY", "NO_ELIGIBLE_POSITIVE_CELLS",
            "NO_WITHIN_FRAME_COMPARISON", "NO_MATCH_UNKNOWN")
METHODS = {"method_metadata_present": "METHOD_METADATA_PRESENT",
           "method_metadata_missing": "METHOD_METADATA_MISSING"}
FIXED106_SHA256 = "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
FROZEN_COMMIT = "d65817fcb3c39060ed544261c291d76a198299c6"
EXTENSION_COMMIT = "32d949b8b63c2adfa4918fda22e842a05cd58e72"
PRIOR_COMPARISON_COMMIT = "32aa43987b5ac4e2ce4c279504ddcc9732bd0b0c"
PRIOR_RESULT_SHA = "fa8342ab203152b8ec347653961612142b19a9e44ca20864904b540e7ed1f788"
PRIOR_ACQUISITION_SHA = "1a1635c23f3100d9794a55eb3f56bf96b5f5285cfffe5e97db114acee9053863"
TRAINING_PATH = "docs/replication/neobat/plant_106x17_source_effort_transfer.json"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_prior(path, expected_sha):
    _require(_sha(path) == expected_sha, "prior receipt SHA mismatch")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def quantiles(values):
    values = sorted(values)
    _require(all(math.isfinite(x) and 0 <= x <= 1 for x in values), "invalid AUC summary input")
    if not values:
        return {"n": 0, "median": None, "q1": None, "q3": None}

    def at(p):
        index = (len(values) - 1) * p
        lo, hi = math.floor(index), math.ceil(index)
        return values[lo] + (index - lo) * (values[hi] - values[lo])

    return {"n": len(values), "median": at(.5), "q1": at(.25), "q3": at(.75)}


def _support(contrasts):
    pairs = Counter((f["positive_cells"], f["background_cells"]) for f in contrasts)
    return {
        "contrasts": len(contrasts),
        "one_positive_one_background_contrasts": pairs.get((1, 1), 0),
        "positive_cells_min": min((p for p, _ in pairs), default=None),
        "positive_cells_max": max((p for p, _ in pairs), default=None),
        "background_cells_min": min((b for _, b in pairs), default=None),
        "background_cells_max": max((b for _, b in pairs), default=None),
        "cell_count_distribution": [
            {"positive_cells": p, "background_cells": b, "contrasts": n}
            for (p, b), n in sorted(pairs.items())
        ],
    }


def country_summary(data, taxa):
    """Summarize per-taxon frame means separately by metadata class."""
    rows = data["taxon_results"]
    names = [r["taxon"] for r in rows]
    _require(len(names) == len(taxa) and len(set(names)) == len(taxa)
             and set(names) == set(taxa), "country taxon universe mismatch")
    coverage = data["coverage"]
    _require(sum(r["matched_records"] > 0 for r in rows) == coverage["matched_taxa"],
             "matched taxon coverage mismatch")
    _require(sum(r["matched_records"] for r in rows) == coverage["matched_records"],
             "matched record coverage mismatch")
    result = {
        "country": data["country"],
        "total_records": coverage["total_records"],
        "matched_taxa": coverage["matched_taxa"],
        "matched_records": coverage["matched_records"],
        "survey_frames": coverage["survey_frames"],
        "records_invalid_coordinates": coverage.get("records_invalid_coordinates"),
        "records_unknown_year": coverage.get("records_unknown_year"),
        "records_before_2000": coverage.get("records_before_2000"),
        "records_unknown_precision": coverage.get("records_unknown_precision"),
        "modes": {},
    }
    for mode in MODES:
        statuses = Counter()
        means = {key: [] for key in METHODS}
        class_contrasts = {key: [] for key in METHODS}
        all_contrasts = []
        for row in rows:
            _require(set(row["modes"]) == set(MODES), "taxon mode universe mismatch")
            value = row["modes"][mode]
            _require(value["status"] in STATUSES, "unknown result status")
            statuses[value["status"]] += 1
            frames = value["frame_results"]
            _require(len({f["frame_id"] for f in frames}) == len(frames), "duplicate taxon frame")
            contrasts = []
            for frame in frames:
                _require(frame["method_class"] in METHODS.values(), "unknown method class")
                has_pair = frame["positive_cells"] > 0 and frame["background_cells"] > 0
                _require((frame["auc"] is not None) == has_pair, "AUC/cell-count inconsistency")
                if has_pair:
                    _require(math.isfinite(frame["auc"]) and 0 <= frame["auc"] <= 1,
                             "invalid frame AUC")
                    contrasts.append(frame)
            expected_status = ("NO_MATCH_UNKNOWN" if row["matched_records"] == 0 else
                               "NO_ELIGIBLE_POSITIVE_CELLS" if value["retained_positive_cells"] == 0 else
                               "EVALUABLE_EXPLORATORY" if contrasts else "NO_WITHIN_FRAME_COMPARISON")
            _require(value["status"] == expected_status, "taxon status inconsistency")
            all_contrasts.extend(contrasts)
            for key, method in METHODS.items():
                selected = [f for f in contrasts if f["method_class"] == method]
                reported = value[key]
                _require(reported["estimable_frames"] == len(selected), "estimable frame count mismatch")
                if selected:
                    mean = math.fsum(f["auc"] for f in selected) / len(selected)
                    _require(reported["mean_frame_auc"] is not None and
                             math.isclose(mean, reported["mean_frame_auc"], rel_tol=1e-12, abs_tol=1e-12),
                             "stored frame mean mismatch")
                    means[key].append(mean)
                    class_contrasts[key].extend(selected)
                else:
                    _require(reported["mean_frame_auc"] is None, "empty frame mean must be null")
        observed = coverage["modes"][mode]
        _require(dict(statuses) == observed["taxon_status_counts"], "country status totals mismatch")
        result["modes"][mode] = {
            "eligible_records_before_taxon_training_exclusion": observed["eligible_records_before_taxon_training_exclusion"],
            "sampled_cells_before_taxon_training_exclusion": observed["sampled_cells_before_taxon_training_exclusion"],
            "taxon_status_counts": {s: statuses[s] for s in STATUSES},
            "estimable_taxon_frame_contrasts": len(all_contrasts),
            "all_contrast_support": _support(all_contrasts),
            **{key: {"taxon_mean_auc": quantiles(means[key]),
                     "contrast_support": _support(class_contrasts[key])}
               for key in METHODS},
        }
    return result


def _validate_result(data, countries, taxa, original_counts, comparison_commit, old=False):
    expected_status = ("EXPLORATORY_BIEN_CR_PA_FIXED106_PLANT_DIAGNOSTIC_COMPLETE" if old else
                       "EXPLORATORY_BIEN_FIXED106_PLANT_DIAGNOSTIC_COMPLETE")
    _require(data["status"] == expected_status, "diagnostic did not complete")
    _require(set(data["countries"]) == set(countries), "diagnostic country scope mismatch")
    _require(data["comparison_frozen_commit"] == comparison_commit, "comparison commit mismatch")
    _require(data["fixed106_taxa_sha256"] == FIXED106_SHA256 and
             tuple(data["modes"]) == MODES, "fixed roster or modes changed")
    n = len(countries) * len(taxa)
    _require(data["taxon_country_results_per_mode"] == n, "result denominator mismatch")
    provenance = data["model_provenance"]
    _require(provenance["frozen_code_commit"] == FROZEN_COMMIT and
             provenance["plant_taxon_count"] == len(taxa) and
             set(provenance["countries"]) == set(countries), "model scope mismatch")
    _require(provenance["expected_fit_count"] == provenance["completed_fit_count"] == n and
             provenance["pinned_package_versions_match"] is True, "model replay incomplete or versions differ")
    fits = provenance["training_fits"]
    expected = {(c, t) for c in countries for t in taxa}
    actual = [(f["country"], f["taxon"]) for f in fits]
    _require(len(actual) == n and set(actual) == expected, "training pair universe mismatch")
    for fit in fits:
        original = original_counts[fit["country"], fit["taxon"]]
        _require((fit["train_positive_rows"], fit["train_background_rows"]) == original and
                 (fit["expected_train_positive_rows"], fit["expected_train_background_rows"]) == original,
                 "original training counts mismatch")
        _require(fit["original_training_counts_match"] is True and
                 fit["training_cell_membership_matches_original_fit_rows"] is True,
                 "training membership verification missing")
    for country in countries:
        _require(data["countries"][country]["country"] == country, "nested country scope mismatch")


def combine_results(prior, new_results, taxa, original_counts):
    """Require all eight new countries, then validate all 1,060 result pairs."""
    _require(len(taxa) == len(set(taxa)) == 106, "fixed 106 taxon universe required")
    _require(set(new_results) == set(NEW_COUNTRIES), "all eight new countries are required")
    _validate_result(prior, ("CR", "PA"), taxa, original_counts, PRIOR_COMPARISON_COMMIT, old=True)
    for country in NEW_COUNTRIES:
        _validate_result(new_results[country], (country,), taxa, original_counts, EXTENSION_COMMIT)
    countries = {}
    for country in COUNTRIES:
        payload = prior if country in ("CR", "PA") else new_results[country]
        countries[country] = country_summary(payload["countries"][country], taxa)
        countries[country]["evidence_stage"] = ("PREVIOUSLY_OPENED_CR_PA" if country in ("CR", "PA")
                                                   else "NEW_PRELISTED_COUNTRY")
        countries[country]["execution_commit"] = payload["execution_commit"]
    return {
        "schema_version": 1,
        "status": "EXPLORATORY_BIEN_PRELISTED_FIXED10_DIAGNOSTIC_COMPLETE",
        "fixed106_taxa_sha256": FIXED106_SHA256,
        "country_order": list(COUNTRIES), "plant_taxa": list(taxa),
        "new_countries": list(NEW_COUNTRIES), "previously_opened_countries": ["CR", "PA"],
        "taxon_country_results_per_mode": 1060,
        "new_fits_validated": 848, "previous_fits_reused": 212,
        "all_original_training_count_records_validated": 1060,
        "mode_status_totals": {
            mode: {status: sum(c["modes"][mode]["taxon_status_counts"][status] for c in countries.values())
                   for status in STATUSES} for mode in MODES},
        "countries": countries,
        "interpretation": {
            "scope": "unchanged exploratory within-source-frame plant climate ranking across prelisted countries",
            "quantiles": "linear interpolation at (n-1)*p of per-taxon equal-frame means, separately by method metadata class",
            "country_taxa_with_no_metric_remain_in_status_denominator": True,
            "pooled_overall_auc_computed": False,
            "source_independence_established": False,
            "independent_geographic_replicates_assumed": False,
            "ecological_M3_estimated": False,
            "bat_improvement_estimated": False,
            "background_means_absence": False,
            "unknown_coordinate_precision_is_verified_precision": False,
        },
    }


def _original_counts(frozen_root):
    frozen_root = Path(frozen_root)
    head = subprocess.run(["git", "-C", str(frozen_root), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    _require(head == FROZEN_COMMIT, "original checkout commit mismatch")
    raw = (frozen_root / TRAINING_PATH).read_bytes()
    expected_blob = subprocess.run(
        ["git", "-C", str(frozen_root), "rev-parse", f"{FROZEN_COMMIT}:{TRAINING_PATH}"],
        check=True, capture_output=True, text=True).stdout.strip()
    actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    _require(actual_blob == expected_blob, "original training receipt bytes changed")
    rows = json.loads(raw)["plant_country_source_rank_results"]
    counts = {(r["holdout_country"], r["plant"]):
              (r["train_source_matched_focal_cells"], r["train_source_matched_target_background_cells"])
              for r in rows}
    _require(len(counts) == len(rows) == 1802, "original training receipt universe changed")
    return counts, {"commit": head, "path": TRAINING_PATH, "git_blob_sha": actual_blob,
                    "sha256": hashlib.sha256(raw).hexdigest()}


def _acquisition_check(acquisition, diagnostic, country):
    _require(acquisition["status"] == "BIEN_EXTERNAL_ACQUISITION_COMPLETE" and
             acquisition["fixed106_taxa_sha256"] == FIXED106_SHA256,
             "country acquisition did not complete")
    acquired = acquisition["countries"][country]
    result = diagnostic["countries"][country]
    coverage = result["coverage"]
    _require(acquired["total_rows"] == coverage["total_records"] and
             acquired["matched_taxa"] == coverage["matched_taxa"] and
             acquired["focal_record_rows"] == coverage["matched_records"],
             "acquisition/result counts mismatch")
    _require(all(acquired["focal_record_counts"][r["taxon"]] == r["matched_records"]
                 for r in result["taxon_results"]), "per-taxon acquisition/result counts mismatch")
    ids = {f["datasource_id"] for f in result["frames"] if f["datasource_id"]}
    sources = {str(r["datasource_id"]): r for r in acquisition["datasource_bibliography"]["source_rows"]}
    _require(ids <= set(sources), "observed source missing from bibliography")
    selected = [sources[i] for i in ids]
    return {
        "database_version": acquisition["BIEN_database_version"],
        "BIEN_R_package_version": acquisition["BIEN_R_package_version"],
        "observed_dataset_ids": sorted(ids), "observed_dataset_count": len(ids),
        "datasets_with_returned_citation": sum(bool(r.get("source_citation")) for r in selected),
        "datasets_with_returned_DOI": sum(bool(r.get("doi")) for r in selected),
        "datasets_with_returned_URL": sum(bool(r.get("source_url")) for r in selected),
        "source_independence": "UNVERIFIED",
    }


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-results-dir", required=True)
    parser.add_argument("--frozen-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prior-diagnostic", default=str(root / "docs/replication/neobat/bien_external_plant_diagnostic_20261121.json"))
    parser.add_argument("--prior-acquisition", default=str(root / "docs/replication/neobat/bien_external_acquisition_receipt_20261121.json"))
    args = parser.parse_args()
    manifest = json.loads((root / "docs/replication/NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json").read_text())
    taxa = tuple(manifest["plant_taxa"])
    roster_sha = hashlib.sha256(("\n".join(taxa) + "\n").encode()).hexdigest()
    _require(roster_sha == FIXED106_SHA256 and tuple(manifest["shadow_fitted_countries"]) == COUNTRIES,
             "fixed manifest changed")
    prior = read_prior(args.prior_diagnostic, PRIOR_RESULT_SHA)
    prior_acquisition = read_prior(args.prior_acquisition, PRIOR_ACQUISITION_SHA)
    new_results, acquisitions, files = {}, {}, {}
    directory = Path(args.new_results_dir)
    for country in NEW_COUNTRIES:
        result_path = directory / f"bien_fixed10_{country}_diagnostic_20261122.json"
        acquisition_path = directory / f"bien_fixed10_{country}_acquisition_20261122.json"
        new_results[country] = json.loads(result_path.read_text())
        acquisitions[country] = json.loads(acquisition_path.read_text())
        _require(set(acquisitions[country]["countries"]) == {country}, "acquisition country scope mismatch")
        _require(new_results[country]["acquisition_receipt_sha256"] == _sha(acquisition_path),
                 "acquisition/result byte provenance mismatch")
        files[country] = {"diagnostic_file": result_path.name, "diagnostic_sha256": _sha(result_path),
                          "acquisition_file": acquisition_path.name, "acquisition_sha256": _sha(acquisition_path)}
    counts, training_source = _original_counts(args.frozen_root)
    combined = combine_results(prior, new_results, taxa, counts)
    for country in COUNTRIES:
        old = country in ("CR", "PA")
        acquisition = prior_acquisition if old else acquisitions[country]
        diagnostic = prior if old else new_results[country]
        combined["countries"][country]["source_metadata"] = _acquisition_check(acquisition, diagnostic, country)
        combined["countries"][country]["input_files"] = (
            {"diagnostic_file": Path(args.prior_diagnostic).name, "diagnostic_sha256": PRIOR_RESULT_SHA,
             "acquisition_file": Path(args.prior_acquisition).name, "acquisition_sha256": PRIOR_ACQUISITION_SHA}
            if old else files[country])
    combined["comparison_frozen_commit"] = EXTENSION_COMMIT
    combined["summarized_at_utc"] = datetime.now(timezone.utc).isoformat()
    combined["summary_script_sha256"] = _sha(__file__)
    combined["original_training_receipt"] = training_source
    combined["raw_locations_or_individual_predictions_written"] = False
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(combined, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": combined["status"], "taxon_country_results_per_mode": 1060,
                      "new_fits_validated": 848, "previous_fits_reused": 212,
                      "mode_status_totals": combined["mode_status_totals"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
