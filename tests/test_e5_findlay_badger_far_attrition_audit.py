"""Post-result receipt-only Findlay BADGER exclusion reconciliation.

Reads *only previously frozen ESDM JSON receipts and local source-code text*;
never opens the original biological CSVs or reruns the one-shot analysis.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "replication"


def read_receipt(filename: str) -> dict:
    return json.loads((EVIDENCE / filename).read_text(encoding="utf-8"))


def test_frozen_stage_mismatch_exactly_matches_the_single_invalid_capture():
    frozen = read_receipt("E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json")
    cells = {(row["species"], row["distance_bin"]): row for row in frozen["stage_cells"]}
    assert len(cells) == 6
    gaps = {
        key: row["triggered_reference_passes"]
        - row["registration_eligible_triggered_rows"]
        for key, row in cells.items()
    }
    assert gaps == {
        ("BADGER", "near_le_1m"): 0,
        ("BADGER", "mid_1_to_3m"): 0,
        ("BADGER", "far_gt_3m"): 1,
        ("FOX", "near_le_1m"): 0,
        ("FOX", "mid_1_to_3m"): 0,
        ("FOX", "far_gt_3m"): 0,
    }
    assert sum(x["triggered_reference_passes"] for x in cells.values()) == 340
    assert sum(x["registration_eligible_triggered_rows"] for x in cells.values()) == 339
    qc = frozen["exclusion_counts"]
    assert qc["registration"]["invalid_capture"] == 1
    assert qc["trigger"]["all_rows"] == qc["registration"]["all_rows"] == 881
    assert sum(qc["registration"][k] for k in (
        "eligible_rows", "not_lateral", "invalid_distance",
        "registration_untriggered_excluded", "invalid_capture"
    )) == 881


def test_pinned_source_row_order_supports_but_does_not_prove_passage_identity():
    linkage = read_receipt("E5_FINDLAY_PASSAGE_LINKAGE_FORENSIC_RECEIPT.json")
    c = linkage["frozen_comparison"]
    assert c["trigger_csv_rows"] == c["registration_csv_rows"] == 881
    assert c["same_row_order_shared_covariate_signatures"] == 881
    assert c["same_row_order_trigger_flags"] == 881
    assert c["identical_but_ambiguous_duplicate_fingerprint_rows"] == 351
    assert c["internal_unique_passage_ID_linkage_verified"] is False
    assert linkage["interpretation"]["actual_mismatch_k_observed_or_bounded"] is False


def test_original_findlay_and_e5_decisions_remain_frozen():
    f = read_receipt("E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json")
    assert f["near_vs_far"]["BADGER"]["status"] == "COHORT_NONCOMPARABLE"
    assert f["near_vs_far"]["BADGER"]["mismatch_reason_not_proven"] is True
    assert f["near_vs_far"]["BADGER"]["composite_far_vs_near_not_estimated"] is True
    assert f["gate_boundary"]["original_standard_E5_qualified"] == 0
    assert f["gate_boundary"]["original_standard_E5_G4_passed"] is False
    original_parser = (ROOT / "scripts" / "run_e5_findlay_pass_stage_descriptive.py").read_text(encoding="utf-8")
    assert 'qc["invalid_capture"] += 1' in original_parser
    assert 'capture = parse_binary(row.get("CAPTURE", ""))' in original_parser
