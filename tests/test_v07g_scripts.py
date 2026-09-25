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


def test_v07g_runners_pin_gate_seed_and_mcmc_profile():
    s = _load("v07g_s", "run_v07g_replicate.py")
    a = _load("v07g_a", "aggregate_v07g.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "5efbb6a34ab202c702d1206de325d3781185204a"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "a37866fb2bd368515f697aa5dbd3f3fb9da04ca8"
        )

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261225
    assert s.FROZEN_SEED_STRIDE == 179
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261225
    assert s._seed(15) == 20261225 + 15 * 179


def test_v07g_gate_blob_matches_pinned_hash():
    s = _load("v07g_s_blob", "run_v07g_replicate.py")
    assert s._verify_gate() == s.FROZEN_GATE_BLOB_SHA
