import importlib.util
from pathlib import Path
import sys


def _load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v04_r2_state_activity.py"
    spec = importlib.util.spec_from_file_location("run_v04_r2_state_activity", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_r2_script_freezes_scientific_execution_profile():
    module = _load_script()

    assert module.FROZEN_GATE_COMMIT == "9e6db6fbe8336c6eb8bbe354713d2863fc40033f"
    assert module.FROZEN_REPLICATES == 16
    assert module.FROZEN_BASE_SEED == 20260926
    assert module.FROZEN_SEED_STRIDE == 47
    assert module.FROZEN_WARMUP == 300
    assert module.FROZEN_SAMPLES == 350
    assert module.FROZEN_CHAINS == 2
    assert module.FROZEN_CREDIBLE_MASS == 0.90
    assert module.FROZEN_TARGET_ACCEPT == 0.90

    help_text = module._parser().format_help()
    for forbidden in (
        "--replicates",
        "--base-seed",
        "--seed-stride",
        "--warmup",
        "--samples",
        "--chains",
        "--credible-mass",
        "--target-accept",
    ):
        assert forbidden not in help_text


def test_r2_worker_command_is_one_frozen_replicate_shard(tmp_path):
    module = _load_script()
    source = tmp_path / "source.csv"
    output = tmp_path / "row.json"

    command = module._worker_command(
        replicate=5,
        source_path=source,
        output_path=output,
        progress_bar=False,
    )

    assert "--_worker-replicate" in command
    assert command[command.index("--_worker-replicate") + 1] == "5"
    assert "--_worker-source" in command
    assert "--_worker-output" in command
    for forbidden in ("--replicates", "--warmup", "--samples", "--chains"):
        assert forbidden not in command


def test_r2_replicate_seed_is_deterministic_and_bounded():
    module = _load_script()
    assert module._replicate_seed(0) == 20260926
    assert module._replicate_seed(15) == 20260926 + 15 * 47



def test_r2_json_safe_serializes_mappingproxy_dataclass():
    import json

    from esdm.validate.v04_r2_gate import R2_RECOVERY_TRUTH
    from esdm.validate.v04_r2_run import V04R2Replicate

    module = _load_script()
    truth = dict(R2_RECOVERY_TRUTH)
    row = V04R2Replicate(
        replicate=0,
        posterior_means=truth,
        posterior_lows={key: value - 0.1 for key, value in truth.items()},
        posterior_highs={key: value + 0.1 for key, value in truth.items()},
        full_heldout_log_score=-1.0,
        activity_knockout_heldout_log_score=-1.1,
        state_knockout_heldout_log_score=-1.2,
        full_divergences=0,
        activity_knockout_divergences=0,
        state_knockout_divergences=0,
    )

    payload = module._json_safe(row)

    assert payload["replicate"] == 0
    assert payload["posterior_means"] == truth
    json.dumps(payload)


def test_r2_pre_mcmc_failure_short_circuits_on_frozen_required_boolean():
    from types import SimpleNamespace

    module = _load_script()
    identification = SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=False,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
    )

    failures = module._pre_mcmc_failures(
        identification,
        extrapolation_integrity=True,
    )

    assert failures == ("positive_practical_pass",)


def test_r2_identification_payload_keeps_anchor_level_practical_metrics():
    from dataclasses import dataclass
    from types import SimpleNamespace

    module = _load_script()

    @dataclass(frozen=True)
    class Structural:
        status: object
        reason: str = "ok"

    @dataclass(frozen=True)
    class Practical:
        weak: bool
        relative_min_singular_value: float
        condition_number: float
        target_sd_proxy: float
        reasons: tuple[str, ...]

    @dataclass(frozen=True)
    class Evidence:
        target: str
        structural: Structural
        practical: Practical | None

    identified = SimpleNamespace(value="Identified")
    row = Evidence(
        target="sp.activity.activity_beta_precip",
        structural=Structural(status=identified),
        practical=Practical(
            weak=True,
            relative_min_singular_value=0.0005,
            condition_number=2000.0,
            target_sd_proxy=0.3,
            reasons=("too weak",),
        ),
    )
    identification = SimpleNamespace(
        positive_structural_pass=True,
        positive_practical_pass=False,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        positive_anchor_evidence=((row,),),
        sparse_anchor_evidence=((row,),),
        unknown_anchor_evidence=((row,),),
    )

    payload = module._identification_payload(identification)

    practical = payload["positive_anchor_evidence"][0][0]["practical"]
    assert practical["weak"] is True
    assert practical["target_sd_proxy"] == 0.3
    assert payload["positive_practical_pass"] is False
