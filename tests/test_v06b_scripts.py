import importlib.util
from pathlib import Path
import sys


def _load():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v06b_joint_audit.py"
    spec = importlib.util.spec_from_file_location("v06b_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v06b_runner_pins_frozen_gate():
    module = _load()
    assert module.FROZEN_GATE_COMMIT == "a4cd5f2ac809fd4db65ce4418f0648a55978fd59"
    assert module.FROZEN_GATE_BLOB_SHA == "31d121519fe018c4cc20d75bfbfadbecc932f7a7"
