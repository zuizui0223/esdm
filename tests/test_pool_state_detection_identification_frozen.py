"""Prevent outcome/qualification drift in committed deterministic certificate."""
from pathlib import Path
import json

from scripts.audit_pool_state_detection_identification import certificate


def test_frozen_identification_audit_result_is_generated_byte_for_byte():
    path = Path(__file__).resolve().parents[1] / 'docs' / 'replication' / 'POOL_STATE_DETECTION_IDENTIFICATION_RESULT.json'
    expected = json.dumps(certificate(), indent=2, sort_keys=True) + '\n'
    assert path.read_text(encoding='utf-8') == expected


def test_no_empirical_claim_promotion_or_changed_old_runs():
    result = certificate()
    assert result['data_boundary']['wildlife_rows_opened'] is False
    assert result['data_boundary']['prior_empirical_fits_changed'] is False
    assert result['data_boundary']['independent_calibration_obtained'] is False
    assert result['decision']['E5_G4_qualified_by_this_proof'] is False
    assert result['decision']['eSDM_superiority_claim_authorized'] is False
