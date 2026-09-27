from pathlib import Path


def _workflow_text():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v04-r5b-recovery-transfer-once.yml"
    )
    return path.read_text(encoding="utf-8")


def test_r5b_workflow_has_16_shards_and_final_aggregation():
    text = _workflow_text()

    assert "feature/v04-r5b-recovery-transfer" in text
    assert "docs/validation/V04_R5B_RUN_AUTHORIZED" in text
    assert "matrix:" in text
    assert "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]" in text
    assert "fail-fast: false" in text
    assert "max-parallel: 16" in text
    assert "aggregate:" in text
    assert "aggregate_v04_r5b.py" in text
    assert "actions/download-artifact@v4" in text
    assert "if: always()" in text


def test_r5b_precheck_does_not_execute_outcome_commands():
    text = _workflow_text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "python scripts/run_v04_r5b_replicate.py" not in precheck
    assert "python scripts/aggregate_v04_r5b.py" not in precheck
