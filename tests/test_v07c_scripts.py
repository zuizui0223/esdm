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


def test_v07c_runners_pin_gate_seed_and_mcmc_profile():
    q = _load("v07c_q", "run_v07c_qualification.py")
    s = _load("v07c_s", "run_v07c_replicate.py")
    a = _load("v07c_a", "aggregate_v07c.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "42772573e83b85174cfad8dc5d9ba5bcd77655af"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "95c6e8b7d77a7164574e7afd013dc47fbfbdcb4a"
        )

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261123
    assert s.FROZEN_SEED_STRIDE == 157
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261123
    assert s._seed(15) == 20261123 + 15 * 157


def test_v07c_gate_blob_matches_pinned_hash():
    q = _load("v07c_q_blob", "run_v07c_qualification.py")
    assert q._verify_gate() == q.FROZEN_GATE_BLOB_SHA
