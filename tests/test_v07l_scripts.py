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


def test_v07l_scripts_pin_gate_and_fresh_seed_families():
    run = _load("v07l_run_script", "run_v07l_replicate.py")
    agg = _load("v07l_agg_script", "aggregate_v07l.py")

    for module in (run, agg):
        assert module.FROZEN_GATE_COMMIT == "363318c3c30aa9ff37b3d39153ecc8ab3100a14a"
        assert module.FROZEN_GATE_BLOB_SHA == "62f2183328ab7abcf6d727573031b149bfacebd3"
        assert module.FROZEN_REPLICATES_PER_WORLD == 16
        assert module.FROZEN_SEED_STRIDE == 193

    assert run.FROZEN_WARMUP == 300
    assert run.FROZEN_SAMPLES == 350
    assert run.FROZEN_CHAINS == 2
    assert run.FROZEN_CREDIBLE_MASS == 0.90
    assert run.FROZEN_TARGET_ACCEPT == 0.90

    assert run._seeds("strong_headroom", 0) == (20280131, 20280231)
    assert run._seeds("threshold_below", 15) == (
        20290131 + 15 * 193,
        20290231 + 15 * 193,
    )
