from __future__ import annotations

import pytest

from esdm.transfer import build_tr1_trait_odsp_bundle


def _result(status="PASS"):
    rows = []
    for replicate, (lower, full) in enumerate(
        ((-0.70, -0.61), (-0.68, -0.60), (-0.72, -0.63))
    ):
        rows.append(
            {
                "world": "positive",
                "replicate": replicate,
                "seed": 20261101 + replicate * 97,
                "environment_only_heldout_log_score": lower,
                "environment_trait_heldout_log_score": full,
                "fitted_trait_coefficient": 1.0,
                "lower_iterations": 5,
                "full_iterations": 6,
                "trait_gain": full - lower,
            }
        )
    return {
        "schema": "esdm.tr1.trait_transfer.v1",
        "status": status,
        "information_filtration": [
            {
                "name": "environment_only",
                "information": ["environment"],
                "score_field": "environment_only_heldout_log_score",
            },
            {
                "name": "environment_traits",
                "information": ["environment", "traits"],
                "score_field": "environment_trait_heldout_log_score",
            },
        ],
        "score_contract": {
            "kind": "log",
            "name": "mean_heldout_log_predictive_density",
            "unit": "nats_per_heldout_context",
            "orientation": "higher_is_better",
        },
        "positive_replicates": rows,
    }


def test_tr1_binding_exports_environment_to_traits_filtration():
    bundle = build_tr1_trait_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_tr1_traits_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "environment_only",
            "information": ["environment"],
            "score_column": "score__environment_only",
        },
        {
            "name": "environment_traits",
            "information": ["environment", "traits"],
            "score_column": "score__environment_traits",
        },
    ]
    assert bundle.rows[0]["score__environment_only"] == pytest.approx(-0.70)
    assert bundle.rows[0]["score__environment_traits"] == pytest.approx(-0.61)
    assert bundle.manifest["group_semantics"] == "independent known-truth replicate"
    assert bundle.manifest["source_schema"] == "esdm.tr1.trait_transfer.v1"


def test_tr1_binding_requires_scientific_pass_before_numeric_axis_export():
    with pytest.raises(ValueError, match="must PASS"):
        build_tr1_trait_odsp_bundle(_result(status="FAIL"))


def test_tr1_binding_rejects_filtration_drift():
    value = _result()
    value["information_filtration"][1]["information"] = [
        "environment",
        "taxon_identity",
    ]
    with pytest.raises(ValueError, match="filtration drifted"):
        build_tr1_trait_odsp_bundle(value)
