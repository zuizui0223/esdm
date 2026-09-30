from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = (
    ROOT / "docs" / "replication"
    / "E4_MICA_SPARSE_POSTRESULT_DIAGNOSTIC.json"
)


def _read() -> dict:
    return json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))


def test_e4_postresult_diagnostic_is_bound_and_noninterventional():
    value = _read()
    source = value["source_result"]
    boundary = value["analysis_boundary"]

    assert value["status"] == "POST_OUTCOME_DESCRIPTIVE_ONLY"
    assert value["diagnostic_id"] == (
        "e4-mica-exact-sparse-postresult-descriptive-v1"
    )
    assert source["workflow_run_id"] == 36622802225
    assert source["artifact_id"] == 11059622869
    assert source["heldout_deployment_rows"] == 733
    assert source["fixture_fingerprint_sha256"] == (
        "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
    )
    assert source["result_json_sha256"] == (
        "34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2"
    )
    assert boundary["post_outcome"] is True
    assert boundary["new_model_fit"] is False
    assert boundary["posterior_refit"] is False
    assert boundary["retuning"] is False
    assert boundary["backend_switch"] is False
    assert boundary["laplace_or_inla"] is False
    assert boundary["claim_promotion"] is False


def test_activity_failure_is_event_bearing_and_tail_concentrated():
    value = _read()["activity_gain_decomposition"]
    positive = value["positive_event_deployments"]
    zero = value["zero_event_deployments"]
    tail = value["negative_tail_concentration"]

    assert positive["count"] == 128
    assert positive["negative_gain_count"] == 127
    assert positive["positive_gain_count"] == 1
    assert positive["mean_gain"] < -3.0
    assert zero["count"] == 605
    assert zero["negative_gain_count"] == 0
    assert zero["positive_gain_count"] == 605
    assert abs(zero["mean_gain"]) < 1e-6
    assert tail["deployments_to_reach_50pct_negative_magnitude"] == 13
    assert tail["deployments_to_reach_80pct_negative_magnitude"] == 34
    assert tail["deployments_to_reach_90pct_negative_magnitude"] == 49


def test_activity_failure_coincides_with_extreme_transfer_geometry():
    value = _read()
    strata = value["source_strata"]
    d = strata["D_stratum_share"]
    plugin = value["activity_posterior_mean_plugin"]
    probability = plugin["event_context_activity_probability"]
    eastness = plugin["heldout_eastness_z_train"]

    assert d["focal_event_fraction"] > 0.98
    assert d["negative_activity_gain_magnitude_fraction"] > 0.99
    assert d["locations_with_negative_mean_activity_gain"] == d["unique_locations"] == 8
    assert eastness["min"] > 3.0
    assert eastness["max"] > 8.0
    assert probability["training_state_annotated_median"] > 0.9
    assert probability["heldout_median"] < 0.2
    assert probability["heldout_day_median"] < 0.001


def test_raw_diel_shift_and_state_gain_are_mixed_not_promoted():
    value = _read()
    diel = value["diel_event_rate_diagnostic"]
    state = value["state_gain_decomposition"]

    assert diel["training_state_annotated"]["night_day_rate_ratio"] > 10.0
    assert 2.0 < diel["heldout_all"]["night_day_rate_ratio"] < 4.0
    assert state["positive_event_deployments_positive_gain"] == 58
    assert state["positive_event_deployments_negative_gain"] == 70
    assert state["group_event_deployments"]["state_gain_sum"] > 0.0
    assert state["no_group_event_deployments"]["state_gain_sum"] < 0.0
    assert "Upgrading the small positive state gain to confirmatory or causal evidence." in (
        value["interpretation"]["not_supported"]
    )
