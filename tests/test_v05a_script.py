import importlib.util
from pathlib import Path
import sys


def _load():
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_v05a_identification.py"
    spec = importlib.util.spec_from_file_location("run_v05a_identification", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v05a_script_pins_frozen_gate():
    module = _load()

    assert module.FROZEN_GATE_COMMIT == "d5f8d3e10c059cedfb8c3efbf5a1d232efa3507d"
    assert module.FROZEN_GATE_BLOB_SHA == "c5d43c4baa01d631704e6769db8eed49ec85837b"


def test_v05a_script_has_no_scientific_override_flags():
    module = _load()
    help_text = module._parser().format_help()

    for forbidden in (
        "--beta",
        "--target-sd",
        "--rtol",
        "--atol",
        "--condition-number",
        "--replicates",
        "--warmup",
        "--samples",
        "--chains",
    ):
        assert forbidden not in help_text
