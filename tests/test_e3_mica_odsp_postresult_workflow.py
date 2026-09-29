from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e3-mica-odsp-postresult-audit.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_e3_postresult_workflow_has_no_manual_dispatch():
    text = _text()

    assert "workflow_dispatch" not in text
    assert "docs/replication/E3_MICA_REDUCED_FROZEN_RESULT.json" in text
    assert "pull_request:" in text
    assert "push:" in text


def test_e3_postresult_workflow_routes_sampling_stop_without_odsp():
    text = _text()

    assert "audit_authorized" in text
    assert "E3_EXPLORATORY_RESULT" in text
    assert "sampling_gate_passed" in text
    assert "NOT_AUTHORIZED_SOURCE_RESULT" in text
    assert '"odsp_executed": False' in text


def test_e3_postresult_workflow_runs_two_parallel_odsp_audits_only_after_frozen_receipt():
    text = _text()

    assert "--contract build/odsp/activity/endpoint.json" in text
    assert "--contract build/odsp/state/endpoint.json" in text
    assert "summarize_e3_mica_odsp_audit.py" in text
    assert "build/E3_MICA_ODSP_AUDIT_RESULT_V1.json" in text
    assert "0bd83e1ebb372c48839654ab0e42124fe37b8faf" in text


def test_e3_postresult_workflow_does_not_create_n3_handoff_or_run_lattice():
    text = _text()

    assert "build_population_transfer_value_handoff" not in text
    assert "odsp experimental" not in text
    assert '"odsp_lattice_authorized": False' in text
    assert "audit_information_lattice" not in text
    assert "certify_information_lattice" not in text
    assert "build_odsp_lattice_ready_bundle" not in text
    assert "lattice_scores.csv" not in text
