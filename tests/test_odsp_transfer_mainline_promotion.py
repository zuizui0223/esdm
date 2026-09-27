from __future__ import annotations

import json
from pathlib import Path

from esdm.transfer import (
    build_transfer_evidence_portfolio_v2,
    exportable_transfer_sources,
    load_transfer_source_registry,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ODSP_TRANSFER_SOURCE_REGISTRY_V1.json"
TERMINAL = ROOT / "docs" / "empirical" / "PROGRAMME_TERMINAL_STATUS.json"


def test_mainline_transfer_registry_is_self_contained():
    sources = load_transfer_source_registry(REGISTRY)

    assert len(sources) == 14
    for source in sources:
        assert (ROOT / source.frozen_receipt).is_file()

    exportable = exportable_transfer_sources(sources)
    assert {source.source_id for source in exportable} == {
        "v04_r5b_activity",
        "v04_r5b_state",
        "v06a_static_accessibility",
        "v07b_dynamic_occupancy",
    }
    for source in exportable:
        assert source.validated_integration_receipt is not None
        assert (ROOT / source.validated_integration_receipt).is_file()


def test_mainline_can_rebuild_complete_transfer_ledger_without_feature_branch():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = load_transfer_source_registry(REGISTRY)
    ledger = build_transfer_evidence_portfolio_v2(
        repository_root=ROOT,
        registry_id=registry["registry_id"],
        sources=sources,
    )

    summary = ledger.coverage_summary
    assert summary["registry_source_count"] == 14
    assert summary["validated_item_count"] == 4
    assert summary["excluded_source_count"] == 10
    assert summary["scientific_fail_count"] == 2
    assert summary["every_registry_source_accounted_for"] is True


def test_transfer_promotion_does_not_reopen_empirical_terminal():
    terminal = json.loads(TERMINAL.read_text(encoding="utf-8"))

    assert terminal["status"] == "EMPIRICAL_ENDPOINT_CONSUMED_STOP"
    empirical = terminal["first_empirical_endpoint"]
    assert empirical["terminal_status"] == "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY"
    assert empirical["model_fits"] == 0
    assert empirical["heldout_scores"] == 0
    assert empirical["response_consumed"] is True

    stop = terminal["development_stop_rule"]
    assert stop["replacement_first_empirical_candidate_authorized"] is False
    assert stop["post_response_parser_repair_authorized"] is False
    assert stop["post_response_model_retuning_authorized"] is False


def test_mainline_transfer_ledger_preserves_failures_as_unsupported_not_zero():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = load_transfer_source_registry(REGISTRY)
    ledger = build_transfer_evidence_portfolio_v2(
        repository_root=ROOT,
        registry_id=registry["registry_id"],
        sources=sources,
    )
    excluded = {item.source_id: item for item in ledger.excluded_sources}

    interaction = excluded["v05f_directed_interaction_replication"]
    assert interaction.registry_status == "scientific_fail_not_exportable"
    assert interaction.numeric_transfer_value_authorized is False
    assert interaction.unsupported_not_zero is True
