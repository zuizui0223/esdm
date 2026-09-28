from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e2-mica-full-response-once.yml"
MARKER = ROOT / "docs" / "replication" / "E2_MICA_FULL_RESPONSE_AUTHORIZED.json"


def test_e2_mica_full_response_workflow_is_one_shot_and_currently_closed():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e2/mica-full-response-v1" in text
    assert "E2_MICA_FULL_RESPONSE_AUTHORIZED.json" in text
    assert "workflow_dispatch" not in text
    assert "full-response authorization commit must change only the marker" in text
    assert "full_response_authorized" in text
    assert "model_fitting_authorized" in text
    assert not MARKER.exists()


def test_e2_mica_response_is_downloaded_once_and_fit_reuses_capture():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count("https://ipt.inbo.be/archive.do?r=mica-agouti&v=3") == 1
    assert "e2-mica-full-response-capture-${{ github.run_id }}" in text
    fit_section = text.split("\n  fit:", 1)[1]
    assert "ipt.inbo.be" not in fit_section
    assert "actions/download-artifact@v4" in fit_section
    assert "--archive captured/mica-v3.zip" in fit_section


def test_e2_mica_capture_must_pass_before_fit_job():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        "if: needs.capture.outputs.capture_status == "
        "'RESPONSE_CAPTURE_QUALIFIED'"
    ) in text
    assert "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY" in text
    assert "tests/test_e2_mica_full_response_contract.py" in text
    assert "tests/test_e2_mica_full_response.py" in text


def test_e2_mica_worldclim_is_pinned_to_frozen_run():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e2-mica-worldclim-36318387923" in text
    assert "run-id: 36318387923" in text
