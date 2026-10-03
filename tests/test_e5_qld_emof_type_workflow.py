from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e5-qld-emof-type-once.yml"


def test_qld_emof_workflow_is_pure_marker_and_value_blind():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-emof-type-v1" in text
    assert "E5_QLD_EMOF_TYPE_AUTHORIZED.json" in text
    assert "85f4d67420ce613a3128e595d23a9e55ba03f043" in text
    assert "f830085a5c1ad6ec9e130169188049670ffa83372a08a02924aa6190554de34e" in text
    assert "workflow_dispatch" not in text
    assert "measurementvalue_decode_authorized" in text
    assert "occurrence_opening_authorized" in text
    assert "precheck_e5_qld_emof_type.py" in text
