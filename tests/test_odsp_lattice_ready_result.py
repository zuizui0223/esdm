from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from esdm.transfer import (
    ODSPLatticeInformationBlock,
    ODSPLatticeNode,
    build_odsp_lattice_ready_bundle,
    required_odsp_lattice_subsets,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "ODSP_LATTICE_READY_RESULT_PROTOCOL_V1.json"


def _records():
    return [
        {"replicate": 0, "base": -2.0, "a": -1.7, "b": -1.8, "ab": -1.3},
        {"replicate": 1, "base": -2.1, "a": -1.9, "b": -1.7, "ab": -1.2},
    ]


def test_two_block_complete_lattice_serializes_four_absolute_score_nodes():
    bundle = build_odsp_lattice_ready_bundle(
        result_id="future-two-block",
        base_information=("suitability",),
        information_blocks=(
            ODSPLatticeInformationBlock("activity", ("activity",)),
            ODSPLatticeInformationBlock("state", ("state",)),
        ),
        nodes=(
            ODSPLatticeNode((), "base"),
            ODSPLatticeNode(("activity",), "a"),
            ODSPLatticeNode(("state",), "b"),
            ODSPLatticeNode(("activity", "state"), "ab"),
        ),
        records=_records(),
        group_field="replicate",
        score_kind="log",
        score_name="mean_heldout_log_predictive_density",
        score_unit="nats_per_context",
    )

    assert bundle.manifest["validation"]["node_count"] == 4
    assert bundle.manifest["validation"]["directed_edge_count"] == 4
    assert bundle.manifest["boundary"]["runs_odsp_inference"] is False
    assert bundle.rows[0]["score__base"] == pytest.approx(-2.0)
    assert bundle.rows[0]["score__activity"] == pytest.approx(-1.7)
    assert bundle.rows[0]["score__state"] == pytest.approx(-1.8)
    assert bundle.rows[0]["score__activity__state"] == pytest.approx(-1.3)


def test_three_block_complete_lattice_requires_eight_nodes_and_twelve_edges():
    blocks = (
        ODSPLatticeInformationBlock("movement", ("movement",)),
        ODSPLatticeInformationBlock("activity", ("activity",)),
        ODSPLatticeInformationBlock("interaction", ("interaction",)),
    )
    subsets = (
        (),
        ("movement",),
        ("activity",),
        ("interaction",),
        ("movement", "activity"),
        ("movement", "interaction"),
        ("activity", "interaction"),
        ("movement", "activity", "interaction"),
    )
    record = {"replicate": 0}
    nodes = []
    for index, subset in enumerate(subsets):
        field = f"s{index}"
        record[field] = -2.0 + 0.1 * index
        nodes.append(ODSPLatticeNode(subset, field))

    bundle = build_odsp_lattice_ready_bundle(
        result_id="future-three-block",
        base_information=("environment",),
        information_blocks=blocks,
        nodes=tuple(nodes),
        records=(record,),
        group_field="replicate",
        score_kind="log",
        score_name="mean_heldout_log_predictive_density",
        score_unit="nats_per_context",
    )
    assert bundle.manifest["validation"]["node_count"] == 8
    assert bundle.manifest["validation"]["directed_edge_count"] == 12


def test_missing_subset_fails_closed_and_r5b_cannot_be_retrofit_to_lattice():
    with pytest.raises(ValueError, match="complete Boolean subset lattice"):
        build_odsp_lattice_ready_bundle(
            result_id="incomplete-r5b-like",
            base_information=("suitability",),
            information_blocks=(
                ODSPLatticeInformationBlock("activity", ("activity",)),
                ODSPLatticeInformationBlock("state", ("state",)),
            ),
            nodes=(
                ODSPLatticeNode(("activity",), "a"),
                ODSPLatticeNode(("state",), "b"),
                ODSPLatticeNode(("activity", "state"), "ab"),
            ),
            records=_records(),
            group_field="replicate",
            score_kind="log",
            score_name="mean_heldout_log_predictive_density",
            score_unit="nats_per_context",
        )


def test_four_or_more_blocks_are_not_authorized_in_v1():
    blocks = tuple(
        ODSPLatticeInformationBlock(name, (name,))
        for name in ("a", "b", "c", "d")
    )
    with pytest.raises(ValueError, match="exactly two or three"):
        build_odsp_lattice_ready_bundle(
            result_id="too-large",
            base_information=("base",),
            information_blocks=blocks,
            nodes=(),
            records=_records(),
            group_field="replicate",
            score_kind="log",
            score_name="score",
            score_unit="unit",
        )


def test_blocks_must_be_variable_disjoint_from_base_and_each_other():
    with pytest.raises(ValueError, match="mutually disjoint"):
        build_odsp_lattice_ready_bundle(
            result_id="overlap",
            base_information=("environment",),
            information_blocks=(
                ODSPLatticeInformationBlock("a", ("environment",)),
                ODSPLatticeInformationBlock("b", ("state",)),
            ),
            nodes=(),
            records=_records(),
            group_field="replicate",
            score_kind="log",
            score_name="score",
            score_unit="unit",
        )


def test_each_node_requires_its_own_absolute_score_field():
    with pytest.raises(ValueError, match="own absolute score field"):
        build_odsp_lattice_ready_bundle(
            result_id="duplicate-field",
            base_information=("suitability",),
            information_blocks=(
                ODSPLatticeInformationBlock("activity", ("activity",)),
                ODSPLatticeInformationBlock("state", ("state",)),
            ),
            nodes=(
                ODSPLatticeNode((), "base"),
                ODSPLatticeNode(("activity",), "a"),
                ODSPLatticeNode(("state",), "a"),
                ODSPLatticeNode(("activity", "state"), "ab"),
            ),
            records=_records(),
            group_field="replicate",
            score_kind="log",
            score_name="score",
            score_unit="unit",
        )


def test_protocol_contract_forbids_retroactive_and_cross_programme_lattices():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["current_odsp_scope"]["supported_information_block_counts"] == [2, 3]
    assert contract["current_odsp_scope"]["four_or_more_blocks_authorized"] is False
    assert contract["r5b_boundary"]["existing_parallel_activity_state_results_promoted_to_lattice"] is False
    assert contract["r5b_boundary"]["synthetic_missing_base_score_allowed"] is False
    assert contract["output_boundary"]["protocol_changes_transfer_source_registry"] is False
    assert contract["output_boundary"]["protocol_authorizes_cross_programme_lattice"] is False
    assert contract["output_boundary"]["protocol_authorizes_global_information_ladder"] is False
    assert contract["output_boundary"]["protocol_authorizes_eog_consumption"] is False



def test_lattice_ready_rejects_negative_sample_weight():
    records = [
        {
            "replicate": 0,
            "weight": -1.0,
            "base": -2.0,
            "a": -1.7,
            "b": -1.8,
            "ab": -1.3,
        }
    ]
    with pytest.raises(ValueError, match="weights must be non-negative"):
        build_odsp_lattice_ready_bundle(
            result_id="negative-weight",
            base_information=("suitability",),
            information_blocks=(
                ODSPLatticeInformationBlock("activity", ("activity",)),
                ODSPLatticeInformationBlock("state", ("state",)),
            ),
            nodes=(
                ODSPLatticeNode((), "base"),
                ODSPLatticeNode(("activity",), "a"),
                ODSPLatticeNode(("state",), "b"),
                ODSPLatticeNode(("activity", "state"), "ab"),
            ),
            records=records,
            group_field="replicate",
            weight_field="weight",
            score_kind="log",
            score_name="score",
            score_unit="unit",
        )


def test_lattice_block_names_cannot_collide_after_column_normalization():
    blocks = (
        ODSPLatticeInformationBlock("A-B", ("x",)),
        ODSPLatticeInformationBlock("A_B", ("y",)),
    )
    nodes = (
        ODSPLatticeNode((), "base"),
        ODSPLatticeNode(("A-B",), "a"),
        ODSPLatticeNode(("A_B",), "b"),
        ODSPLatticeNode(("A-B", "A_B"), "ab"),
    )
    with pytest.raises(ValueError, match="collide after score-column normalization"):
        build_odsp_lattice_ready_bundle(
            result_id="column-collision",
            base_information=("environment",),
            information_blocks=blocks,
            nodes=nodes,
            records=_records(),
            group_field="replicate",
            score_kind="log",
            score_name="score",
            score_unit="unit",
        )



def test_required_subset_roster_can_be_frozen_before_outcome_scoring():
    blocks = (
        ODSPLatticeInformationBlock("movement", ("movement",)),
        ODSPLatticeInformationBlock("activity", ("activity",)),
        ODSPLatticeInformationBlock("interaction", ("interaction",)),
    )
    assert required_odsp_lattice_subsets(
        base_information=("environment",),
        information_blocks=blocks,
    ) == (
        (),
        ("movement",),
        ("activity",),
        ("interaction",),
        ("movement", "activity"),
        ("movement", "interaction"),
        ("activity", "interaction"),
        ("movement", "activity", "interaction"),
    )



def test_lattice_ready_bundle_writes_deterministic_csv_and_manifest(tmp_path: Path):
    records = [
        {
            "replicate": 0,
            "block": "fold-a",
            "base": -2.0,
            "a": -1.7,
            "b": -1.8,
            "ab": -1.3,
        },
        {
            "replicate": 1,
            "block": "fold-b",
            "base": -2.1,
            "a": -1.9,
            "b": -1.7,
            "ab": -1.2,
        },
    ]
    bundle = build_odsp_lattice_ready_bundle(
        result_id="write-roundtrip",
        base_information=("suitability",),
        information_blocks=(
            ODSPLatticeInformationBlock("activity", ("activity",)),
            ODSPLatticeInformationBlock("state", ("state",)),
        ),
        nodes=(
            ODSPLatticeNode((), "base"),
            ODSPLatticeNode(("activity",), "a"),
            ODSPLatticeNode(("state",), "b"),
            ODSPLatticeNode(("activity", "state"), "ab"),
        ),
        records=records,
        group_field="replicate",
        validation_block_field="block",
        score_kind="log",
        score_name="mean_heldout_log_predictive_density",
        score_unit="nats_per_context",
    )
    written = bundle.write(tmp_path)

    manifest = json.loads(Path(written["manifest"]).read_text(encoding="utf-8"))
    with Path(written["scores"]).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert manifest["validation"]["validation_block_column"] == "validation_block"
    assert manifest["row_count"] == 2
    assert rows[0]["validation_block"] == "fold-a"
    assert float(rows[0]["score__base"]) == pytest.approx(-2.0)
    assert float(rows[0]["score__activity__state"]) == pytest.approx(-1.3)
