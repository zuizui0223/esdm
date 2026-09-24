import importlib.util
from pathlib import Path
import sys


def _load():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v06c_frontier.py"
    spec = importlib.util.spec_from_file_location("v06c_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v06c_runner_pins_frozen_gate():
    module = _load()
    assert module.FROZEN_GATE_COMMIT == "1441d7ca241b09cad54563f3b6c0ed53bae6aa90"
    assert module.FROZEN_GATE_BLOB_SHA == "f09f1857756bf1b14c2f8c9888f35cf1d6a44ab7"
