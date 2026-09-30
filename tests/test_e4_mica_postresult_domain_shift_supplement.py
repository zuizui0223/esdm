from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT = (
    ROOT / "docs" / "replication"
    / "E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json"
)


def _read() -> dict:
    return json.loads(SUPPLEMENT.read_text(encoding="utf-8"))


def test_e4_domain_shift_supplement_is_downstream_only():
    value = _read()
    boundary = value["analysis_boundary"]

    assert value["status"] == "POSTRESULT_EXPLORATORY_SUPPLEMENT"
    assert value["parent_audit"]["audit_id"] == "e4-mica-postresult-transfer-tail-v1"
    assert value["source_result"]["workflow_run_id"] == 36622802225
    assert value["source_result"]["artifact_id"] == 11059622869
    assert value["source_result"]["heldout_deployment_rows"] == 733
    assert value["source_result"]["fixture_fingerprint_sha256"] == (
        "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
    )
    assert boundary["post_outcome"] is True
    assert boundary["new_model_fit"] is False
    assert boundary["posterior_refit"] is False
    assert boundary["retuning"] is False
    assert boundary["backend_switch"] is False
    assert boundary["laplace_or_inla"] is False
    assert boundary["claim_promotion"] is False
    assert boundary["frozen_e4_result_changed"] is False


def test_activity_failure_is_carried_by_event_bearing_deployments():
    value = _read()["event_bearing_deployment_decomposition"]

    assert value["zero_focal_event_deployments"] == 605
    assert value["positive_focal_event_deployments"] == 128
    assert value["positive_event_deployments_with_negative_activity_gain"] == 127
    assert value["positive_event_deployments_with_positive_activity_gain"] == 1
    assert value["positive_event_activity_gain_sum"] < -468.0
    assert abs(value["zero_event_activity_gain_mean"]) < 1e-6


def test_source_domain_shift_is_explicit_but_not_causal():
    value = _read()
    strata = value["source_stratum_shift"]
    d = strata["D_stratum"]

    assert strata["training_state_annotated_deployments_by_prefix"]["D"] == 0
    assert strata["training_state_annotated_deployments_by_prefix"]["NL"] == 0
    assert strata["heldout_focal_events_by_prefix"]["D"] == 5091
    assert d["heldout_focal_event_fraction"] > 0.98
    assert d["negative_activity_gain_magnitude_fraction"] > 0.99
    assert d["locations_with_negative_mean_activity_gain"] == d["unique_locations"] == 8
    assert "causal" in strata["interpretive_limit"].lower()


def test_diel_contrast_shifts_and_frozen_activity_surface_underpredicts_day_events():
    value = _read()
    diel = value["raw_diel_rate_shift"]
    plugin = value["posterior_mean_activity_context_diagnostic"]

    assert diel["training_state_annotated"]["night_day_rate_ratio"] > 13.0
    assert 2.9 < diel["heldout_all"]["night_day_rate_ratio"] < 3.1
    assert 2.9 < diel["heldout_D"]["night_day_rate_ratio"] < 3.1
    assert plugin["training_state_annotated_event_context_activity_probability"]["median"] > 0.9
    assert plugin["heldout_event_context_activity_probability"]["median"] < 0.2
    assert plugin["heldout_day_event_context_activity_probability"]["median"] < 0.001


def test_positive_state_gain_is_localized_and_sign_mixed():
    value = _read()["state_gain_localization"]

    assert value["aggregate_state_gain"] > 0.0
    assert value["event_bearing_deployments_positive_state_gain"] == 58
    assert value["event_bearing_deployments_negative_state_gain"] == 70
    assert value["group_event_deployments_state_gain_sum"] > 0.0
    assert value["no_group_event_deployments_state_gain_sum"] < 0.0
