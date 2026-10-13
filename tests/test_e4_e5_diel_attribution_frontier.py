from __future__ import annotations

import json
import math

import pytest

from scripts.e4_e5_diel_attribution_frontier import (
    attribution_frontier,
    from_frozen_e4_summary,
)


def test_frontier_is_an_exact_product_identity_with_no_identification():
    value = attribution_frontier(13.404766493011527, 2.964538545731028)
    c = value["relative_observed_diel_contrast"]
    assert math.isclose(c, 0.22115555293533593, rel_tol=1e-13)
    assert math.isclose(value["reciprocal_observed_diel_contrast"], 4.521704233636819)
    assert value["interpretation"] == "EXACT_AGGREGATE_ACCOUNTING_NONIDENTIFIED_NOT_A_FIT"
    for row in value["hypothetical_scenarios"]:
        assert math.isclose(
            row["relative_detection_diel_contrast"]
            * row["required_relative_passage_diel_contrast"], c, rel_tol=1e-14
        )
    assert math.isclose(value["equal_log_contributions_hypothetical_factor"] ** 2, c)
    assert math.isclose(
        value["if_passage_diel_contrast_unchanged_required_relative_detection"], c
    )


def test_inversion_of_between_cohort_passage_diel_trend_is_possible_but_not_observed():
    value = attribution_frontier(13.404766493011527, 2.964538545731028)
    scenarios = {
        row["relative_detection_diel_contrast"]:
            row["required_relative_passage_diel_contrast"]
        for row in value["hypothetical_scenarios"]
    }
    assert scenarios[0.2] > 1.0
    assert scenarios[0.25] < 1.0
    assert scenarios[1.0] == value["relative_observed_diel_contrast"]


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_invalid_ratios_are_rejected(bad):
    with pytest.raises(ValueError):
        attribution_frontier(13.0, bad)
    with pytest.raises(ValueError):
        attribution_frontier(13.0, 3.0, [bad])


def test_empty_scenario_set_is_rejected():
    with pytest.raises(ValueError):
        attribution_frontier(13.0, 3.0, [])


def test_rejects_changed_or_unpinned_source(tmp_path):
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    with pytest.raises(ValueError, match="pinned E4"):
        from_frozen_e4_summary(source)


def test_original_e4_summary_is_only_source_and_boundary_is_preserved():
    output = from_frozen_e4_summary()
    assert output["frozen_e4_run_id"] == 36622802225
    assert output["raw_biological_rows_opened"] == 0
    assert output["model_fits"] == 0
    assert output["does_not_identify_activity_or_detection"] is True
    assert output["original_E5_G4_qualification_changed"] is False
    assert output["source_cohorts"] == ["training_state_annotated", "heldout_D"]
