"""Regression guard for the original consumed Clare Dryad HTTP 401 stop."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs/replication/CLARE_STATION_METHOD_FROZEN_RESULT.json"
WORKFLOW = ROOT / ".github/workflows/clare-station-conditioned-camera-tracks-once.yml"

def test_original_stop_receipt_exact_bytes():
    b = RECEIPT.read_bytes()
    assert len(b) == 135
    assert hashlib.sha256(b).hexdigest() == "66b2f0d7a95bc17a7965ede5de1710bfaeeb06ef189c0301df90f4890d0aa6cb"
    assert b.endswith(b"\n")
    assert json.loads(b)["status"] == "TRANSPORT_OR_SOURCE_STOP"

def test_no_clare_ecological_effect_or_promotion():
    o = json.loads(RECEIPT.read_text())
    assert o["biological_effect_evaluated"] is False
    assert o["original_E5_qualified_count_unchanged"] == 0
    assert not any(k in o for k in ("delta_per_observed_paired_occasion","support","station_bootstrap_95_interval"))

def test_original_one_shot_workflow_retired():
    s = WORKFLOW.read_text()
    assert "if: false # TERMINAL original run 44477943475 HTTP 401" in s
    assert "44477943475" in s
