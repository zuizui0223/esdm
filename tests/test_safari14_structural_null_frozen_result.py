"""Freeze retrospective Safari14 null diagnostics and prevent ecological overclaim.

This test reads only archived aggregate receipt and the interpretive markdown.
No original animal, image, project camera, or sequence data is opened.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPL = ROOT / "docs" / "replication"


def _receipt():
    return json.loads((REPL/"SAFARI14_STRUCTURAL_NULL_RESULT_RECEIPT.json").read_text(encoding="utf-8"))


def test_original_frozen_and_new_aggregate_artifact_digest_provenance():
    r=_receipt()
    p=r["evidence"]
    assert p["frozen_empirical_run_id"] == 42848095854
    assert p["frozen_empirical_json_sha256"] == "f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
    assert p["new_aggregate_only_run_id"] == 43577782379
    assert p["new_run_conclusion"] == "success"
    assert p["artifact_id"] == 14106593727
    assert p["artifact_zip_sha256"] == "a8e71dc30fdb2f0e102bc5d1b75dc4305e07cf975be854205598d53dd2e4b0be"
    assert p["result_json_sha256"] == "c4cacd72617d414791e2f44cc8832fad982b00e4f4187d103bdc8ee3f727b303"
    assert p["new_wildlife_rows_opened"] == 0


def test_original_observation_and_uniform_random_scenario_both_turnover_dominant():
    r=_receipt()
    assert r["original_observed"]["both_splits_turnover_dominant_original_camera_draws"]==500
    null0=r["scenarios"][0]
    assert null0["alpha"]==0
    assert null0["discovery_dominant"]==500
    assert null0["validation_dominant"]==500
    assert null0["discovery_sim"]>null0["discovery_sne"]
    assert null0["validation_sim"]>null0["validation_sne"]
    assert null0["discovery_sim"]>r["original_observed"]["discovery_beta_sim"]
    assert null0["validation_sim"]>r["original_observed"]["validation_beta_sim"]


def test_increasing_frequency_weight_sensitivity_can_reverse_discovery_dominance():
    r=_receipt()
    q=r["scenarios"]
    assert [x["alpha"] for x in q]==[0,0.5,1]
    assert [(x["discovery_dominant"],x["validation_dominant"]) for x in q] == [
        (500,500),(485,500),(4,494)
    ]
    assert q[0]["discovery_sim"]>q[1]["discovery_sim"]>q[2]["discovery_sim"]
    assert q[0]["discovery_sne"]<q[1]["discovery_sne"]<q[2]["discovery_sne"]
    assert q[0]["validation_sim"]>q[1]["validation_sim"]>q[2]["validation_sim"]
    assert q[0]["validation_sne"]<q[1]["validation_sne"]<q[2]["validation_sne"]
    assert r["setup"]["median_pair_abs_richness_gap_discovery"] == 6
    assert r["setup"]["median_pair_abs_richness_gap_validation"] == 2


def test_post_outcome_diagnostic_does_not_prove_nonrandom_assembly():
    r=_receipt()
    x=r["inference_limits"]
    assert x["post_outcome_illustrative_not_confirmatory"] is True
    assert x["original_turnover_dominance_observation_unchanged"] is True
    assert x["artificial_sets_not_actual_camera_by_species_incidence"] is True
    assert x["null_simulation_frequency_not_formal_p_value_or_confidence_interval"] is True
    assert x["environmental_filtering_dispersal_or_interactions_not_inferred"] is True
    assert x["E5_G4_unpassed"] is True
    note=(REPL/"SAFARI14_STRUCTURAL_NULL_ECOLOGICAL_INTERPRETATION.md").read_text(encoding="utf-8")
    for snippet in ("500/500", "4/500", "not a", "post-outcome", "camera", "null"):
        assert snippet.lower() in note.lower()
