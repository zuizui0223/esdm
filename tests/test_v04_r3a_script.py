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
        == "aa38b790e094261addd07c301edc24afa110cb4c"
    )
    assert module.FROZEN_GATE_BLOB_SHA == "ed470d4f6166c5107aeda9432ca44a985cb55e72"
    assert module.ANNOTATED_SITE_COUNT == 36
    assert module.ANNOTATED_TIME_COUNT == 12
    assert module.ANNOTATED_CONTEXT_COUNT == 432
    assert module.CALIBRATED_SITE_COUNT == 18
    assert module.CALIBRATED_TIME_COUNT == 24
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



def test_r3a_script_verifies_current_gate_blob_before_qualification(tmp_path, monkeypatch):
    module = _load_script()
    gate = tmp_path / "V04_R3A_QUALIFICATION_GATE.md"
    gate.write_text("frozen gate\n", encoding="utf-8")

    monkeypatch.setattr(module, "GATE_PATH", gate)
    monkeypatch.setattr(
        module,
        "FROZEN_GATE_BLOB_SHA",
        module._git_blob_sha1(gate.read_bytes()),
    )

    assert module._verify_gate_blob() == module.FROZEN_GATE_BLOB_SHA


def test_r3a_script_refuses_gate_blob_drift(tmp_path, monkeypatch):
    import pytest

    module = _load_script()
    gate = tmp_path / "V04_R3A_QUALIFICATION_GATE.md"
    gate.write_text("changed gate\n", encoding="utf-8")

    monkeypatch.setattr(module, "GATE_PATH", gate)
    monkeypatch.setattr(module, "FROZEN_GATE_BLOB_SHA", "0" * 40)

    with pytest.raises(RuntimeError, match="gate blob mismatch"):
        module._verify_gate_blob()
