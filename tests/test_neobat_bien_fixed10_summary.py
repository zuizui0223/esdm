"""Panel completeness and descriptive summaries must not select outcomes."""
import copy
import hashlib
import json

import pytest

from scripts.neobat_bien_fixed10_summary import (
    COUNTRIES, NEW_COUNTRIES, MODES, FIXED106_SHA256, FROZEN_COMMIT,
    EXTENSION_COMMIT, country_summary, combine_results, quantiles, read_prior,
)


def blank_country(country, taxa):
    rows = []
    for taxon in taxa:
        modes = {m: {"status": "NO_MATCH_UNKNOWN", "retained_positive_cells": 0,
                     "method_metadata_present": {"estimable_frames": 0, "mean_frame_auc": None},
                     "method_metadata_missing": {"estimable_frames": 0, "mean_frame_auc": None},
                     "frame_results": []} for m in MODES}
        rows.append({"taxon": taxon, "matched_records": 0, "modes": modes})
    return {"country": country, "frames": [], "taxon_results": rows,
            "coverage": {"total_records": 0, "matched_records": 0, "matched_taxa": 0,
                         "survey_frames": 0,
                         "modes": {m: {"eligible_records_before_taxon_training_exclusion": 0,
                                       "sampled_cells_before_taxon_training_exclusion": 0,
                                       "taxon_status_counts": {"NO_MATCH_UNKNOWN": len(taxa)}}
                                   for m in MODES}}}


def result(countries, taxa, original_counts, old=False):
    fits = []
    for c in countries:
        for taxon in taxa:
            pos, bg = original_counts[c, taxon]
            fits.append({"country": c, "taxon": taxon, "train_positive_rows": pos,
                         "train_background_rows": bg, "expected_train_positive_rows": pos,
                         "expected_train_background_rows": bg,
                         "original_training_counts_match": True,
                         "training_cell_membership_matches_original_fit_rows": True})
    return {
        "status": ("EXPLORATORY_BIEN_CR_PA_FIXED106_PLANT_DIAGNOSTIC_COMPLETE" if old else
                   "EXPLORATORY_BIEN_FIXED106_PLANT_DIAGNOSTIC_COMPLETE"),
        "fixed106_taxa_sha256": FIXED106_SHA256,
        "comparison_frozen_commit": "32aa43987b5ac4e2ce4c279504ddcc9732bd0b0c" if old else EXTENSION_COMMIT,
        "execution_commit": "a" * 40, "modes": list(MODES),
        "taxon_country_results_per_mode": len(taxa) * len(countries),
        "model_provenance": {
            "frozen_code_commit": FROZEN_COMMIT, "plant_taxon_count": len(taxa),
            "countries": list(countries), "expected_fit_count": len(fits),
            "completed_fit_count": len(fits), "pinned_package_versions_match": True,
            "training_fits": fits,
        },
        "countries": {c: blank_country(c, taxa) for c in countries},
    }


def panel():
    taxa = tuple(f"Taxon {i:03d}" for i in range(106))
    counts = {(c, t): (20, 40) for c in COUNTRIES for t in taxa}
    old = result(("CR", "PA"), taxa, counts, old=True)
    new = {c: result((c,), taxa, counts) for c in NEW_COUNTRIES}
    return taxa, counts, old, new


def add_contrast(row, auc, frame_id, method="METHOD_METADATA_PRESENT"):
    row["matched_records"] = 1
    for m in MODES:
        mode = row["modes"][m]
        mode["status"] = "EVALUABLE_EXPLORATORY"
        mode["retained_positive_cells"] = 1
        mode["frame_results"].append({"frame_id": frame_id, "method_class": method,
                                      "positive_cells": 1, "background_cells": 5, "auc": auc})
        for key, group in (("method_metadata_present", "METHOD_METADATA_PRESENT"),
                           ("method_metadata_missing", "METHOD_METADATA_MISSING")):
            values = [f["auc"] for f in mode["frame_results"] if f["method_class"] == group]
            mode[key] = {"estimable_frames": len(values),
                         "mean_frame_auc": sum(values) / len(values) if values else None}


def test_quantiles_have_defined_interpolation_and_empty_is_not_zero():
    assert quantiles([]) == {"n": 0, "median": None, "q1": None, "q3": None}
    assert quantiles([0, .5, 1]) == {"n": 3, "median": .5, "q1": .25, "q3": .75}
    assert quantiles([0]) == {"n": 1, "median": 0, "q1": 0, "q3": 0}


def test_country_distribution_weights_taxa_and_keeps_method_classes_separate():
    taxa = ("A", "B", "Unobserved")
    country = blank_country("BR", taxa)
    add_contrast(country["taxon_results"][0], .4, "F1")
    add_contrast(country["taxon_results"][0], .8, "F2")
    add_contrast(country["taxon_results"][1], .2, "F1")
    add_contrast(country["taxon_results"][1], 1, "F3", "METHOD_METADATA_MISSING")
    country["coverage"]["matched_taxa"] = country["coverage"]["matched_records"] = 2
    country["coverage"]["total_records"] = 10
    for m in MODES:
        country["coverage"]["modes"][m]["taxon_status_counts"] = {
            "EVALUABLE_EXPLORATORY": 2, "NO_MATCH_UNKNOWN": 1}
    summary = country_summary(country, taxa)
    for m in MODES:
        s = summary["modes"][m]
        assert s["method_metadata_present"]["taxon_mean_auc"]["n"] == 2
        assert s["method_metadata_present"]["taxon_mean_auc"]["median"] == pytest.approx(.4)
        assert s["method_metadata_missing"]["taxon_mean_auc"]["median"] == 1
        assert s["estimable_taxon_frame_contrasts"] == 4
        assert s["taxon_status_counts"]["NO_MATCH_UNKNOWN"] == 1


def test_complete_empty_panel_keeps_all_1060_pairs_and_null_metrics():
    taxa, counts, old, new = panel()
    combined = combine_results(old, new, taxa, counts)
    assert combined["taxon_country_results_per_mode"] == 1060
    assert combined["new_fits_validated"] == 848
    assert combined["previous_fits_reused"] == 212
    for m in MODES:
        assert combined["mode_status_totals"][m]["NO_MATCH_UNKNOWN"] == 1060
        for c in COUNTRIES:
            assert combined["countries"][c]["modes"][m]["method_metadata_present"]["taxon_mean_auc"]["median"] is None
    assert combined["countries"]["CR"]["evidence_stage"] == "PREVIOUSLY_OPENED_CR_PA"
    assert combined["countries"]["BR"]["evidence_stage"] == "NEW_PRELISTED_COUNTRY"


def test_missing_country_and_duplicate_taxon_cannot_shrink_denominator():
    taxa, counts, old, new = panel()
    missing = dict(new)
    missing.pop("SV")
    with pytest.raises(ValueError, match="eight"):
        combine_results(old, missing, taxa, counts)
    duplicated = copy.deepcopy(new)
    duplicated["BR"]["countries"]["BR"]["taxon_results"][-1] = copy.deepcopy(
        duplicated["BR"]["countries"]["BR"]["taxon_results"][0])
    with pytest.raises(ValueError, match="taxon universe"):
        combine_results(old, duplicated, taxa, counts)


def test_training_counts_checked_against_original_not_just_copied_flags():
    taxa, counts, old, new = panel()
    fit = new["BR"]["model_provenance"]["training_fits"][0]
    fit["train_positive_rows"] = fit["expected_train_positive_rows"] = 999
    with pytest.raises(ValueError, match="original training counts"):
        combine_results(old, new, taxa, counts)


def test_wrong_country_or_comparison_commit_is_not_accepted():
    taxa, counts, old, new = panel()
    bad = copy.deepcopy(new)
    bad["BR"]["countries"] = {"EC": bad["BR"]["countries"].pop("BR")}
    with pytest.raises(ValueError, match="country scope"):
        combine_results(old, bad, taxa, counts)
    new["BR"]["comparison_frozen_commit"] = "b" * 40
    with pytest.raises(ValueError, match="comparison commit"):
        combine_results(old, new, taxa, counts)


def test_prior_receipt_bytes_cannot_be_rewritten(tmp_path):
    path = tmp_path / "changed.json"
    path.write_text('{"status":"pretend"}')
    with pytest.raises(ValueError, match="prior receipt SHA"):
        read_prior(path, "fa8342ab203152b8ec347653961612142b19a9e44ca20864904b540e7ed1f788")


def test_inconsistent_stored_mean_is_rejected_and_extra_raw_fields_not_copied():
    data = blank_country("BR", ("Focal",))
    add_contrast(data["taxon_results"][0], .8, "F1")
    data["coverage"]["matched_records"] = data["coverage"]["matched_taxa"] = 1
    for m in MODES:
        data["coverage"]["modes"][m]["taxon_status_counts"] = {"EVALUABLE_EXPLORATORY": 1}
    data["latitude"] = 12.3456789
    data["plot_name"] = "PRIVATE_SITE"
    summary = country_summary(data, ("Focal",))
    text = json.dumps(summary)
    assert "PRIVATE_SITE" not in text and "12.3456789" not in text
    data["taxon_results"][0]["modes"][MODES[0]]["method_metadata_present"]["mean_frame_auc"] = .1
    with pytest.raises(ValueError, match="frame mean"):
        country_summary(data, ("Focal",))
