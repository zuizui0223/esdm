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


def test_v07h_runners_pin_gate_seed_and_mcmc_profile():
    s = _load("v07h_s", "run_v07h_replicate.py")
    a = _load("v07h_a", "aggregate_v07h.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "66f3c4d3637744c13377e503957b5fa518c52f61"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "508f49699339c95729bc88f3061db8a0e2ed7efc"
        )

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20270105
    assert s.FROZEN_SEED_STRIDE == 181
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(15) == 20270105 + 15 * 181


def test_v07h_gate_blob_matches_pinned_hash():
    s = _load("v07h_s_blob", "run_v07h_replicate.py")
    assert s._verify_gate() == s.FROZEN_GATE_BLOB_SHA
