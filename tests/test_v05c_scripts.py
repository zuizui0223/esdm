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


def test_v05c_runner_pins_gate_and_seed_family():
    s = _load("v05c_s", "run_v05c_replicate.py")
    a = _load("v05c_a", "aggregate_v05c.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == "884872d28bc848539836e13e9f357b82f3794d01"
        assert module.FROZEN_GATE_BLOB_SHA == "c5446065cc81ea27a6c59861a3ae52a1437e8909"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261009
    assert s.FROZEN_SEED_STRIDE == 83
    assert s.FROZEN_NULL_OFFSET == 1000000
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed("interaction_event", 0) == 20261009
    assert s._seed("hidden_driver_null", 0) == 21261009
    assert s._seed("interaction_event", 15) == 20261009 + 15 * 83
