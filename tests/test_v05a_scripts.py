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


def test_v05a_runners_pin_frozen_gate_and_seed_family():
    q = _load("v05a_q", "run_v05a_qualification.py")
    s = _load("v05a_s", "run_v05a_replicate.py")
    a = _load("v05a_a", "aggregate_v05a.py")

    for module in (q, s, a):
        assert module.FROZEN_GATE_COMMIT == "c6b7630030b63a950008191e4e4842950b660b6e"
        assert module.FROZEN_GATE_BLOB_SHA == "d3c4d3f1b3f29858c8fdc2c69eb2003d5552111e"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261001
    assert s.FROZEN_SEED_STRIDE == 73
    assert s.FROZEN_NULL_OFFSET == 1000000
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed("interaction", 0) == 20261001
    assert s._seed("measured_shared_null", 0) == 21261001
