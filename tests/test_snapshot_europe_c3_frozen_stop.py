"""One-shot response-free regression checks against original published stop receipt."""
from pathlib import Path
import json

BASE=Path(__file__).resolve().parents[1]


def test_original_terminal_receipt_exactly_marks_no_biological_opening():
    r=json.loads((BASE/'docs/replication/C3_CROSSYEAR_COUNTRY_PRIOR_FROZEN_RESULT.json').read_text())
    assert r['status']=='RESPONSE_SCHEMA_STOP'
    assert r['stop_reason']=='RESPONSE_SCHEMA_STOP: physical camera mapped to conflicting country/array'
    assert r['source_animal_response_may_have_been_opened'] is False
    assert r['ecological_transfer_test_completed'] is False
    assert r['execution']['run_id']=='44252651086'
    assert r['source']['file_id']==345505
    assert 'primary' not in r
    assert r['prior_ecological_results_unchanged'] is True


def test_consumed_c3_workflow_is_immutable_pr_and_head_guarded():
    yml=(BASE/'.github/workflows/snapshot-europe-c3-country-prior-once.yml').read_text()
    assert 'github.event.pull_request.number == 238' in yml
    assert "github.event.pull_request.head.sha == 'f300e7650fddcac2cadedd00f97a072fce63c90f'" in yml
    assert 'github.run_attempt == 1' in yml
    assert 'workflow_dispatch:' not in yml
    assert 'schedule:' not in yml
