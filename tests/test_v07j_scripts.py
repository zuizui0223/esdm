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


def test_v07j_runners_pin_gate_world_seeds_and_mcmc_profile():
    s = _load("v07j_s", "run_v07j_replicate.py")
    a = _load("v07j_a", "aggregate_v07j.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "41d669b2b3fce602d969bd60b7c469de6e9ebc83"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "7d576aef64fdc16373ec56eb60ba5a5c40bb6666"
        )

    assert s.FROZEN_WORLDS == ("transfer_positive", "reversal")
    assert s.FROZEN_REPLICATES_PER_WORLD == 16
    assert s.FROZEN_BASE_SEEDS["transfer_positive"] == 20261301
    assert s.FROZEN_BASE_SEEDS["reversal"] == 20271301
    assert s.FROZEN_SEED_STRIDE == 179
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90


def test_v07j_gate_blob_matches_pinned_hash():
    s = _load("v07j_s_blob", "run_v07j_replicate.py")
    assert s._verify_gate() == s.FROZEN_GATE_BLOB_SHA
