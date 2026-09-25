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


def test_v07b_runners_pin_gate_seed_and_mcmc_profile():
    q = _load("v07b_q", "run_v07b_qualification.py")
    s = _load("v07b_s", "run_v07b_replicate.py")
    a = _load("v07b_a", "aggregate_v07b.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "e1f805c6681d33bfc92758b2cdf9d95673353ccc"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "b0f721ac334a2e76e0387510f5a889980eaefe53"
        )

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261117
    assert s.FROZEN_SEED_STRIDE == 113
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261117
    assert s._seed(15) == 20261117 + 15 * 113


def test_v07b_gate_blob_matches_pinned_hash():
    q = _load("v07b_q_blob", "run_v07b_qualification.py")
    assert q._verify_gate() == q.FROZEN_GATE_BLOB_SHA
