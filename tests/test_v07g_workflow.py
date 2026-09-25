from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07g-calibration-placement-once.yml"
    ).read_text(encoding="utf-8")


def test_v07g_workflow_runs_sixteen_paired_replicates_after_precheck():
    text = _text()

    assert "needs: precheck" in text
    assert "needs.precheck.outputs.authorized == 'true'" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text


def test_v07g_outcome_requires_explicit_authorization():
    text = _text()

    assert "docs/validation/V07G_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    assert "cancel-in-progress: false" in text


def test_v07g_aggregate_is_fail_closed():
    text = _text()

    assert '"status":"INFRASTRUCTURE_BLOCKED"' in text
    assert "if: always()" in text
