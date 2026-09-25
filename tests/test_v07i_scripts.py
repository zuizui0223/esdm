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


def test_v07i_runners_pin_gate_seeds_and_mcmc_profile():
    r = _load("v07i_r", "run_v07i_replicate.py")
    a = _load("v07i_a", "aggregate_v07i.py")

    for module in (r, a):
        assert module.FROZEN_GATE_COMMIT == (
            "aa3ac6917b9e990c6da9f0cf3e5ae7efcb281e4e"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "c6679964dbc62d08ad3dcf925d271f7a6c625353"
        )

    assert r.FROZEN_REPLICATES == 16
    assert r.FROZEN_PILOT_BASE_SEED == 20270105
    assert r.FROZEN_PILOT_SEED_STRIDE == 191
    assert r.FROZEN_CONFIRM_BASE_SEED == 20280105
    assert r.FROZEN_CONFIRM_SEED_STRIDE == 193
    assert r.FROZEN_WARMUP == 300
    assert r.FROZEN_SAMPLES == 350
    assert r.FROZEN_CHAINS == 2
    assert r.FROZEN_TARGET_ACCEPT == 0.90

    pilot = [r._pilot_seed(i) for i in range(16)]
    confirm = [r._confirm_seed(i) for i in range(16)]
    assert set(pilot).isdisjoint(set(confirm))
    assert pilot[0] == 20270105
    assert confirm[0] == 20280105


def test_v07i_gate_blob_matches_pinned_hash():
    r = _load("v07i_r_blob", "run_v07i_replicate.py")
    assert r._verify_gate() == r.FROZEN_GATE_BLOB_SHA
