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


def test_v07j_runners_pin_gate_worlds_and_seed_families():
    run = _load("v07j_run_script", "run_v07j_replicate.py")
    agg = _load("v07j_agg_script", "aggregate_v07j.py")

    assert run.FROZEN_GATE_COMMIT == "14dfe742bd1f676ffa1cd94ea99ee9f5f9e0d5c7"
    assert run.FROZEN_GATE_BLOB_SHA == "ef2c8f6aa412a3a05a1201778ff430d4d4385613"
    assert agg.FROZEN_GATE_COMMIT == run.FROZEN_GATE_COMMIT
    assert agg.FROZEN_GATE_BLOB_SHA == run.FROZEN_GATE_BLOB_SHA

    assert run.FROZEN_REPLICATES_PER_WORLD == 12
    assert run.FROZEN_WARMUP == 300
    assert run.FROZEN_SAMPLES == 350
    assert run.FROZEN_CHAINS == 2
    assert run.FROZEN_CREDIBLE_MASS == 0.90
    assert run.FROZEN_TARGET_ACCEPT == 0.90
    assert run.FROZEN_SEED_FAMILIES == {
        "low_occupancy": (20300117, 211),
        "high_occupancy": (20310117, 223),
        "high_turnover": (20320117, 227),
    }

    assert run._seed("low_occupancy", 0) == 20300117
    assert run._seed("high_turnover", 11) == 20320117 + 11 * 227
