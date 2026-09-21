import importlib.util
from pathlib import Path
import sys


def _load_script():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_v04_r3a_qualification.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_v04_r3a_qualification",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_r3a_script_freezes_gate_and_budget_constants():
    module = _load_script()

    assert (
        module.FROZEN_GATE_COMMIT
        == "7fac98708d4474dc175d48c0ec3854f63d0ba527"
    )
    assert module.FROZEN_GATE_BLOB_SHA == "72ea44d467b41f78a0e9ec71941d8bb2ab26a227"
    assert module.ANNOTATED_SITE_COUNT == 36
    assert module.ANNOTATED_TIME_COUNT == 12
    assert module.ANNOTATED_CONTEXT_COUNT == 432
    assert module.CALIBRATED_SITE_COUNT == 18
    assert module.CALIBRATED_CONTEXT_COUNT == 432


def test_r3a_script_has_no_scientific_override_flags():
    module = _load_script()
    help_text = module._parser().format_help()

    for forbidden in (
        "--sites",
        "--times",
        "--target-sd",
        "--condition-number",
        "--singular-value",
        "--anchor",
        "--rtol",
        "--atol",
    ):
        assert forbidden not in help_text


def test_r3a_initial_payload_fails_closed():
    module = _load_script()

    payload = module._initial_payload()

    assert payload["status"] == "INFRASTRUCTURE_BLOCKED"
    assert payload["gate_freeze_commit"] == module.FROZEN_GATE_COMMIT
    assert payload["infrastructure_block"] is not None
