from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07k-local-repilot-once.yml"
    ).read_text(encoding="utf-8")


def test_v07k_workflow_has_two_worlds_and_sixteen_replicates_each():
    text = _text()

    assert "world: [transfer_positive, reversal]" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text


def test_v07k_outcome_requires_authorization_and_cannot_be_cancelled():
    text = _text()

    assert "docs/validation/V07K_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    assert "cancel-in-progress: false" in text


def test_v07k_aggregate_is_fail_closed():
    text = _text()

    assert '"status":"INFRASTRUCTURE_BLOCKED"' in text
    assert "if: always()" in text
