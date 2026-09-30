from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e4-mica-odsp-postresult-audit.yml"
)


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def test_e4_odsp_workflow_uses_frozen_source_and_pinned_odsp():
    text = _text()

    assert "run-id: 36622802225" in text
    assert "e4-mica-sparse-result-36622802225" in text
    assert (
        "34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2"
        in text
    )
    assert "0bd83e1ebb372c48839654ab0e42124fe37b8faf" in text
    assert "odsp transfer" in text


def test_e4_odsp_workflow_runs_two_parallel_not_ordered_audits():
    text = _text()

    assert "build/odsp/activity/endpoint.json" in text
    assert "build/odsp/state/endpoint.json" in text
    assert "summarize_e4_mica_odsp_audit.py" in text
    assert "E4_MICA_ODSP_AUDIT_RESULT_V1.json" in text


def test_e4_odsp_workflow_has_no_fit_or_result_mutation_path():
    text = _text()

    for forbidden in (
        "fit_e4_mica_sparse",
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "workflow_dispatch",
        "E4_MICA_SPARSE_FIT_AUTHORIZED",
    ):
        assert forbidden not in text
