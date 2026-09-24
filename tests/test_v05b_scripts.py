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


def test_v05b_runners_pin_frozen_gate_and_seed_family():
    s = _load("v05b_s", "run_v05b_replicate.py")
    a = _load("v05b_a", "aggregate_v05b.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == "06c6943de8cfa5a2edb8b9ecd7bde05ebb661fa5"
        assert module.FROZEN_GATE_BLOB_SHA == "ba1ff83cabf402b98ea4fd7a3e097adcb06b5fd6"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261005
    assert s.FROZEN_SEED_STRIDE == 83
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
