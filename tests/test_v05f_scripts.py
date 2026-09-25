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


def test_v05f_runners_pin_gate_seed_and_mcmc_profile():
    q = _load("v05f_q", "run_v05f_qualification.py")
    s = _load("v05f_s", "run_v05f_replicate.py")
    a = _load("v05f_a", "aggregate_v05f.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == "2247728b88c1b0acce7cf4f8362bb9d5cd541092"
        assert module.FROZEN_GATE_BLOB_SHA == "f94a598acaef95ca3d3387b8aedfed9d0dd73dd9"

    assert s.FROZEN_WORLDS == ("interaction", "measured_shared_null")
    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20271001
    assert s.FROZEN_SEED_STRIDE == 73
    assert s.FROZEN_NULL_OFFSET == 1000000
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90

    assert s._seed("interaction", 0) == 20271001
    assert s._seed("interaction", 15) == 20271001 + 15 * 73
    assert s._seed("measured_shared_null", 0) == 20271001 + 1000000
