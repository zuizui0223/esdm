"""Synthetic-only tests: no access to source wildlife response or Actions ZIP."""
from __future__ import annotations

import copy
from itertools import combinations

import pytest

from scripts.safari14_fm_source_pool_contrast import (
    REPORTED_ECOLOGICAL_LINKS, SPLITS, summarize, validate_partition,
)


def _rows(parks, obs=0.5, null=0.1):
    return [dict(project_1=a, project_2=b,
                 original_observed_sim_median=obs,
                 null_sim_median=null,
                 median_sim_excess_vs_null=obs-null,
                 null_pair_draws_estimable=500)
            for a, b in combinations(parks, 2)]


def test_park_leave_one_out_reaggregation_is_not_original_draw_statistic():
    parks = ("A", "B", "C", "D")
    rows = _rows(parks)
    rows[0].update(original_observed_sim_median=0.06,
                   null_sim_median=0.1, median_sim_excess_vs_null=-0.04)
    result = summarize(rows, parks)
    assert result["pair_count"] == 6
    assert result["positive_pair_count"] == 5
    assert result["negative_pair_count"] == 1
    assert result["median_of_pair_level_excess"] == pytest.approx(0.4)
    assert len(result["leave_one_park_out"]) == 4
    assert all(x["remaining_pairs"] == 3 for x in result["leave_one_park_out"])
    assert result["leave_one_park_positive_count"] == 4


def test_retroactively_named_landscape_links_calculate_without_sign_filtering():
    parks = ("A", "B", "C", "D")
    rows = _rows(parks)
    rows[0].update(original_observed_sim_median=0.0,
                   null_sim_median=0.1, median_sim_excess_vs_null=-0.1)
    r = summarize(rows, parks, linked={("A", "B"): "hypothetical shared biome"})
    match = r["retrospective_named_landscape_links"]
    assert match["status"] == "POST_OUTCOME_EXPLORATORY_NOT_CONFIRMED"
    assert match["matched_median_excess"] == pytest.approx(-0.1)
    assert match["matched_pairs"][0]["low_excess_rank_among_all_pairs"] == 1
    assert match["unmatched_median_excess"] == pytest.approx(0.4)
    assert match["matched_minus_unmatched_median_excess"] == pytest.approx(-0.5)


@pytest.mark.parametrize("damage", ["duplicate", "missing", "bad_value", "wrong_difference", "wrong_support"])
def test_frozen_pair_universe_and_arithmetic_refuse_corrupt_inputs(damage):
    parks = ("A", "B", "C", "D")
    rows = _rows(parks)
    if damage == "duplicate": rows[1] = copy.deepcopy(rows[0])
    elif damage == "missing": rows.pop()
    elif damage == "bad_value": rows[0]["null_sim_median"] = float("nan")
    elif damage == "wrong_difference": rows[0]["median_sim_excess_vs_null"] = 0.5
    else: rows[0]["null_pair_draws_estimable"] = 499
    with pytest.raises(ValueError):
        validate_partition(rows, parks)


def test_pinned_park_sets_and_retrospective_source_descriptions_are_explicit():
    assert len(SPLITS["discovery"]) == 7
    assert len(SPLITS["validation"]) == 5
    assert set(REPORTED_ECOLOGICAL_LINKS) == {
        ("APN", "KRU"), ("CDB", "KAR"), ("KGA", "LEC")}
