import pytest

from esdm.transfer import build_v07b_dynamic_occupancy_odsp_bundle


def _result():
    records = []
    for replicate, (knockout, full) in enumerate(
        ((-2.0, -1.8), (-1.9, -1.7), (-2.1, -1.95))
    ):
        records.append(
            {
                "replicate": replicate,
                "posterior_means": {},
                "posterior_lows": {},
                "posterior_highs": {},
                "full_heldout_log_score": full,
                "occupancy_knockout_heldout_log_score": knockout,
                "full_divergences": 0,
                "knockout_divergences": 0,
            }
        )
    return {
        "schema": "esdm.v07b.dynamic_transfer.v1",
        "status": "PASS",
        "git_sha": "future-v07b",
        "infrastructure_block": None,
        "information_filtration": [
            {
                "name": "suitability_only",
                "information": ["suitability"],
                "score_field": "occupancy_knockout_heldout_log_score",
            },
            {
                "name": "suitability_dynamic_occupancy",
                "information": ["suitability", "dynamic_occupancy"],
                "score_field": "full_heldout_log_score",
            },
        ],
        "score_contract": {
            "kind": "log",
            "name": "mean_heldout_log_predictive_density",
            "unit": "nats_per_heldout_context",
            "orientation": "higher_is_better",
        },
        "replicates": records,
    }


def test_v07b_binding_exports_absolute_scores_as_nested_information():
    bundle = build_v07b_dynamic_occupancy_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_v07b_dynamic_occupancy_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_only",
            "information": ["suitability"],
            "score_column": "score__suitability_only",
        },
        {
            "name": "suitability_dynamic_occupancy",
            "information": ["suitability", "dynamic_occupancy"],
            "score_column": "score__suitability_dynamic_occupancy",
        },
    ]
    assert bundle.rows[0]["score__suitability_only"] == pytest.approx(-2.0)
    assert bundle.rows[0]["score__suitability_dynamic_occupancy"] == pytest.approx(-1.8)
    assert bundle.manifest["source_schema"] == "esdm.v07b.dynamic_transfer.v1"


def test_v07b_binding_rejects_filtration_or_score_contract_drift():
    broken = _result()
    broken["information_filtration"][1]["information"] = ["suitability", "movement"]
    with pytest.raises(ValueError, match="filtration drifted"):
        build_v07b_dynamic_occupancy_odsp_bundle(broken)

    broken = _result()
    broken["score_contract"]["unit"] = "arbitrary"
    with pytest.raises(ValueError, match="score contract drifted"):
        build_v07b_dynamic_occupancy_odsp_bundle(broken)


def test_v07b_binding_rejects_infrastructure_block():
    blocked = _result()
    blocked["status"] = "INFRASTRUCTURE_BLOCKED"
    blocked["infrastructure_block"] = {"reason": "blocked"}

    with pytest.raises(ValueError, match="completed scientific result"):
        build_v07b_dynamic_occupancy_odsp_bundle(blocked)
