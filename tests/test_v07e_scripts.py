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


def test_v07e_runners_pin_gate_seed_and_mcmc_profile():
    q = _load("v07e_q", "run_v07e_qualification.py")
    s = _load("v07e_s", "run_v07e_replicate.py")
    a = _load("v07e_a", "aggregate_v07e.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == "a047fdb0fd7843b83169d5b168d86de005143c3b"
        assert module.FROZEN_GATE_BLOB_SHA == "e089e43ff009d11e87a16cd7f1c18276b0017f41"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261217
    assert s.FROZEN_SEED_STRIDE == 173
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261217
    assert s._seed(15) == 20261217 + 15 * 173
