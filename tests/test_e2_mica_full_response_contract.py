import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "docs" / "replication" / "E2_MICA_FULL_RESPONSE_CONTRACT.json"
TEMPORAL = ROOT / "docs" / "replication" / "E2_MICA_TEMPORAL_INTEGRITY_RESULT.json"
CLIMATE = ROOT / "docs" / "replication" / "E2_MICA_WORLDCLIM_FROZEN.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_e2_mica_pre_response_dependencies_are_frozen_and_passed():
    temporal = _read(TEMPORAL)
    climate = _read(CLIMATE)
    contract = _read(FULL)

    assert temporal["status"] == "TEMPORAL_INTEGRITY_PASS"
    assert temporal["decision"]["passed"] is True
    assert temporal["decision"]["authorizes_full_response"] is False
    assert temporal["quarantine"]["event_count"] == 11
    assert temporal["quarantine"]["event_identity_set_sha256"] == (
        "1c3b13e44a0db6e09a47babb42617d34ba7813e080eb5c5201c8e7f1790bc9f9"
    )

    assert climate["status"] == "CLIMATE_QUALIFIED"
    assert climate["decision"]["climate_qualified"] is True
    assert climate["decision"]["authorizes_full_response"] is False
    assert climate["deployment_climate_sha256"] == (
        "c05fe8cf883d929ae618d3ccd8e64c33a7534517341ede36aafa6742d86ee4df"
    )

    assert contract["status"] == "FROZEN_PRE_FULL_RESPONSE_OPEN"
    assert contract["execution"]["full_response_authorized_now"] is False


def test_e2_mica_full_response_keeps_r5b_estimability_and_fit_profile():
    contract = _read(FULL)
    stops = contract["consumed_estimability_stops"]
    assert stops["minimum_opportunistic_focal_events"] == 10
    assert stops["minimum_calibrated_focal_events"] == 10
    assert stops["minimum_training_state_annotated_each_state"] == 10
    assert stops["minimum_state_calibration_each_state"] == 10
    assert stops["minimum_heldout_state_annotated_each_state"] == 5

    fit = contract["fit"]
    assert fit["fits"] == ["full", "activity_knockout", "state_knockout"]
    assert fit["num_warmup"] == 300
    assert fit["num_samples"] == 350
    assert fit["num_chains"] == 2
    assert fit["target_accept_probability"] == 0.90
    assert fit["rng_seed_full"] == 20260927
    assert fit["rng_seed_activity_knockout"] == 20260928
    assert fit["rng_seed_state_knockout"] == 20260929


def test_e2_mica_count_and_quarantine_semantics_are_fixed_before_response():
    contract = _read(FULL)
    focal = contract["focal_endpoint"]
    assert focal["species"] == "Ondatra zibethicus"
    assert focal["quarantine_applied_before_focal_filter"] is True
    assert "one distinct positive" in focal["positive_count_rule"]
    assert "more than one distinct positive" in focal["positive_count_rule"]
    assert focal["state_mapping"]["solitary"].endswith("== 1")
    assert focal["state_mapping"]["group"].endswith(">= 2")

    quarantine = contract["temporal_quarantine"]
    assert quarantine["quarantine_event_count"] == 11
    assert quarantine["event_identity_set_sha256"] == (
        "1c3b13e44a0db6e09a47babb42617d34ba7813e080eb5c5201c8e7f1790bc9f9"
    )


def test_e2_mica_odsp_serialization_is_absolute_and_row_level():
    contract = _read(FULL)
    primary = contract["primary_empirical_endpoints"]
    assert primary["minimum_effect_size_threshold"] is None
    assert primary["activity_gain"] == "full - activity_knockout"
    assert primary["state_gain"] == "full - state_knockout"

    odsp = contract["row_level_odsp_serialization"]
    assert odsp["required"] is True
    assert odsp["row_unit"] == "one east-heldout deployment"
    assert odsp["equal_weight_mean_must_equal_aggregate_score"] is True
    assert odsp["absolute_tolerance"] == 1e-12


def test_e2_mica_one_open_rule_is_terminal_and_nonretunable():
    contract = _read(FULL)
    rule = contract["one_open_rule"]
    assert all(value is False for key, value in rule.items() if key != "negative_or_null_empirical_result_is_terminal")
    assert rule["negative_or_null_empirical_result_is_terminal"] is True
