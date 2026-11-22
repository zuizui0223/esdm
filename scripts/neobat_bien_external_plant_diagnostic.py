"""Aggregate-only BIEN diagnostic for the frozen climate-only plants.

The pure grouping/metric functions intentionally need no numerical libraries.
Raw records, cell identifiers and individual scores remain private in memory.
See the committed comparison specification for interpretation and exclusions.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys


COUNTRIES = ("CR", "PA")
ALLOWED_COUNTRIES = ("BR", "CR", "EC", "GF", "GT", "HN", "NI", "PA", "PE", "SV")
MODES = ("primary_2000_2025", "known_precision_2000_2025", "historical_undated_descriptive")
FIXED106_SHA256 = "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
COMPARISON_COMMIT = "32aa43987b5ac4e2ce4c279504ddcc9732bd0b0c"
SPEC_PATH = "docs/replication/NEOBAT_BIEN_EXTERNAL_PLANT_DIAGNOSTIC_FROZEN_20261121.md"
METHOD_FIELDS = ("sampling_protocol", "methodology_reference", "methodology_description")
INCLUSION_FIELDS = (
    "growth_forms_included_all", "growth_forms_included_trees",
    "growth_forms_included_shrubs", "growth_forms_included_lianas",
    "growth_forms_included_herbs", "growth_forms_included_epiphytes",
    "growth_forms_included_notes", "taxa_included_all",
    "taxa_included_seed_plants", "taxa_included_ferns_lycophytes",
    "taxa_included_bryophytes", "taxa_included_exclusions",
)
FRAME_FIELDS = ("datasource_id", "datasource", "dataset", *METHOD_FIELDS,
                "plot_area_ha", *INCLUSION_FIELDS)


def _clean(value):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return format(value, ".15g")
    text = " ".join(str(value).split())
    return "" if text.lower() in {"na", "n/a", "null", "nan"} else text


def _year(value):
    match = re.match(r"^(\d{4})(?:$|-\d{1,2}(?:-|$)|[T ])", _clean(value))
    if not match:
        return None
    year = int(match.group(1))
    return year if 1000 <= year <= 9999 else None


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PreparedRecord:
    taxon: str
    cell: tuple[int, int] | None
    year: int | None
    precision: float | None
    precision_state: str
    frame: tuple[str, ...]


def prepare_records(rows, project):
    """Normalize full-country rows; project(lon,lat) returns a private grid cell."""
    prepared = []
    for row in rows:
        taxon = _clean(row.get("scrubbed_species_binomial"))
        lon, lat = _number(row.get("longitude")), _number(row.get("latitude"))
        cell = None
        if lon is not None and lat is not None and -180 <= lon <= 180 and -90 <= lat <= 90:
            try:
                value = project(lon, lat)
                if len(value) != 2 or any(not isinstance(i, int) or isinstance(i, bool) for i in value):
                    raise ValueError("projector must return two grid integers")
                cell = tuple(value)
            except (ValueError, OverflowError):
                cell = None
        precision_text = _clean(row.get("coord_uncertainty_m"))
        precision = _number(row.get("coord_uncertainty_m"))
        if not precision_text:
            precision_state = "unknown"
        elif precision is None or precision < 0:
            precision_state = "invalid"
        else:
            precision_state = "known"
        prepared.append(PreparedRecord(
            taxon, cell, _year(row.get("date_collected")), precision,
            precision_state, tuple(_clean(row.get(k)) for k in FRAME_FIELDS),
        ))
    return tuple(prepared)


def _eligible(record, mode):
    if record.cell is None or record.precision_state == "invalid":
        return False
    if record.precision_state == "known" and record.precision > 12500:
        return False
    if mode == "known_precision_2000_2025" and record.precision_state != "known":
        return False
    if mode == "historical_undated_descriptive":
        return record.year is None or record.year <= 2025
    return record.year is not None and 2000 <= record.year <= 2025


def pairwise_auc(positive_scores, background_scores):
    """Exact within-frame pair concordance; ties count one half."""
    positive_scores, background_scores = list(positive_scores), list(background_scores)
    if any(not math.isfinite(x) for x in positive_scores + background_scores):
        raise ValueError("AUC inputs must be finite")
    if not positive_scores or not background_scores:
        return None
    background_scores.sort()
    agreement = math.fsum(
        bisect_left(background_scores, x)
        + .5 * (bisect_right(background_scores, x) - bisect_left(background_scores, x))
        for x in positive_scores
    )
    return agreement / (len(positive_scores) * len(background_scores))


def _public_frame(key, frame_id):
    values = dict(zip(FRAME_FIELDS, key))
    method_present = any(values[k] for k in METHOD_FIELDS)
    # Free-text methods/inclusion notes can contain locations or contacts.
    # Preserve distinction through hashes without exporting their text.
    return {
        "frame_id": frame_id,
        "datasource_id": values["datasource_id"],
        "datasource": values["datasource"], "dataset": values["dataset"],
        "plot_area_ha": _number(values["plot_area_ha"]),
        "method_class": "METHOD_METADATA_PRESENT" if method_present else "METHOD_METADATA_MISSING",
        "method_fields": {k: {"present": bool(values[k]),
                               "sha256": _digest(values[k]) if values[k] else None}
                          for k in METHOD_FIELDS},
        "inclusion_metadata": {
            k: (values[k].lower() if values[k].lower() in {"true", "false", "0", "1", "t", "f"}
                else {"present": bool(values[k]), "sha256": _digest(values[k]) if values[k] else None})
            for k in INCLUSION_FIELDS
        },
        "frame_metadata_sha256": _digest(json.dumps(key, ensure_ascii=False)),
        "equal_metadata_proves_equal_effort": False,
    }


def _mean_summary(frame_results, method_class):
    values = [r["auc"] for r in frame_results
              if r["method_class"] == method_class and r["auc"] is not None]
    return {"estimable_frames": len(values),
            "mean_frame_auc": math.fsum(values) / len(values) if values else None,
            "weighting": "equal_weight_per_estimable_frame_descriptive_only"}


def evaluate_country(country, taxa, records, predictions, training_cells):
    """Return only aggregates for every taxon and every precommitted mode.

    predictions is the private cell -> taxon -> score mapping; training_cells
    is taxon -> exact original fit-cell union. Missing cell predictions denote
    raster invalidity. Missing taxon predictions are an integrity error.
    """
    taxa = tuple(taxa)
    if country not in ALLOWED_COUNTRIES or len(taxa) != len(set(taxa)):
        raise ValueError("invalid country or duplicate taxa")
    if any(taxon not in training_cells for taxon in taxa):
        raise ValueError("missing taxon training membership")
    for scores in predictions.values():
        if any(taxon not in scores for taxon in taxa):
            raise ValueError("missing prediction taxon")
        if any(not math.isfinite(scores[taxon]) for taxon in taxa):
            raise ValueError("prediction scores must be finite")
    keys = sorted({r.frame for r in records})
    frames = {key: _public_frame(key, f"{country}_F{i:03d}")
              for i, key in enumerate(keys, 1)}
    by_taxon = defaultdict(list)
    for record in records:
        by_taxon[record.taxon].append(record)
    eligible = {mode: defaultdict(list) for mode in MODES}
    for mode in MODES:
        for record in records:
            if _eligible(record, mode):
                eligible[mode][record.frame].append(record)
    coverage = {
        "total_records": len(records), "survey_frames": len(frames),
        "matched_taxa": sum(bool(by_taxon[t]) for t in taxa),
        "matched_records": sum(len(by_taxon[t]) for t in taxa),
        "records_missing_datasource_id": sum(not r.frame[0] for r in records),
        "records_missing_species_name": sum(not r.taxon for r in records),
        "records_invalid_coordinates": sum(r.cell is None for r in records),
        "records_unknown_year": sum(r.year is None for r in records),
        "records_before_2000": sum(r.year is not None and r.year < 2000 for r in records),
        "records_after_2025": sum(r.year is not None and r.year > 2025 for r in records),
        "records_unknown_precision": sum(r.precision_state == "unknown" for r in records),
        "records_invalid_precision": sum(r.precision_state == "invalid" for r in records),
        "records_known_precision_above_12500m": sum(r.precision_state == "known" and r.precision > 12500 for r in records),
        "modes": {},
    }
    for mode in MODES:
        rows = [r for values in eligible[mode].values() for r in values]
        coverage["modes"][mode] = {
            "eligible_records_before_taxon_training_exclusion": len(rows),
            "sampled_cells_before_taxon_training_exclusion": len({r.cell for r in rows}),
            "records_unknown_precision": sum(r.precision_state == "unknown" for r in rows),
        }
    taxon_results = []
    valid_cells = set(predictions)
    for taxon in taxa:
        focal = by_taxon[taxon]
        all_known_positive = {r.cell for r in focal if r.cell is not None}
        focal_frames = sorted({r.frame for r in focal})
        training = set(training_cells[taxon])
        taxon_result = {"taxon": taxon, "matched_records": len(focal), "modes": {}}
        for mode in MODES:
            frame_results, retained_positive = [], set()
            for key in focal_frames:
                rows = eligible[mode].get(key, ())
                sampled = {r.cell for r in rows}
                pos_before = {r.cell for r in rows if r.taxon == taxon}
                bg_before = sampled - all_known_positive
                pos_not_train, bg_not_train = pos_before - training, bg_before - training
                positive, background = pos_not_train & valid_cells, bg_not_train & valid_cells
                retained_positive.update(positive)
                auc = pairwise_auc([predictions[c][taxon] for c in positive],
                                   [predictions[c][taxon] for c in background])
                frame_results.append({
                    "frame_id": frames[key]["frame_id"],
                    "method_class": frames[key]["method_class"],
                    "positive_cells_before_training_and_raster_exclusion": len(pos_before),
                    "background_cells_before_training_and_raster_exclusion": len(bg_before),
                    "known_positive_background_exclusions": len(sampled & all_known_positive),
                    "positive_training_overlap_excluded": len(pos_before & training),
                    "background_training_overlap_excluded": len(bg_before & training),
                    "positive_raster_invalid_excluded": len(pos_not_train - valid_cells),
                    "background_raster_invalid_excluded": len(bg_not_train - valid_cells),
                    "positive_cells": len(positive), "background_cells": len(background),
                    "auc": auc,
                    "status": ("EVALUABLE_EXPLORATORY" if auc is not None else
                               "NO_POSITIVE_CELLS" if not positive else "NO_BACKGROUND_CELLS"),
                })
            status = ("NO_MATCH_UNKNOWN" if not focal else
                      "NO_ELIGIBLE_POSITIVE_CELLS" if not retained_positive else
                      "EVALUABLE_EXPLORATORY" if any(r["auc"] is not None for r in frame_results)
                      else "NO_WITHIN_FRAME_COMPARISON")
            taxon_result["modes"][mode] = {
                "status": status,
                "retained_positive_cells": len(retained_positive),
                "eligible_positive_records_unknown_precision": sum(
                    _eligible(r, mode) and r.precision_state == "unknown" for r in focal),
                "method_metadata_present": _mean_summary(frame_results, "METHOD_METADATA_PRESENT"),
                "method_metadata_missing": _mean_summary(frame_results, "METHOD_METADATA_MISSING"),
                "frame_results": frame_results,
            }
        taxon_results.append(taxon_result)
    for mode in MODES:
        statuses = Counter(r["modes"][mode]["status"] for r in taxon_results)
        coverage["modes"][mode]["taxon_status_counts"] = dict(sorted(statuses.items()))
        coverage["modes"][mode]["taxa_with_estimable_method_metadata_present_frames"] = sum(
            r["modes"][mode]["method_metadata_present"]["estimable_frames"] > 0 for r in taxon_results)
        coverage["modes"][mode]["taxa_with_estimable_method_metadata_missing_frames"] = sum(
            r["modes"][mode]["method_metadata_missing"]["estimable_frames"] > 0 for r in taxon_results)
    return {"country": country, "coverage": coverage,
            "frames": list(frames.values()), "taxon_results": taxon_results}


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-records", required=True)
    parser.add_argument("--acquisition-receipt", required=True)
    parser.add_argument("--frozen-root", required=True)
    parser.add_argument("--plant-archive", required=True)
    parser.add_argument("--raster-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--countries", default=",".join(COUNTRIES),
                        help="Comma-separated subset of the fixed ten countries; default CR,PA")
    parser.add_argument("--comparison-specification", default=SPEC_PATH)
    parser.add_argument("--comparison-commit", default=COMPARISON_COMMIT)
    parser.add_argument("--compact-json", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from scripts.neobat_bien_frozen_plant_adapter import FixedPlantComponent, validate_countries
    countries = validate_countries(country.strip() for country in args.countries.split(","))
    from pyproj import Transformer
    manifest = _read(root / "docs/replication/NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json")
    taxa = tuple(manifest["plant_taxa"])
    if (len(taxa) != 106 or len(set(taxa)) != 106 or
            manifest["source_fixed106_sha256"] != FIXED106_SHA256 or
            tuple(manifest["shadow_fitted_countries"]) != ALLOWED_COUNTRIES):
        raise RuntimeError("FIXED_106_MANIFEST_DRIFT")
    receipt = _read(args.acquisition_receipt)
    private = _read(args.private_records)
    if (not isinstance(receipt, dict) or not isinstance(private, dict) or
            receipt.get("status") != "BIEN_EXTERNAL_ACQUISITION_COMPLETE" or
            receipt.get("fixed106_taxa_sha256") != FIXED106_SHA256 or
            not isinstance(receipt.get("countries"), dict) or
            not isinstance(private.get("countries"), dict) or
            set(receipt["countries"]) != set(countries) or
            set(private["countries"]) != set(countries)):
        raise RuntimeError("BIEN_ACQUISITION_RECEIPT_INVALID")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)

    def project(lon, lat):
        x, y = transformer.transform(lon, lat)
        return math.floor(x / 25000), math.floor(y / 25000)

    results = {}
    with FixedPlantComponent(args.frozen_root, args.plant_archive, args.raster_dir,
                             countries=countries) as component:
        if tuple(component.taxa) != taxa:
            raise RuntimeError("FROZEN_ADAPTER_TAXA_ORDER_MISMATCH")
        for country in countries:
            rows = private["countries"][country]
            expected = receipt["countries"][country]
            if len(rows) != expected["total_rows"]:
                raise RuntimeError("BIEN_ACQUISITION_ROW_COUNT_MISMATCH")
            records = prepare_records(rows, project)
            matched_taxa = len({r.taxon for r in records}.intersection(taxa))
            if matched_taxa != expected["matched_taxa"]:
                raise RuntimeError("BIEN_ACQUISITION_MATCH_COUNT_MISMATCH")
            cells = {r.cell for r in records if r.cell is not None}
            predictions, invalid_cells = component.predict(country, cells)
            if set(predictions) | set(invalid_cells) != cells or set(predictions) & set(invalid_cells):
                raise RuntimeError("BIEN_PREDICTION_CELL_ACCOUNTING_MISMATCH")
            training = {taxon: component.training_cells(country, taxon) for taxon in taxa}
            results[country] = evaluate_country(country, taxa, records, predictions, training)
        model_provenance = component.provenance()
    if not model_provenance["pinned_package_versions_match"]:
        raise RuntimeError("FROZEN_NUMERICAL_PACKAGE_VERSION_MISMATCH")
    output = {
        "schema_version": 1,
        "status": ("EXPLORATORY_BIEN_CR_PA_FIXED106_PLANT_DIAGNOSTIC_COMPLETE"
                   if set(countries) == set(COUNTRIES)
                   else "EXPLORATORY_BIEN_FIXED106_PLANT_DIAGNOSTIC_COMPLETE"),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_commit": os.environ.get("GITHUB_SHA"),
        "comparison_frozen_commit": args.comparison_commit,
        "comparison_specification": args.comparison_specification,
        "comparison_specification_sha256": _file_sha(root / args.comparison_specification),
        "script_sha256": _file_sha(__file__),
        "acquisition_receipt_sha256": _file_sha(args.acquisition_receipt),
        "private_input_sha256": _file_sha(args.private_records),
        "fixed106_taxa_sha256": FIXED106_SHA256,
        "taxon_country_results_per_mode": sum(len(r["taxon_results"]) for r in results.values()),
        "modes": list(MODES), "model_provenance": model_provenance,
        "interpretation": {
            "independent_source_validation_established": False,
            "ecological_M3_estimated": False,
            "bat_prediction_improvement_estimated": False,
            "background_means_absence": False,
            "scores_are_calibrated_occupancy": False,
            "method_metadata_proves_homogeneous_effort": False,
            "frames_are_independent_replicates": False,
            "taxon_without_matching_record_means_absent": False,
            "claims": "exploratory within-source-frame geographic transfer of the frozen climate-only plant component",
            "date_mode_priority": "primary_2000_2025; other modes remain separate even if primary is non-estimable",
        },
        "privacy": {"raw_coordinates_written": False, "plot_or_cell_identifiers_written": False,
                    "individual_predictions_written": False, "raw_tables_written_to_public_output": False},
        "countries": results,
    }
    if output["taxon_country_results_per_mode"] != 106 * len(countries):
        raise RuntimeError("FIXED_REQUESTED_COUNTRY_RESULT_DENOMINATOR_CHANGED")
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=None if args.compact_json else 2,
                               separators=(",", ":") if args.compact_json else None,
                               ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"],
                      "taxon_country_results_per_mode": output["taxon_country_results_per_mode"],
                      "countries": {c: results[c]["coverage"] for c in countries}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
