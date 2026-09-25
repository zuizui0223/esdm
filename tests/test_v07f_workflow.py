from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07f-misspecified-resolution-once.yml"
    ).read_text(encoding="utf-8")


def test_v07f_workflow_has_two_worlds_and_sixteen_replicates_each():
    text = _text()

    assert "world: [dynamic_like, static_like]" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text
    assert "--world ${{ matrix.world }}" in text
    assert "--replicate ${{ matrix.replicate }}" in text


def test_v07f_outcome_requires_explicit_authorization_and_cannot_be_cancelled_by_cleanup():
    text = _text()

    assert "docs/validation/V07F_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    assert "cancel-in-progress: false" in text
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  qualification:\n", 1)[0]
    assert "run_v07f_qualification.py" not in precheck
    assert "run_v07f_replicate.py" not in precheck
    assert "aggregate_v07f.py" not in precheck


def test_v07f_aggregate_is_fail_closed():
    text = _text()

    assert '"status":"INFRASTRUCTURE_BLOCKED"' in text
    assert "if: always()" in text
