from pathlib import Path


def test_r2_one_shot_workflow_is_fail_closed_and_authorization_guarded():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r2-state-activity-full-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "feature/v04-frozen-validation-r2" in text
    assert "timeout-minutes: 360" in text
    assert 'python-version: "3.12"' in text
    assert 'python -m pip install -e ".[dev,inference]"' in text
    assert "docs/validation/V04_R2_RUN_AUTHORIZED" in text
    assert "needs: precheck" in text
    assert "if: needs.precheck.outputs.authorized == 'true'" in text
    assert "INFRASTRUCTURE_BLOCKED" in text

    for required_test in (
        "tests/test_v04_r2_effort.py",
        "tests/test_v04_r2_presence_detection.py",
        "tests/test_v04_r2_fixture.py",
        "tests/test_v04_r2_identification.py",
        "tests/test_v04_r2_gate.py",
        "tests/test_v04_r2_run.py",
        "tests/test_v04_r2_script.py",
        "tests/test_v04_r2_workflow.py",
    ):
        assert required_test in text

    assert (
        "python scripts/run_v04_r2_state_activity.py "
        "--output artifacts/v04_r2_state_activity_gate.json"
    ) in text
    assert "if: always()" in text
    assert "v04-r2-state-activity-" in text
    assert "github.run_id" in text
