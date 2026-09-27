from pathlib import Path


def _workflow():
    return (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "e2-mica-temporal-integrity-once.yml"
    ).read_text(encoding="utf-8")


def test_e2_mica_temporal_workflow_is_authorization_only_and_one_shot():
    text = _workflow()

    assert "e2/mica-temporal-integrity-v1-r2" in text
    assert "E2_MICA_TEMPORAL_INTEGRITY_AUTHORIZED_R2.json" in text
    assert "workflow_dispatch" not in text
    assert "authorization commit must change only" in text
    assert "full_response_authorized" in text


def test_e2_mica_temporal_workflow_never_runs_model_fit():
    text = _workflow()

    assert "audit_e2_mica_temporal_integrity.py" in text
    assert "fit_numpyro" not in text
    assert "run_empirical" not in text
    assert "heldout" in text
    assert "model_fits" in text
    assert "heldout_scores" in text


def test_e2_mica_temporal_workflow_uploads_pass_or_stop_result():
    text = _workflow()

    assert "TEMPORAL_INTEGRITY_PASS" in text
    assert "STOP_TEMPORAL_INTEGRITY" in text
    assert "if: always()" in text
    assert "requires_separate_full_response_authorization" in text


def test_e2_mica_temporal_r2_fetches_complete_history_for_ancestor_check():
    text = _workflow()

    assert "fetch-depth: 0" in text
    assert "e2-mica-temporal-integrity-r2-infrastructure-amendment-v1" in text
