import importlib.util
from pathlib import Path
import sys


def _load():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v05b_identification.py"
    spec = importlib.util.spec_from_file_location("run_v05b_identification", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v05b_script_pins_frozen_gate():
    module = _load()
    assert module.FROZEN_GATE_COMMIT == "a3f83975c992827eab097081e2d41224205d739f"
    assert module.FROZEN_GATE_BLOB_SHA == "c73242983e928eea31634c03b2d179b821907a64"


def test_v05b_script_has_no_scientific_override_flags():
    module = _load()
    help_text = module._parser().format_help()
    for forbidden in (
        "--beta",
        "--perturbation",
        "--target-sd",
        "--rtol",
        "--atol",
        "--replicates",
        "--warmup",
    ):
        assert forbidden not in help_text
