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


def test_v07f_runners_pin_gate_world_seeds_and_mcmc_profile():
    q = _load("v07f_q", "run_v07f_qualification.py")
    s = _load("v07f_s", "run_v07f_replicate.py")
    a = _load("v07f_a", "aggregate_v07f.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "09a6ac71bcc1ddfc6781253e8b48aa377115e5d1"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "092e3c706abe55912776f99fa5418e9ed205cc22"
        )

    assert s.FROZEN_WORLDS == ("dynamic_like", "static_like")
    assert s.FROZEN_REPLICATES_PER_WORLD == 16
    assert s.FROZEN_BASE_SEEDS["dynamic_like"] == 20261217
    assert s.FROZEN_BASE_SEEDS["static_like"] == 20271217
    assert s.FROZEN_SEED_STRIDE == 173
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed("dynamic_like", 0) == 20261217
    assert s._seed("static_like", 15) == 20271217 + 15 * 173


def test_v07f_gate_blob_matches_pinned_hash():
    q = _load("v07f_q_blob", "run_v07f_qualification.py")
    assert q._verify_gate() == q.FROZEN_GATE_BLOB_SHA
