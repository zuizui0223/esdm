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


def test_r7_shard_freezes_seed_and_mcmc_profile():
    module = _load("r7_shard", "run_v04_r7_replicate.py")

    assert module.FROZEN_GATE_COMMIT == "2c6c1473cbe7a571ee8972476225574a7906a1cb"
    assert module.FROZEN_GATE_BLOB_SHA == "7c3261211cc8b1eb51e50f912457dd54dd8fdb33"
    assert module.FROZEN_REPLICATES == 16
    assert module.FROZEN_BASE_SEED == 20260928
    assert module.FROZEN_SEED_STRIDE == 67
    assert module.FROZEN_WARMUP == 300
    assert module.FROZEN_SAMPLES == 350
    assert module.FROZEN_CHAINS == 2
    assert module.FROZEN_TARGET_ACCEPT == 0.90
    assert module._seed(0) == 20260928
    assert module._seed(15) == 20260928 + 15 * 67


def test_r7_aggregate_uses_same_seed_family():
    module = _load("r7_aggregate", "aggregate_v04_r7.py")

    assert module.FROZEN_GATE_COMMIT == "2c6c1473cbe7a571ee8972476225574a7906a1cb"
    assert module.FROZEN_GATE_BLOB_SHA == "7c3261211cc8b1eb51e50f912457dd54dd8fdb33"
    assert module._seed(15) == 20260928 + 15 * 67
