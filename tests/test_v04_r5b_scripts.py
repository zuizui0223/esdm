import importlib.util
from pathlib import Path
import sys


def _load(name, filename):
    path = Path(__file__).resolve().parents[1] / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_r5b_shard_script_freezes_scientific_profile():
    module = _load("r5b_shard", "run_v04_r5b_replicate.py")

    assert module.FROZEN_GATE_COMMIT == "98c828797e73d6b40cf9a73651662d7877473bbc"
    assert module.FROZEN_GATE_BLOB_SHA == "227938d2b104d6e900dbbc7ca9d82d019db9f526"
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
        "--warmup", "--samples", "--chains", "--credible-mass",
        "--target-accept", "--base-seed", "--seed-stride",
    ):
        assert forbidden not in help_text


def test_r5b_aggregate_pins_same_gate_and_seed_sequence():
    module = _load("r5b_aggregate", "aggregate_v04_r5b.py")

    assert module.FROZEN_GATE_COMMIT == "98c828797e73d6b40cf9a73651662d7877473bbc"
    assert module.FROZEN_GATE_BLOB_SHA == "227938d2b104d6e900dbbc7ca9d82d019db9f526"
    assert module.FROZEN_REPLICATES == 16
    assert module._replicate_seed(0) == 20260926
    assert module._replicate_seed(15) == 20260926 + 15 * 47
