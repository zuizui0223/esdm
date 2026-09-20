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
