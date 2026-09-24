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


def test_v05b_runner_pins_gate_and_profile():
    s = _load("v05b_s", "run_v05b_replicate.py")
    a = _load("v05b_a", "aggregate_v05b.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == "0955decc9a3abfa3e30f3f4f57d90192cdecc46a"
        assert module.FROZEN_GATE_BLOB_SHA == "8cb04d4195fbd6e8e61f24f58c4202298e9e3776"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261005
    assert s.FROZEN_SEED_STRIDE == 79
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed(15) == 20261005 + 15 * 79
