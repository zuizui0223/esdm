"""Inspect only the frozen 276-byte aggregate result and consumed-workflow guard."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'docs/replication/D1_CROSSCOUNTRY_CAMERA_DETECTION_ZONE_FROZEN_RESULT.json'
WORKFLOW = ROOT / '.github/workflows/d1-crosscountry-detection-zone-once.yml'


def test_unmodified_original_actions_artifact_json():
    raw = RESULT.read_bytes()
    assert len(raw) == 276
    assert hashlib.sha256(raw).hexdigest() == '8740e8ad80d55391aba615e45d8559cbeae073cea14cf9df24189bed748e55f6'
    assert json.loads(raw)['status'] == 'SCHEMA_STOP'


def test_stop_not_reinterpreted_as_negative_predictive_result():
    obj = json.loads(RESULT.read_text())
    assert obj['error'] == 'SCHEMA_STOP: source zone ID blank or duplicated'
    assert obj['model_fitted'] is False
    assert obj['source_response_rows_exported'] is False
    assert not any(k in obj for k in ('primary','score','heldout_mae','country_fold_summaries'))


def test_consumed_workflow_has_no_path_to_repeat_source_opening():
    source=WORKFLOW.read_text()
    assert "if: false # TERMINAL" in source
    assert 'D1_COUNTRY_TRANSFER_TECHNICAL_RESTART.json' in source
    assert 'github.run_attempt' not in source.split('if: false # TERMINAL',1)[1].split('\n',1)[0]
