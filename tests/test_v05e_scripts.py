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


def test_v05e_runner_pins_gate_seed_family_and_mcmc_profile():
    s = _load("v05e_s", "run_v05e_replicate.py")
    a = _load("v05e_a", "aggregate_v05e.py")

    for module in (s, a):
        assert module.FROZEN_GATE_COMMIT == "8d3ffa928dcb6ff9c36a8b10eaa1c76028eaecf0"
        assert module.FROZEN_GATE_BLOB_SHA == "c9dde4bf7ef95541fdcf183d1755b7c0a05c208b"

    assert s.FROZEN_REPLICATES == 16
    assert s.FROZEN_BASE_SEED == 20261009
    assert s.FROZEN_SEED_STRIDE == 83
    assert s.FROZEN_WORLD_OFFSETS["hidden_event_silent"] == 0
    assert s.FROZEN_WORLD_OFFSETS["realized_only"] == 1000000
    assert s.FROZEN_WORLD_OFFSETS["directed_realized"] == 2000000
    assert s.FROZEN_WARMUP == 300
    assert s.FROZEN_SAMPLES == 350
    assert s.FROZEN_CHAINS == 2
    assert s.FROZEN_CREDIBLE_MASS == 0.90
    assert s.FROZEN_TARGET_ACCEPT == 0.90
    assert s._seed("hidden_event_silent", 0) == 20261009
    assert s._seed("realized_only", 0) == 21261009
    assert s._seed("directed_realized", 0) == 22261009
