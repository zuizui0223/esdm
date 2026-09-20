from pathlib import Path


def test_v04_one_shot_workflow_is_fail_closed_and_marker_guarded():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-state-activity-full-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "feature/v04-frozen-validation" in text
    assert "timeout-minutes: 360" in text
    assert 'python-version: "3.12"' in text
    assert 'python -m pip install -e ".[dev,inference]"' in text
    assert "docs/validation/V04_RUN_AUTHORIZED" in text
    assert "authorization" in text
    assert "gate-v04" in text
    assert "needs: precheck" in text
    assert "if: needs.precheck.outputs.authorized == 'true'" in text
    assert "status" in text and "INFRASTRUCTURE_BLOCKED" in text

    for required_test in (
        "tests/test_v04_activity_process.py",
        "tests/test_v04_state_process.py",
        "tests/test_v04_latent_channels.py",
        "tests/test_v04_observation_blocks.py",
        "tests/test_v04_state_annotated.py",
        "tests/test_v04_simulation.py",
        "tests/test_v04_numpyro.py",
        "tests/test_v04_identifiability.py",
        "tests/test_v04_jax_scaling.py",
        "tests/test_v04_validation_fixture.py",
        "tests/test_v04_validation_gate.py",
        "tests/test_v04_validation_identification.py",
        "tests/test_v04_state_predictive_score.py",
        "tests/test_v04_validation_run.py",
        "tests/test_v04_validation_script.py",
        "tests/test_v04_validation_workflow.py",
    ):
        assert required_test in text

    assert (
        "python scripts/run_v04_state_activity.py "
        "--output artifacts/v04_state_activity_gate.json"
    ) in text
    assert "if: always()" in text
    assert "v04-state-activity-" in text
    assert "github.run_id" in text
