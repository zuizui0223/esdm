from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    ROOT / ".github" / "workflows"
    / "e5-ecuador-event-core-precheck-once.yml"
)


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def test_ecuador_precheck_workflow_requires_pure_marker_on_dedicated_branch():
    text = _text()
    assert "e5/ecuador-event-core-precheck-v1" in text
    assert "E5_ECUADOR_EVENT_CORE_PRECHECK_AUTHORIZED.json" in text
    assert "authorization commit must change only the marker" in text
    assert "implementation_parent_sha" in text
    assert "abc16124ab57f0df56ccd396716c966bba835516" in text
    assert "workflow_dispatch" not in text


def test_ecuador_precheck_workflow_keeps_occurrence_and_fitting_forbidden():
    text = _text()
    assert "occurrence_extension_opening_authorized" in text
    assert "focal_response_opening_authorized" in text
    assert "model_fitting_authorized" in text
    assert 'int(boundary["occurrence_rows_read"]) != 0' in text
    for forbidden in (
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "occurrence.txt",
        "scientificName",
    ):
        assert forbidden not in text


def test_ecuador_precheck_workflow_uploads_only_result_and_deletes_archive():
    text = _text()
    assert "rm -f build/private/ecuador_landscape_camera_v1_3.zip" in text
    upload = text.split("- name: Upload precheck result only", 1)[1]
    assert "build/public/E5_ECUADOR_EVENT_CORE_PRECHECK_RESULT.json" in upload
    assert "build/private" not in upload
    assert "ecuador_landscape_camera_v1_3.zip" not in upload
