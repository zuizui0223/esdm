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
        assert module.FROZEN_GATE_COMMIT == (
            "3f542a4069bb77eda706e99347dda51414132ce9"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "e4bc1e342808353f65067a2379c9813a13e867a4"
        )

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261209
    assert s.FROZEN_SEED_STRIDE == 167
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261209
    assert s._seed(15) == 20261209 + 15 * 167


def test_v07e_gate_blob_matches_pinned_hash():
    q = _load("v07e_q_blob", "run_v07e_qualification.py")
    assert q._verify_gate() == q.FROZEN_GATE_BLOB_SHA
