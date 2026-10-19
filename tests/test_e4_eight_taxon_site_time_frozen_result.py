"""Frozen descriptive all-pair result regression checks; zero biological row access."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs" / "replication"


def _read(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def test_one_successful_result_has_pinned_source_artifact_and_fixed_design():
    d = _read("E4_EIGHT_TAXON_SITE_TIME_RESULT_RECEIPT.json")
    p = d["provenance"]
    assert p["workflow_run_id"] == 39208596309
    assert p["workflow_head_sha"] == "4ddc66e7b1367003d884554a78bf6fde49922565"
    assert p["workflow_attempt"] == 1 and p["workflow_conclusion"] == "success"
    assert p["unit_tests_passed_before_response"] == 7
    assert p["artifact_id"] == 12167010654
    assert p["artifact_zip_sha256"] == (
        "bbbdf19749f1551f5105f8d4ae7cbddb68cc88dd3e08f65ae0dc65f921190748"
    )
    assert p["original_mica_archive_sha256"] == (
        "8346f3fe467a201525d6bedd4ebd6e2078457ee8bb778501d41d55ace7d962c9"
    )
    assert d["cohort_geometry"]["fixed_taxa"] == 8
    assert d["cohort_geometry"]["fixed_taxon_pairs"] == 28
    assert d["eligibility"]["min_independent_physical_sites"] == 3
    assert d["eligibility"]["min_informative_site_time_tables"] == 4
    assert d["eligibility"]["min_distinct_time_bins"] == 2
    assert d["eligibility"]["pseudocounts_used"] is False


def test_all_28_unordered_pairs_remain_in_each_csv_time_control():
    with (BASE / "E4_EIGHT_TAXON_SITE_TIME_ALL_PAIRS.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 56
    group = {mode: [r for r in rows if r["mode"] == mode]
             for mode in ("site_season", "site_yearmonth")}
    assert all(len(group[k]) == 28 for k in group)
    assert {tuple(sorted([r["species1"], r["species2"]])) for r in group["site_season"]} == {
        tuple(sorted([r["species1"], r["species2"]])) for r in group["site_yearmonth"]
    }
    assert len({(r["species1"], r["species2"]) for r in group["site_season"]}) == 28
    d = _read("E4_EIGHT_TAXON_SITE_TIME_RESULT_RECEIPT.json")
    for mode, label in [("site_season", "primary_site_season"),
                        ("site_yearmonth", "sensitivity_site_yearmonth")]:
        part = d[label]
        subset = group[mode]
        comparable = [r for r in subset if r["east_train_ratio"] != ""]
        assert len(comparable) == part["comparable_pairs"]
        assert sum(int(r["reversal"]) for r in subset) == part["observed_pairwise_reversals"]
        assert sum(int(r["LOO_robust"]) for r in subset) == part["leave_one_site_stable_reversals"]
        assert all(r["east_train_ratio"] == "" for r in subset if not r["train_odds"] or not r["east_odds"])
        for row in comparable:
            assert math.isclose(float(row["east_train_ratio"]),
                                float(row["east_odds"]) / float(row["train_odds"]),
                                rel_tol=1e-6)


def test_rodent_reversal_survives_both_site_time_controls():
    d = _read("E4_EIGHT_TAXON_SITE_TIME_RESULT_RECEIPT.json")
    season = d["primary_site_season"]["rat_vs_muskrat"]
    month = d["sensitivity_site_yearmonth"]["rat_vs_muskrat"]
    assert season["informative_sites_training"] == 16
    assert season["informative_sites_heldout"] == 8
    assert month["informative_sites_training"] == 14
    assert month["informative_sites_D"] == 8
    assert season["LOO_robust"] and month["LOO_robust"]
    assert season["training_odds"] < 1 < season["heldout_D_odds"]
    assert month["training_odds"] < 1 < month["heldout_D_odds"]
    assert math.isclose(season["D_over_train_ratio"], 6.734949770657086)
    assert math.isclose(month["D_over_train_ratio"], 9.72464334666708)


def test_waterbird_reversal_is_only_season_leave_one_site_stable():
    d = _read("E4_EIGHT_TAXON_SITE_TIME_RESULT_RECEIPT.json")
    season = d["primary_site_season"]
    month = d["sensitivity_site_yearmonth"]
    assert season["leave_one_site_stable_reversals"] == 2
    assert month["leave_one_site_stable_reversals"] == 1
    birds = next(x for x in season["leave_one_site_stable_pair_species_1_vs_species_2"]
                 if x["species_1"] == "Fulica atra")
    assert birds["species_2"] == "Gallinula chloropus"
    assert birds["train_LOO_range"][0] > 1 > birds["D_LOO_range"][1]
    assert "fails single-location deletion robustness" in month["waterbird_pair_note"]


def test_no_claim_upgrade_or_deletion_of_unsupported_pairs():
    r = _read("E4_EIGHT_TAXON_SITE_TIME_RESULT_RECEIPT.json")
    b = r["inferential_bounds"]
    assert b["all_28_pairs_reported_for_both_controls"] is True
    assert b["taxon_roster_and_rat_pair_selected_after_earlier_outcomes"] is True
    assert b["event_level_CI_or_pvalues_computed"] is False
    assert b["independent_known_passage_denominator_available"] is False
    assert b["species_specific_detection_calibrated"] is False
    assert b["site_source_geography_fully_crossed"] is False
    assert b["original_E4_fit_rerun"] is False
    assert b["original_E5_qualified_candidates"] == 0
    assert b["original_E5_G4_passed"] is False
    statement = (BASE / "E4_EIGHT_TAXON_SITE_TIME_STUDY.md").read_text(encoding="utf-8")
    assert "15/28" in statement
    assert "12/28" in statement
    assert "not a" in statement.lower() or "not " in statement.lower()
