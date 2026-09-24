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


def test_v06a_runners_pin_gate_seed_and_mcmc_profile():
    q = _load("v06a_q", "run_v06a_qualification.py")
    s = _load("v06a_s", "run_v06a_replicate.py")
    a = _load("v06a_a", "aggregate_v06a.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == "425fc21b4d6e2285a8e04690f08d30fd4b5a34ab"
        assert module.FROZEN_GATE_BLOB_SHA == "8b601d3919284af9129aca0bf94563305c7cf0f2"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261013
    assert s.FROZEN_SEED_STRIDE == 89
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(0) == 20261013
    assert s._seed(15) == 20261013 + 15 * 89
