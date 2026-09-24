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


def test_r6_shard_freezes_seed_and_mcmc_profile():
    module = _load("r6_shard", "run_v04_r6_replicate.py")

    assert module.FROZEN_GATE_COMMIT == "3bae2166fdae6b568a0bb155d795e369445cadf1"
    assert module.FROZEN_GATE_BLOB_SHA == "d6c15b922895aee40c072a1cab4c92781507c2e5"
    assert module.FROZEN_REPLICATES == 16
    assert module.FROZEN_BASE_SEED == 20260924
    assert module.FROZEN_SEED_STRIDE == 61
    assert module.FROZEN_NULL_OFFSET == 1000000
    assert module.FROZEN_WARMUP == 300
    assert module.FROZEN_SAMPLES == 350
    assert module.FROZEN_CHAINS == 2
    assert module.FROZEN_TARGET_ACCEPT == 0.90
    assert module._seed("structured", 0) == 20260924
    assert module._seed("resolution_null", 0) == 21260924


def test_r6_aggregate_uses_same_seed_family():
    module = _load("r6_aggregate", "aggregate_v04_r6.py")

    assert module.FROZEN_GATE_COMMIT == "3bae2166fdae6b568a0bb155d795e369445cadf1"
    assert module.FROZEN_GATE_BLOB_SHA == "d6c15b922895aee40c072a1cab4c92781507c2e5"
    assert module._seed("structured", 15) == 20260924 + 15 * 61
    assert module._seed("resolution_null", 15) == 20260924 + 1000000 + 15 * 61
