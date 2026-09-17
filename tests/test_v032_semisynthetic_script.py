import importlib.util
from pathlib import Path
import sys


def _load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v032_semisynthetic.py"
    spec = importlib.util.spec_from_file_location("run_v032_semisynthetic", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v032_script_freezes_scientific_execution_profile():
    module = _load_script()
    assert module.FROZEN_REPLICATES == 20
    assert module.FROZEN_BASE_SEED == 20260922
    assert module.FROZEN_SEED_STRIDE == 41
    assert module.FROZEN_WARMUP == 250
    assert module.FROZEN_SAMPLES == 300
    assert module.FROZEN_CHAINS == 2
    assert module.FROZEN_CREDIBLE_MASS == 0.90
    assert module.FROZEN_TARGET_ACCEPT == 0.90

    help_text = module._parser().format_help()
    for forbidden in (
        "--replicates",
        "--base-seed",
        "--warmup",
        "--samples",
        "--chains",
        "--credible-mass",
        "--target-accept",
    ):
        assert forbidden not in help_text


def test_v032_worker_command_is_one_frozen_replicate_shard(tmp_path):
    module = _load_script()
    source = tmp_path / "source.csv"
    output = tmp_path / "row.json"
    command = module._build_worker_command(
        replicate=3,
        source_path=source,
        output_path=output,
        progress_bar=False,
    )
    assert "--_worker-replicate" in command
    assert command[command.index("--_worker-replicate") + 1] == "3"
    assert "--_worker-source" in command
    assert "--_worker-output" in command
    for forbidden in ("--replicates", "--warmup", "--samples", "--chains"):
        assert forbidden not in command


def test_v032_replicate_seed_is_deterministic_and_bounded():
    module = _load_script()
    assert module._replicate_seed(0) == 20260922
    assert module._replicate_seed(19) == 20260922 + 19 * 41
