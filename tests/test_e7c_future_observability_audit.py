"""Support-bound calculation regression tests, without any biological-row read."""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
import math

import pytest

from scripts.e7c_future_observability_audit import (
    E7C_STATUS, MIN_CAMERA_YEARS, MIN_CAMERAS, MIN_COLLECTION_FOLDERS,
    PINNED_SOURCE_SHA256, evaluate, shortfalls, toy_complete_probability,
    expected_per_cell_for_probability,
)


def toy_result():
    taxa=sorted(("buffalo","elephant","gazelleGrants","gazelleThomsons",
                 "giraffe","hartebeest","hyenaSpotted","lion","reedbuck",
                 "warthog","wildebeest","zebra"))
    all_pairs=[{
        "species_1":a,"species_2":b,
        "eligible_matched_site_years":0,"eligible_distinct_cameras":0,
        "original_source_folders":0,"status":"INSUFFICIENT_DIRECT_CELL_SUPPORT"
    } for a,b in combinations(taxa,2)]
    base={
        "all_66_pairs_including_support_refusals":all_pairs,
        "estimable_pairs":0,
        "species_complete_site_year_counts":{t:0 for t in taxa},
    }
    return {
        "status":E7C_STATUS,"original_frozen_taxa":taxa,
        "discovery":deepcopy(base),"validation":deepcopy(base),
        "cross_period":{"both_estimable_pairs":0},
    }


def test_exact_gate_and_just_one_missing_camera_year():
    assert (MIN_CAMERA_YEARS,MIN_CAMERAS,MIN_COLLECTION_FOLDERS)==(10,5,3)
    row={"eligible_matched_site_years":9,"eligible_distinct_cameras":9,
         "original_source_folders":4,"status":"INSUFFICIENT_DIRECT_CELL_SUPPORT"}
    a=shortfalls(row)
    assert a["missing_complete_camera_years"]==1
    assert a["missing_distinct_camera_sites"]==0
    assert a["missing_original_collection_folders"]==0
    assert a["hypothetical_future_minimum_extra_fully_observed_camera_years"]==1
    row.update(eligible_matched_site_years=10,status="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE")
    assert shortfalls(row)["original_estimable"] is True


def test_invalid_status_and_impossible_distinct_camera_count_are_rejected():
    row={"eligible_matched_site_years":5,"eligible_distinct_cameras":6,
         "original_source_folders":4,"status":"INSUFFICIENT_DIRECT_CELL_SUPPORT"}
    with pytest.raises(ValueError,match="impossible"):
        shortfalls(row)
    row.update(eligible_matched_site_years=9,eligible_distinct_cameras=5,
               status="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE")
    with pytest.raises(ValueError,match="gate/status"):
        shortfalls(row)


def test_eight_cell_sampling_probability_is_only_a_poisson_thought_experiment():
    assert math.isclose(toy_complete_probability(1),0.02549173076596687)
    assert math.isclose(toy_complete_probability(2),0.3124509872361312)
    assert math.isclose(toy_complete_probability(4),0.8625315296687566)
    lam=expected_per_cell_for_probability(0.8)
    assert math.isclose(lam,3.59329558325999)
    assert math.isclose(toy_complete_probability(lam),0.8)
    with pytest.raises(ValueError):toy_complete_probability(-1)
    with pytest.raises(ValueError):expected_per_cell_for_probability(1)


def test_all_66_pairs_and_all_original_refusals_are_kept():
    result=evaluate(toy_result())
    assert result["status"]=="E7C_FROZEN_AGGREGATE_FUTURE_OBSERVABILITY_AUDIT"
    assert result["pairs_estimable_in_both_original_partitions"]==0
    for part in ("discovery","validation"):
        a=result["periods"][part]
        assert a["pair_universe"]==66
        assert a["pair_count_by_complete_camera_year"]["0"]==66
    assert len(result["all_66_pair_support_and_future_shortfalls"])==66
    assert result["interpretation_boundary"]["cannot_add_source_folders_or_observations_to_original_frozen_E7C_partitions"] is True


def test_pair_universe_or_status_tampering_cannot_be_silently_repaired():
    x=toy_result()
    x["discovery"]["all_66_pairs_including_support_refusals"].pop()
    with pytest.raises(ValueError,match="66-pair"):
        evaluate(x)
    x=toy_result()
    x["validation"]["all_66_pairs_including_support_refusals"][0]["status"]="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE"
    with pytest.raises(ValueError,match="gate/status"):
        evaluate(x)
    x=toy_result()
    x["original_frozen_taxa"][-1]=x["original_frozen_taxa"][0]
    with pytest.raises(ValueError,match="roster drift"):
        evaluate(x)


def test_frozen_original_digest_is_a_64_character_immutable_check():
    assert PINNED_SOURCE_SHA256=="a032635e1acfabd89c253fe52308469735c4e13776ae3f49b7294cded9e7b6cf"
