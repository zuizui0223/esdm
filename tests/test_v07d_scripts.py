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


def test_v07d_runners_pin_gate_seed_and_mcmc_profile():
    q = _load("v07d_q", "run_v07d_qualification.py")
    s = _load("v07d_s", "run_v07d_replicate.py")
    a = _load("v07d_a", "aggregate_v07d.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "c50e05f049da05c5b5063d5034cacfae9e8ecd98"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "131f0376a5097aa97358ff2511a63c68f2922a53"
        )

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261201
    assert s.FROZEN_SEED_STRIDE == 163
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261201
    assert s._seed(15) == 20261201 + 15 * 163


def test_v07d_gate_blob_matches_pinned_hash():
    q = _load("v07d_q_blob", "run_v07d_qualification.py")
    assert q._verify_gate() == q.FROZEN_GATE_BLOB_SHA
