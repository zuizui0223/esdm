from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e5-qld-deployment-capture-once.yml"


def test_qld_capture_is_marker_only_and_never_queries_observations():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-wet-tropics-deployment-capture-v1" in text
    assert "E5_QLD_DEPLOYMENT_CAPTURE_AUTHORIZED.json" in text
    assert "21d43a2e67aa65147602e0cbffb121fa729e23ba" in text
    assert "workflow_dispatch" not in text
    assert "observations_authorized" in text
    assert "media_authorized" in text
    assert "model_fitting_authorized" in text
    assert "WILDOBSR_API_KEY" in text
    assert "E5_DEPLOYMENT_CAPTURE_TRANSPORT_STOP" in text
