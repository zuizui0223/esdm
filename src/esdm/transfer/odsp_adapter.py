"""Export eSDM held-out scores to an ODSP information-transfer bundle.

The adapter is intentionally dependency-free: eSDM writes a CSV plus an ODSP
endpoint contract, and ODSP remains responsible for validating and scoring that
contract. Only genuinely nested information levels are accepted.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import csv
import json
import math
from pathlib import Path
import re
from typing import Mapping, Sequence


_SAFE = re.compile(r"[^A-Za-z0-9_]+")


@dataclass(frozen=True, slots=True)
class ODSPInformationLevel:
    name: str
    information: tuple[str, ...]
    source_score_field: str

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        field = str(self.source_score_field).strip()
        information = tuple(str(value).strip() for value in self.information)
        if not name:
            raise ValueError("level name must be non-empty")
        if not field:
            raise ValueError("source_score_field must be non-empty")
        if not information or any(not value for value in information):
            raise ValueError("each level must declare at least one information label")
        if len(set(information)) != len(information):
            raise ValueError("information labels must be unique within a level")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "source_score_field", field)
        object.__setattr__(self, "information", information)


@dataclass(frozen=True, slots=True)
class ODSPTransferBundle:
    contract: dict
    rows: tuple[dict, ...]
    manifest: dict

    def write(
        self,
        directory: str | Path,
        *,
        scores_filename: str = "scores.csv",
        contract_filename: str = "endpoint.json",
        manifest_filename: str = "adapter_manifest.json",
    ) -> dict[str, str]:
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        scores_path = root / scores_filename
        contract_path = root / contract_filename
        manifest_path = root / manifest_filename

        if not self.rows:
            raise ValueError("ODSP transfer bundle contains no rows")
        fieldnames = list(self.rows[0])
        with scores_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)

        contract = dict(self.contract)
        contract["data"] = {"path": scores_filename, "format": "csv"}
        contract_path.write_text(
            json.dumps(contract, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest_path.write_text(
            json.dumps(self.manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {
            "scores": str(scores_path),
            "contract": str(contract_path),
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


def _column_name(level_name: str) -> str:
    normalized = _SAFE.sub("_", level_name.strip()).strip("_").lower()
    if not normalized:
        raise ValueError("level name cannot normalize to an empty score column")
    return f"score__{normalized}"


def _validate_filtration(levels: Sequence[ODSPInformationLevel]) -> tuple[ODSPInformationLevel, ...]:
    rows = tuple(levels)
    if len(rows) < 2:
        raise ValueError("ODSP export requires at least two information levels")
    if len({row.name for row in rows}) != len(rows):
        raise ValueError("ODSP export level names must be unique")
    if len({_column_name(row.name) for row in rows}) != len(rows):
        raise ValueError("ODSP export level names collide after column normalization")

    for lower, upper in zip(rows, rows[1:]):
        lower_set = frozenset(lower.information)
        upper_set = frozenset(upper.information)
        if not lower_set < upper_set:
            raise ValueError(
                "ODSP export accepts only strict nested information levels; "
                f"{lower.name!r} -> {upper.name!r} is not a filtration"
            )
    return rows


def build_odsp_transfer_bundle(
    *,
    endpoint_id: str,
    levels: Sequence[ODSPInformationLevel],
    records: Sequence[object],
    group_field: str,
    row_id_field: str | None = None,
    block_field: str | None = None,
    weight_field: str | None = None,
    population_cluster_field: str | None = None,
    analysis_mode: str = "descriptive",
    filtration_frozen_before_outcome_scoring: bool = True,
    source_schema: str | None = None,
    source_git_sha: str | None = None,
    group_semantics: str | None = None,
) -> ODSPTransferBundle:
    """Build an ODSP-compatible external-score bundle from eSDM records."""

    endpoint_id = str(endpoint_id).strip()
    if not endpoint_id:
        raise ValueError("endpoint_id must be non-empty")
    levels = _validate_filtration(levels)
    source_rows = tuple(_mapping(record) for record in records)
    if not source_rows:
        raise ValueError("records must be non-empty")
    if analysis_mode not in {"descriptive", "confirmatory"}:
        raise ValueError("analysis_mode must be descriptive or confirmatory")
    if analysis_mode == "confirmatory" and not filtration_frozen_before_outcome_scoring:
        raise ValueError("confirmatory export requires frozen filtration")

    score_columns = {level.name: _column_name(level.name) for level in levels}
    rows: list[dict[str, object]] = []
    seen_row_ids: set[str] = set()

    for index, source in enumerate(source_rows):
        if group_field not in source:
            raise ValueError(f"record {index} is missing group_field {group_field!r}")
        group = str(source[group_field]).strip()
        if not group:
            raise ValueError(f"record {index} has empty group value")

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
        if block_field is not None:
            if block_field not in source:
                raise ValueError(f"record {index} is missing block_field {block_field!r}")
            row["block"] = str(source[block_field]).strip()
            if not row["block"]:
                raise ValueError("block values must be non-empty")
        if population_cluster_field is not None:
            if population_cluster_field not in source:
                raise ValueError(
                    f"record {index} is missing population_cluster_field "
                    f"{population_cluster_field!r}"
                )
            row["population_cluster"] = str(source[population_cluster_field]).strip()
            if not row["population_cluster"]:
                raise ValueError("population cluster values must be non-empty")

        for level in levels:
            if level.source_score_field not in source:
                raise ValueError(
                    f"record {index} is missing score field "
                    f"{level.source_score_field!r}"
                )
            row[score_columns[level.name]] = _finite(
                source[level.source_score_field],
                name=f"record[{index}].{level.source_score_field}",
            )
        rows.append(row)

    contract = {
        "schema_version": 1,
        "endpoint_id": endpoint_id,
        "data": {"path": "scores.csv", "format": "csv"},
        "columns": {
            "row_id": "row_id",
            "group": "group",
            "block": None if block_field is None else "block",
            "weight": "weight",
            "population_cluster": (
                None if population_cluster_field is None else "population_cluster"
            ),
        },
        "score": {
            "kind": "log",
            "name": "mean_heldout_log_predictive_density",
            "orientation": "higher_is_better",
            "common_scoring_rule": True,
            "common_reference_measure": True,
        },
        "evaluation": {
            "analysis_mode": analysis_mode,
            "heldout_predictions": True,
            "same_rows_across_levels": True,
            "heldout_outcome_not_used_for_prediction_or_selection": True,
            "filtration_frozen_before_outcome_scoring": bool(
                filtration_frozen_before_outcome_scoring
            ),
            "row_independence_if_no_block": block_field is None,
        },
        "levels": [
            {
                "name": level.name,
                "information": list(level.information),
                "score_column": score_columns[level.name],
            }
            for level in levels
        ],
        "certification": {
            "familywise_confidence_level": 0.95,
            "bootstrap_draws": 500,
            "seed": 20260924,
            "minimum_blocks_per_group": 2,
            "gain_tolerance": 0.0,
        },
    }
    manifest = {
        "schema": "esdm.odsp_transfer_bundle.v1",
        "endpoint_id": endpoint_id,
        "source_schema": source_schema,
        "source_git_sha": source_git_sha,
        "group_semantics": group_semantics,
        "row_count": len(rows),
        "level_count": len(levels),
        "analysis_mode": analysis_mode,
        "information_levels": [
            {"name": level.name, "information": list(level.information)}
            for level in levels
        ],
        "odsp_dependency_required_to_export": False,
        "odsp_top_level_cli": "odsp transfer",
    }
    return ODSPTransferBundle(
        contract=contract,
        rows=tuple(rows),
        manifest=manifest,
    )


def build_v06a_accessibility_odsp_bundle(
    aggregate_result: Mapping[str, object],
) -> ODSPTransferBundle:
    """Bind the frozen v0.6a accessibility comparison to ODSP transfer levels."""

    if aggregate_result.get("schema") != "esdm.v06a.accessibility.v1":
        raise ValueError("expected esdm.v06a.accessibility.v1 aggregate result")
    if aggregate_result.get("status") not in {"PASS", "FAIL"}:
        raise ValueError("v0.6a aggregate must be a completed scientific result")
    if aggregate_result.get("infrastructure_block") is not None:
        raise ValueError("infrastructure-blocked v0.6a result cannot be exported")

    records = aggregate_result.get("replicates")
    if not isinstance(records, list) or not records:
        raise ValueError("v0.6a aggregate must contain replicate records")

    return build_odsp_transfer_bundle(
        endpoint_id="esdm_v06a_accessibility_transfer_v1",
        levels=(
            ODSPInformationLevel(
                name="suitability_only",
                information=("suitability",),
                source_score_field="accessibility_knockout_heldout_log_score",
            ),
            ODSPInformationLevel(
                name="suitability_accessibility",
                information=("suitability", "accessibility"),
                source_score_field="full_heldout_log_score",
            ),
        ),
        records=records,
        group_field="replicate",
        analysis_mode="descriptive",
        filtration_frozen_before_outcome_scoring=True,
        source_schema="esdm.v06a.accessibility.v1",
        source_git_sha=(
            None
            if aggregate_result.get("git_sha") is None
            else str(aggregate_result.get("git_sha"))
        ),
        group_semantics="independent known-truth replicate",
    )
