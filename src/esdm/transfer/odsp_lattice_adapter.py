"""Serialize future eSDM results as complete ODSP information-lattice score tables.

This module does not run lattice inference. It validates that a future eSDM
result has already preserved every absolute held-out score needed for a complete
Boolean subset lattice, on the same held-out rows under one score currency.

Current v1 is intentionally limited to two or three unordered information
blocks, matching the presently qualified ODSP complete-lattice family sizes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import csv
import itertools
import json
import math
from pathlib import Path
import re
from typing import Mapping, Sequence


_SAFE = re.compile(r"[^A-Za-z0-9_]+")


@dataclass(frozen=True, slots=True)
class ODSPLatticeInformationBlock:
    name: str
    variables: tuple[str, ...]

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        variables = tuple(str(value).strip() for value in self.variables)
        if not name:
            raise ValueError("lattice block name must be non-empty")
        if not variables or any(not value for value in variables):
            raise ValueError(f"lattice block {name!r} must contain non-empty variables")
        if len(set(variables)) != len(variables):
            raise ValueError(f"lattice block {name!r} contains duplicate variables")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "variables", variables)


@dataclass(frozen=True, slots=True)
class ODSPLatticeNode:
    blocks: tuple[str, ...]
    source_score_field: str

    def __post_init__(self) -> None:
        blocks = tuple(str(value).strip() for value in self.blocks)
        field = str(self.source_score_field).strip()
        if any(not value for value in blocks):
            raise ValueError("lattice node block labels must be non-empty")
        if len(set(blocks)) != len(blocks):
            raise ValueError("lattice node block labels must be unique")
        if not field:
            raise ValueError("source_score_field must be non-empty")
        object.__setattr__(self, "blocks", blocks)
        object.__setattr__(self, "source_score_field", field)


@dataclass(frozen=True, slots=True)
class ODSPLatticeReadyBundle:
    rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]

    def write(
        self,
        directory: str | Path,
        *,
        scores_filename: str = "lattice_scores.csv",
        manifest_filename: str = "lattice_manifest.json",
    ) -> dict[str, str]:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        score_path = root / scores_filename
        manifest_path = root / manifest_filename

        if not self.rows:
            raise ValueError("lattice-ready bundle contains no rows")
        fieldnames = list(self.rows[0])
        with score_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)
        manifest_path.write_text(
            json.dumps(self.manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return {
            "scores": str(score_path),
            "manifest": str(manifest_path),
        }


def _mapping(record: object) -> Mapping[str, object]:
    if isinstance(record, Mapping):
        return record
    if is_dataclass(record):
        return asdict(record)
    raise ValueError("records must be mappings or dataclass instances")


def _finite(value: object, *, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _canonical_subset(values: Sequence[str], order: tuple[str, ...]) -> tuple[str, ...]:
    local = tuple(str(value).strip() for value in values)
    if any(not value for value in local) or len(set(local)) != len(local):
        raise ValueError("lattice node block labels must be unique non-empty strings")
    unknown = sorted(set(local) - set(order))
    if unknown:
        raise ValueError(f"lattice node contains unknown blocks: {unknown!r}")
    chosen = set(local)
    return tuple(name for name in order if name in chosen)


def _all_subsets(order: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for size in range(len(order) + 1):
        rows.extend(tuple(combo) for combo in itertools.combinations(order, size))
    return tuple(rows)


def _node_column(subset: tuple[str, ...]) -> str:
    if not subset:
        return "score__base"
    normalized = "__".join(
        _SAFE.sub("_", value).strip("_").lower()
        for value in subset
    )
    if not normalized:
        raise ValueError("lattice node names cannot normalize to an empty column")
    return f"score__{normalized}"


def _validate_blocks(
    base_information: Sequence[str],
    blocks: Sequence[ODSPLatticeInformationBlock],
) -> tuple[tuple[str, ...], tuple[ODSPLatticeInformationBlock, ...]]:
    base = tuple(str(value).strip() for value in base_information)
    if not base or any(not value for value in base):
        raise ValueError("base_information must contain non-empty labels")
    if len(set(base)) != len(base):
        raise ValueError("base_information labels must be unique")

    block_rows = tuple(blocks)
    if len(block_rows) not in {2, 3}:
        raise ValueError(
            "ODSP lattice-ready result v1 supports exactly two or three unordered information blocks"
        )
    names = [row.name for row in block_rows]
    if len(set(names)) != len(names):
        raise ValueError("lattice block names must be unique")

    seen = set(base)
    for row in block_rows:
        overlap = seen & set(row.variables)
        if overlap:
            raise ValueError(
                "base information and lattice-block variables must be mutually disjoint; "
                f"overlap={tuple(sorted(overlap))!r}"
            )
        seen.update(row.variables)
    return base, block_rows


def build_odsp_lattice_ready_bundle(
    *,
    result_id: str,
    base_information: Sequence[str],
    information_blocks: Sequence[ODSPLatticeInformationBlock],
    nodes: Sequence[ODSPLatticeNode],
    records: Sequence[object],
    group_field: str,
    score_kind: str,
    score_name: str,
    score_unit: str,
    row_id_field: str | None = None,
    validation_block_field: str | None = None,
    weight_field: str | None = None,
    source_schema: str | None = None,
    source_git_sha: str | None = None,
    group_semantics: str | None = None,
) -> ODSPLatticeReadyBundle:
    """Build a complete-subset score table for future ODSP lattice audits."""

    result_id = str(result_id).strip()
    if not result_id:
        raise ValueError("result_id must be non-empty")
    score_kind = str(score_kind).strip()
    score_name = str(score_name).strip()
    score_unit = str(score_unit).strip()
    if score_kind not in {"log", "other_proper"}:
        raise ValueError("score_kind must be 'log' or 'other_proper'")
    if not score_name or not score_unit:
        raise ValueError("score_name and score_unit must be non-empty")

    base, block_rows = _validate_blocks(base_information, information_blocks)
    block_order = tuple(row.name for row in block_rows)
    expected = set(_all_subsets(block_order))

    node_map: dict[tuple[str, ...], ODSPLatticeNode] = {}
    fields: set[str] = set()
    for node in nodes:
        subset = _canonical_subset(node.blocks, block_order)
        if subset in node_map:
            raise ValueError(f"duplicate lattice node for subset {subset!r}")
        if node.source_score_field in fields:
            raise ValueError("every lattice node must retain its own absolute score field")
        node_map[subset] = node
        fields.add(node.source_score_field)

    missing = sorted(expected - set(node_map), key=lambda value: (len(value), value))
    extra = sorted(set(node_map) - expected, key=lambda value: (len(value), value))
    if missing or extra:
        raise ValueError(
            "complete Boolean subset lattice is required; "
            f"missing={missing!r}, extra={extra!r}"
        )

    source_rows = tuple(_mapping(record) for record in records)
    if not source_rows:
        raise ValueError("records must be non-empty")

    rows: list[dict[str, object]] = []
    seen_row_ids: set[str] = set()
    ordered_subsets = _all_subsets(block_order)
    column_by_subset = {
        subset: _node_column(subset) for subset in ordered_subsets
    }
    if len(set(column_by_subset.values())) != len(column_by_subset):
        raise ValueError(
            "lattice block names collide after score-column normalization"
        )

    for index, source in enumerate(source_rows):
        if group_field not in source:
            raise ValueError(f"record {index} is missing group_field {group_field!r}")
        group = str(source[group_field]).strip()
        if not group:
            raise ValueError(f"record {index} has empty group")

        if row_id_field is None:
            row_id = f"row-{index:04d}"
        else:
            if row_id_field not in source:
                raise ValueError(f"record {index} is missing row_id_field {row_id_field!r}")
            row_id = str(source[row_id_field]).strip()
        if not row_id or row_id in seen_row_ids:
            raise ValueError("row ids must be unique non-empty strings")
        seen_row_ids.add(row_id)

        row: dict[str, object] = {
            "row_id": row_id,
            "group": group,
            "weight": 1.0 if weight_field is None else _finite(
                source.get(weight_field), name=f"record[{index}].{weight_field}"
            ),
        }
        if validation_block_field is not None:
            if validation_block_field not in source:
                raise ValueError(
                    f"record {index} is missing validation_block_field "
                    f"{validation_block_field!r}"
                )
            block_value = str(source[validation_block_field]).strip()
            if not block_value:
                raise ValueError("validation block values must be non-empty")
            row["validation_block"] = block_value

        for subset in ordered_subsets:
            field = node_map[subset].source_score_field
            if field not in source:
                raise ValueError(
                    f"record {index} is missing absolute lattice score field {field!r}"
                )
            row[column_by_subset[subset]] = _finite(
                source[field], name=f"record[{index}].{field}"
            )
        rows.append(row)

    manifest = {
        "schema": "esdm.odsp_lattice_ready_bundle.v1",
        "result_id": result_id,
        "source_schema": source_schema,
        "source_git_sha": source_git_sha,
        "group_semantics": group_semantics,
        "row_count": len(rows),
        "base_information": list(base),
        "information_blocks": [
            {"name": block.name, "variables": list(block.variables)}
            for block in block_rows
        ],
        "nodes": [
            {
                "blocks": list(subset),
                "source_score_field": node_map[subset].source_score_field,
                "score_column": column_by_subset[subset],
            }
            for subset in ordered_subsets
        ],
        "score": {
            "kind": score_kind,
            "name": score_name,
            "unit": score_unit,
            "orientation": "higher_is_better",
            "same_heldout_rows_across_nodes": True,
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "validation": {
            "complete_boolean_subset_lattice": True,
            "node_count": len(ordered_subsets),
            "directed_edge_count": len(block_rows) * (2 ** (len(block_rows) - 1)),
            "validation_block_column": (
                None if validation_block_field is None else "validation_block"
            ),
        },
        "boundary": {
            "runs_odsp_inference": False,
            "authorizes_lattice_claim": False,
            "authorizes_new_information_order": False,
            "authorizes_cross_programme_lattice": False,
            "authorizes_eog_consumption": False,
            "authorizes_n4_action": False,
            "current_odsp_qualified_block_counts": [2, 3],
            "four_or_more_blocks_supported_by_v1": False,
        },
    }
    return ODSPLatticeReadyBundle(rows=tuple(rows), manifest=manifest)
