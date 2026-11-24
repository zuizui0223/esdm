"""Check persisted original Yasuní field result and two-site source reconciliation."""
import json
from pathlib import Path


def _file(name):
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "docs/replication/neobat" / name).read_text(encoding="utf-8"))


def test_preserved_original_author_source_counts_not_pseudoreplicated():
    y = _file("yasuni_seed_portfolio_original_result_20261124.json")
    assert y["status"] == "YASUNI_ORIGINAL_SEED_FALL_AND_SOURCELINK_PORTFOLIO_COMPLETE"
    assert y["source"]["YASUNI_original_git_blob"] == "11cafba9ae138605fdd79cea7a31bc4821d869ee"
    assert y["source"]["taxon_bridge_original_git_blob"] == "d9e017afc326059d5feb8f89e4a17bd079f52301"
    s = y["sampling"]
    assert s["source_records"] == s["source_taxon_codes"] * s["timepoints"] == 298282
    assert s["matched_numeric_values"] == s["matched_zero_values"] + s["matched_positive_values"] == 2830
    assert s["matched_zero_values"] == 1909
    assert s["matched_explicit_missing_values"] == s["matched_omitted_code_timepoints"] == 0
    assert len(s["matched"]) == 10
    assert len(y["all_26_source_bat_portfolios"]) == 26
    assert sum(p["eligible"] for p in y["all_26_source_bat_portfolios"]) == 6
    assert sum(p["eligible"] and p["CV_ratio"] > 1
               for p in y["all_26_source_bat_portfolios"]) == 4
    assert y["interpretation"]["bat_outcomes_and_M3_M1_N1_not_estimated"]


def test_saved_26_bat_reconciliation_uses_only_source_ids_and_nulls():
    c = _file("cc1_original_seed_portfolio_result_20261124.json")
    y = _file("yasuni_seed_portfolio_original_result_20261124.json")
    x = _file("cc1_yasuni_26bat_descriptive_crosssite_20261124.json")
    assert len(x["all_candidate_bats"]) == x["original_bat_candidate_denominator"] == 26
    assert [p["bat"] for p in x["all_candidate_bats"]] == [
        p["bat"] for p in c["portfolios"]["per_candidate_bat"]]
    assert [p["bat"] for p in x["all_candidate_bats"]] == [
        p["bat"] for p in y["all_26_source_bat_portfolios"]]
    eligible_both = []
    for row, cc, ys in zip(
        x["all_candidate_bats"], c["portfolios"]["per_candidate_bat"],
        y["all_26_source_bat_portfolios"]):
        assert row["CC1"]["eligible"] == cc["eligible"]
        assert row["YASUNI"]["eligible"] == ys["eligible"]
        assert row["CC1"]["observed_cv_over_shift_null"] == cc["CV_ratio"]
        assert row["YASUNI"]["observed_cv_over_shift_null"] == ys["CV_ratio"]
        if cc["eligible"] and ys["eligible"]:
            eligible_both.append(row["bat"])
            assert row["CC1"]["plant_names"] != row["YASUNI"]["plant_names"]
    assert eligible_both == x["both_sites_evaluable_candidate_names"]
    assert len(eligible_both) == 4
    assert x["both_site_identical_source_plant_sets"] == 0
    assert x["limits"]["two_sites_same_original_paper_not_independent_studies"]
    assert x["limits"]["source_network_not_locally_verified_in_either_site"]
