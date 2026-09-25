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


def test_v07k_runners_pin_gate_seed_families_and_mcmc_profile():
    s = _load("v07k_s", "run_v07k_replicate.py")
    a = _load("v07k_a", "aggregate_v07k.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == (
            "7a1cd43514ec5d9c3ce12d96ec0aed5c60996b04"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "c11c885924b9806de65fbacbeb77ba0b7ca61a74"
        )

    assert s.FROZEN_WORLDS == ("transfer_positive", "reversal")
    assert s.FROZEN_REPLICATES_PER_WORLD == 16
    assert s.FROZEN_PILOT_BASE_SEEDS["transfer_positive"] == 20261321
    assert s.FROZEN_CONFIRM_BASE_SEEDS["transfer_positive"] == 20261421
    assert s.FROZEN_PILOT_BASE_SEEDS["reversal"] == 20271321
    assert s.FROZEN_CONFIRM_BASE_SEEDS["reversal"] == 20271421
    assert s.FROZEN_SEED_STRIDE == 181
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_TARGET_ACCEPT == 0.90

    pilot, confirm = s._seeds("transfer_positive", 0)
    assert pilot == 20261321
    assert confirm == 20261421
    assert pilot != confirm


def test_v07k_gate_blob_matches_pinned_hash():
    s = _load("v07k_s_blob", "run_v07k_replicate.py")
    assert s._verify_gate() == s.FROZEN_GATE_BLOB_SHA
