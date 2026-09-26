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


def test_v07m_scripts_pin_gate_seed_and_mcmc_profile():
    run = _load("v07m_run_script", "run_v07m_replicate.py")
    agg = _load("v07m_agg_script", "aggregate_v07m.py")

    for module in (run, agg):
        assert module.FROZEN_GATE_COMMIT == (
            "29eb329f778e34510b7987aa99d194dc2d4f4630"
        )
        assert module.FROZEN_GATE_BLOB_SHA == (
            "8392afc802723288f7d04e3413fe07d0f6fbc847"
        )
        assert module.FROZEN_REPLICATES_PER_WORLD == 16
        assert module.FROZEN_SEED_STRIDE == 197

    assert run.FROZEN_WARMUP == 300
    assert run.FROZEN_SAMPLES == 350
    assert run.FROZEN_CHAINS == 2
    assert run.FROZEN_CREDIBLE_MASS == 0.90
    assert run.FROZEN_TARGET_ACCEPT == 0.90

    assert run._seeds("adaptive_large_headroom", 0) == (
        20320131,
        20320231,
    )
    assert run._seeds("abstain_inadequate", 15) == (
        20350131 + 15 * 197,
        20350231 + 15 * 197,
    )
