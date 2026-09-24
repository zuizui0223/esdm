import importlib.util
from pathlib import Path
import sys


def _load():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v06c_alignment_stress.py"
    spec = importlib.util.spec_from_file_location("v06c_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v06c_runner_pins_frozen_gate():
    module = _load()
    assert module.FROZEN_GATE_COMMIT == "def179b40608c85ca2809e98517ea72deb3c4757"
    assert module.FROZEN_GATE_BLOB_SHA == "108828a22c857b76baa7e3ca1a4ebc86a19ceb3a"
