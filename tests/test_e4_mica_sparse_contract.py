from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E4_MICA_SPARSE_NUTS_CONTRACT.json"


def _read():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_e4_sparse_contract_is_separate_from_terminal_e3():
    value = _read()

    assert value["programme_id"] == "E4_MICA_SPARSE_NUTS"
    assert value["status"] == "FROZEN_PRE_OUTCOME_IMPLEMENTATION_ONLY"
    assert value["parent"]["e3_scientific_result_available"] is False
    assert value["parent"]["e3_same_programme_rerun_allowed"] is False
    assert "does not reopen" in value["parent"]["relationship"]


def test_e4_sparse_contract_changes_only_domain_representation():
    model = _read()["scientific_model"]

    assert model["ecological_processes_unchanged"] is True
    assert model["observation_likelihoods_unchanged"] is True
    assert model["covariates_unchanged"] is True
    assert model["priors_unchanged"] is True
    assert model["training_heldout_partition_unchanged"] is True
    assert model["heldout_score_definition_unchanged"] is True

    exact = _read()["exact_compaction"]
    assert exact["posterior_target_changed"] is False
    assert exact["approximation_introduced"] is False
    assert "structural_exposure_mask is false" in exact["transformation"]


def test_e4_sparse_contract_freezes_actual_mica_compaction_geometry():
    exact = _read()["exact_compaction"]
    training = exact["training"]
    heldout = exact["heldout"]

    assert training["dense_context_count"] == 615020
    assert training["compact_context_count"] == 11531
    assert training["reduction_factor"] == pytest.approx(53.33622409157922)
    assert training["retained_keys_sha256"] == (
        "41bd70aa1f913bcb1c988f6c5cdae3441ed978d4ee0f6791bcfc497290710646"
    )
    assert training["exposed_contexts_by_stream"] == {
        "presence_opportunistic": 3286,
        "presence_calibrated": 3466,
        "annotated": 4779,
    }

    assert heldout["dense_context_count"] == 560012
    assert heldout["compact_context_count"] == 10168
    assert heldout["reduction_factor"] == pytest.approx(55.07592446892211)
    assert heldout["retained_keys_sha256"] == (
        "0ed3fb9e96b1323a4290b7cb92621d219e317b8b916201a1b2665db4a272b1d9"
    )
    assert heldout["exposed_contexts_by_stream"] == {
        "presence_opportunistic": 0,
        "presence_calibrated": 0,
        "annotated": 10168,
    }


def test_e4_sparse_contract_keeps_e3_nuts_profile_and_blocks_laplace():
    value = _read()
    inference = value["inference"]

    assert inference["backend"] == "NumPyro NUTS"
    assert inference["num_warmup"] == 300
    assert inference["num_samples"] == 350
    assert inference["num_chains"] == 2
    assert inference["target_accept_probability"] == 0.9
    assert inference["rng_seed_full"] == 20260927
    assert inference["rng_seed_activity_knockout"] == 20260928
    assert inference["rng_seed_state_knockout"] == 20260929
    assert value["fallback_boundary"]["laplace_or_inla_backend_authorized_now"] is False


def test_e4_sparse_contract_requires_no_fit_qualification_first():
    q = _read()["qualification_before_empirical_fit"]

    assert q["required"] is True
    assert q["empirical_fit_authorized_now"] is False
    assert q["qualification_may_emit_scientific_scores"] is False
    assert q["qualification_may_run_mcmc"] is False
    assert q["likelihood_identity_absolute_tolerance"] == 1e-12
