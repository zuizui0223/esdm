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


def test_v06c_scripts_pin_gate_seed_and_mcmc_profile():
    q = _load("v06c_q", "run_v06c_qualification.py")
    s = _load("v06c_s", "run_v06c_replicate.py")
    a = _load("v06c_a", "aggregate_v06c.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == "cd1088f1d60f771b4ab6d00d089c7a9f0b08150f"
        assert module.FROZEN_GATE_BLOB_SHA == "f5fb2ae16ec8c0b37eeb1a9d87f688763ce18d83"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261021
    assert s.FROZEN_SEED_STRIDE == 101
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
