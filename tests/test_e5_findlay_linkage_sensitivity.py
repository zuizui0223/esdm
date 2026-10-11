import json
from pathlib import Path

import pytest

from scripts.e5_findlay_linkage_sensitivity import calculate

ROOT=Path(__file__).resolve().parents[1]/"docs"/"replication"
FROZEN=ROOT/"E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json"
RESULT=ROOT/"E5_FINDLAY_PASSAGE_LINKAGE_SENSITIVITY_RESULT.json"


def test_sensitivity_is_deterministic_and_frozen():
    source=json.loads(FROZEN.read_text(encoding="utf-8"))
    r=calculate(source)
    saved=json.loads(RESULT.read_text(encoding="utf-8"))
    assert r["FOX_thresholds"]["first_k_per_bin_erasing_near_greater_than_far_composite"]==4
    assert r["FOX_thresholds"]["first_k_per_bin_erasing_far_greater_than_near_registration"]==6
    assert saved["FOX"]["first_k_to_erase_near_greater_than_far_composite"]==4
    assert saved["FOX"]["first_k_to_erase_far_greater_than_near_conditional_registration"]==6
    for k,x in enumerate(r["FOX_trace"]):
        y=saved["FOX"]["trace"][k]
        assert y["k"]==k
        assert y["registered_near"]==x["near_registered_bounds"]
        assert y["registered_far"]==x["far_registered_bounds"]
        assert y["min_near_minus_far_composite"]==pytest.approx(
            x["minimum_near_minus_far_total"]
        )
        assert y["min_far_minus_near_conditional"]==pytest.approx(
            x["minimum_far_minus_near_conditional"]
        )


def test_hypothetical_k_not_empirically_estimated():
    r=calculate(json.loads(FROZEN.read_text(encoding="utf-8")))
    assert r["actual_mismatch_k_measured"] is False
    assert r["upper_bound_on_actual_k_established"] is False
    assert r["boundaries"]["passage_level_identity_proven"] is False
    assert r["boundaries"]["original_E5_qualified"]==0
    assert r["boundaries"]["original_E5_G4_passed"] is False
    assert r["BADGER_far"]["composite_identified"] is False


def test_frozen_original_counts_tamper_refused():
    source=json.loads(FROZEN.read_text(encoding="utf-8"))
    next(x for x in source["stage_cells"]
         if x["species"]=="FOX" and x["distance_bin"]=="near_le_1m"
         )["registered_images"]=20
    with pytest.raises(AssertionError,match=""):
        calculate(source)
