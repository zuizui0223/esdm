from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E4_MICA_SPARSE_FIT_CONTRACT.json"
SCRIPT = ROOT / "scripts" / "fit_e4_mica_sparse.py"


def _read():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_e4_fit_contract_pins_qualified_sparse_fixture():
    value = _read()
    qualification = value["qualification"]

    assert value["programme_id"] == "E4_MICA_SPARSE_NUTS"
    assert value["status"] == "FROZEN_FIT_NOT_AUTHORIZED"
    assert qualification["workflow_run_id"] == 36621160011
    assert qualification["artifact_id"] == 11058179352
    assert qualification["artifact_digest"] == (
        "sha256:07afb1d5e41c4515148a5c0c9bea2ac1f3c8a6ad9278e9ba8e504c8d0a583631"
    )
    assert qualification["result_sha256"] == (
        "2a8ce70ce8eefbbd70a2cdeaa2f4fc558aa64ab061985c263c8d1656979d83ff"
    )
    assert qualification["required_status"] == "E4_SPARSE_QUALIFIED"


def test_e4_fit_contract_keeps_exact_e3_nuts_profile():
    value = _read()
    fit = value["fit"]
    compact = value["exact_compaction"]

    assert fit["backend"] == "NumPyro NUTS"
    assert fit["fits"] == ["full", "activity_knockout", "state_knockout"]
    assert fit["num_warmup"] == 300
    assert fit["num_samples"] == 350
    assert fit["num_chains"] == 2
    assert fit["target_accept_probability"] == 0.9
    assert fit["rng_seed_full"] == 20260927
    assert fit["rng_seed_activity_knockout"] == 20260928
    assert fit["rng_seed_state_knockout"] == 20260929
    assert compact["training_compact_contexts"] == 11531
    assert compact["heldout_compact_contexts"] == 10168
    assert compact["posterior_target_changed"] is False
    assert compact["approximation_introduced"] is False


def test_e4_fit_contract_predeclares_output_and_terminal_boundaries():
    value = _read()

    assert value["outputs"]["heldout_row_count"] == 733
    assert value["outputs"]["row_level_absolute_scores_required"] is True
    assert value["decision"]["minimum_effect_size_threshold"] is None
    assert value["decision"]["confirmatory_replication_claim"] is False
    assert value["decision"]["e3_rescue_claim"] is False
    assert value["execution_safety"]["prewrite_result_before_mcmc"] is True
    assert value["execution_safety"]["same_programme_rerun_allowed"] is False
    assert value["execution_safety"]["laplace_or_inla_backend_authorized_now"] is False
    assert value["execution"]["fit_authorized_now"] is False


def test_e4_runner_prewrite_occurs_before_expensive_fit():
    text = SCRIPT.read_text(encoding="utf-8")

    prewrite = text.index("_write(args.out, result)")
    fit = text.index("fit_e4_mica_sparse_nuts(fixture")
    assert prewrite < fit
    assert '"E4_SPARSE_EXECUTION_STARTED"' in text
    assert '"E4_SPARSE_EXECUTION_STOP"' in text


def test_e4_runner_is_syntactically_valid():
    text = SCRIPT.read_text(encoding="utf-8")
    compile(text, str(SCRIPT), "exec")
