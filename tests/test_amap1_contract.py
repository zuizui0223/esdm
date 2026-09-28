import json
from pathlib import Path

from scripts.aggregate_amap1 import (
    EXPECTED_FIT_COUNT,
    EXPECTED_SHARD_COUNT,
    REPLICATES,
)
from esdm.validate.amap1_gate import AMap1GateConfig
from esdm.validate.amap1_known_truth import make_amap1_worlds
from esdm.validate.amap1_run import (
    FROZEN_AMAP1_MCMC_PROFILE,
    amap1_required_fit_plan,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "map" / "AMAP1_CONTRACT_DRAFT.json"
GATE = ROOT / "docs" / "map" / "AMAP1_QUALIFICATION_GATE.md"
WORKFLOW = ROOT / ".github" / "workflows" / "amap1-qualification-once.yml"


def test_amap1_contract_matches_runtime_and_gate_constants():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    execution = contract["execution"]
    gate = AMap1GateConfig()
    profile = FROZEN_AMAP1_MCMC_PROFILE

    assert contract["status"] == "FROZEN_PRE_OUTCOME_NOT_AUTHORIZED"
    assert execution["replicates_per_world"] == REPLICATES == 16
    assert execution["expected_shards"] == EXPECTED_SHARD_COUNT == 144
    assert execution["expected_fits"] == EXPECTED_FIT_COUNT == 384
    assert execution["materiality"] == gate.materiality == 0.005
    assert execution["positive_min_rate"] == gate.positive_min_rate == 0.75
    assert (
        execution["positive_min_mean_gain"]
        == gate.positive_min_mean_gain
        == 0.005
    )
    assert (
        execution["low_regret_max_material_rate"]
        == gate.low_regret_max_material_rate
        == 0.25
    )
    assert (
        execution["low_regret_max_mean_regret"]
        == gate.low_regret_max_mean_regret
        == 0.005
    )
    assert (
        execution["max_mean_divergences_per_fit"]
        == gate.max_mean_divergences_per_fit
        == 0.10
    )

    mcmc = execution["mcmc_profile"]
    assert mcmc["num_warmup"] == profile.num_warmup == 300
    assert mcmc["num_samples"] == profile.num_samples == 350
    assert mcmc["num_chains"] == profile.num_chains == 2
    assert (
        mcmc["target_accept_probability"]
        == profile.target_accept_prob
        == 0.90
    )


def test_amap1_declared_fit_cardinality_matches_world_plans():
    worlds = make_amap1_worlds()
    assert len(worlds) == 9

    per_replicate = sum(
        len(amap1_required_fit_plan(world.world_id))
        for world in worlds
    )
    assert per_replicate == 24
    assert per_replicate * REPLICATES == EXPECTED_FIT_COUNT == 384


def test_amap1_gate_and_workflow_name_the_same_worlds():
    worlds = tuple(world.world_id for world in make_amap1_worlds())
    gate_text = GATE.read_text(encoding="utf-8")
    workflow_text = WORKFLOW.read_text(encoding="utf-8")

    for world_id in worlds:
        assert f"- {world_id}" in workflow_text

    for geometry in ("G1", "G2", "G3"):
        assert geometry in gate_text

    for truth in ("T0", "TX", "TC"):
        assert truth in gate_text


def test_amap1_authorization_is_not_enabled_by_contract():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    execution = contract["execution"]

    assert execution["confirmatory_outcome_authorized"] is False
    assert execution["empirical_response_authorized"] is False
    assert execution["qualification_branch"] == "amap1/qualification-v1"
    assert (
        execution["authorization_marker_contract"]["path"]
        == "docs/map/AMAP1_RUN_AUTHORIZED"
    )
