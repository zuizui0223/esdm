from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e5-sumatra-s1-inventory-once.yml"


def test_sumatra_inventory_workflow_is_pure_marker_and_response_blind():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/sumatra-mesopredator-s1-inventory-v1" in text
    assert "E5_SUMATRA_S1_INVENTORY_AUTHORIZED.json" in text
    assert "da628205f2cded73d93646e96ad7456263f2e733" in text
    assert "10.1371%2Fjournal.pone.0202876.s001" in text
    assert "workflow_dispatch" not in text
    assert "data_member_opening_authorized" in text
    assert "focal_response_opening_authorized" in text
    assert "inventory_e5_sumatra_s1.py" in text
