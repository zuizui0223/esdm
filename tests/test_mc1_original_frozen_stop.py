"""Original consumed MC1 source-stop receipt and no-reexecution regression tests."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/'docs/replication/MC1_COYOTE_IMAGE_RESULT_FROZEN.json'
WORKFLOW=ROOT/'.github/workflows/mc1-coyote-image-quality-once.yml'

def test_original_mc1_result_sha_and_length():
    b=RECEIPT.read_bytes()
    assert len(b)==225
    assert hashlib.sha256(b).hexdigest()=='e7481cdc3848817208e18f1568422bc1a036ac5c9222f7695489c10b8f7744ce'
    assert b.endswith(b'\n')

def test_no_mc1_biological_result_and_original_e5_invariant():
    o=json.loads(RECEIPT.read_text())
    assert o['status']=='MC1_TERMINAL_SOURCE_OR_SCHEMA_STOP'
    assert o['reason']=='RESPONSE_SCHEMA_STOP: invalid calendar year'
    assert o['biological_prediction_evaluated'] is False
    assert o['original_E5_qualified_count_unchanged']==0
    assert 'primary' not in o and 'support' not in o

def test_mc1_biological_source_workflow_retired():
    w=WORKFLOW.read_text()
    assert 'if: false # TERMINAL run 44525869485' in w
