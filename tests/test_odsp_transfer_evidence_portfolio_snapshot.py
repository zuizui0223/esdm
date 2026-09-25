from __future__ import annotations

import hashlib
import json
from pathlib import Path

from esdm.transfer import (
    build_transfer_evidence_portfolio,
    load_transfer_source_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ODSP_TRANSFER_SOURCE_REGISTRY_V1.json"
SNAPSHOT = ROOT / "ODSP_TRANSFER_EVIDENCE_PORTFOLIO_V1.json"
RECEIPT = ROOT / "ODSP_TRANSFER_EVIDENCE_PORTFOLIO_RECEIPT_V1.json"


def test_frozen_portfolio_snapshot_matches_live_builder_exactly():
    sources = load_transfer_source_registry(REGISTRY)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rebuilt = build_transfer_evidence_portfolio(
        repository_root=ROOT,
        registry_id=registry["registry_id"],
        sources=sources,
    ).as_dict()
    frozen = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    assert rebuilt == frozen


def test_frozen_portfolio_file_hash_and_fingerprint_are_pinned():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    frozen = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    observed_sha = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()

    assert observed_sha == receipt["portfolio_sha256"]
    assert frozen["fingerprint"] == receipt["portfolio_fingerprint"]
    assert receipt["generation"]["workflow_run_id"] == 36106976869
    assert receipt["generation"]["artifact_id"] == 10851860634
    assert receipt["generation"]["artifact_digest"] == (
        "sha256:e03e438f916d902acc1aea2419b04272f7958681b9f861294b1e63ef7a5080dc"
    )


def test_frozen_portfolio_receipt_records_nonranking_boundary():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    assert receipt["contents"]["item_count"] == 4
    assert receipt["contents"]["parallel_family_count"] == 1
    assert receipt["contents"]["all_population_status_positive"] is True
    assert receipt["boundaries"]["ranking_authorized"] is False
    assert receipt["boundaries"]["global_information_ladder_authorized"] is False
    assert receipt["boundaries"]["lattice_inference_created"] is False
    assert receipt["boundaries"]["eog_consumption_authorized"] is False
    assert receipt["boundaries"]["n4_action_authorized"] is False
    assert receipt["boundaries"]["n4_survey_action_owner"] == "ACSP"
