"""Normalized, non-ranking portfolio of validated eSDM -> ODSP transfer evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .source_registry import TransferSource, exportable_transfer_sources


PORTFOLIO_SCHEMA = "esdm.odsp_transfer_evidence_portfolio.v1"


@dataclass(frozen=True, slots=True)
class TransferEvidenceItem:
    source_id: str
    programme: str
    endpoint_id: str
    lower_level: str
    upper_level: str
    added_information: tuple[str, ...]
    population_mean_gain: float
    mean_interval_lower: float
    mean_interval_upper: float
    population_status: str
    positive_group_fraction: float | None
    prediction_lower: float | None
    prediction_upper: float | None
    conservative_mean_value: float
    score_kind: str
    score_name: str
    score_unit: str
    parallel_family: str | None
    ordering_relation: str
    validated_integration_receipt: str
    receipt_sha256: str

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["added_information"] = list(self.added_information)
        return value


@dataclass(frozen=True, slots=True)
class TransferEvidencePortfolio:
    schema: str
    registry_id: str
    items: tuple[TransferEvidenceItem, ...]
    parallel_families: tuple[dict[str, object], ...]
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "registry_id": self.registry_id,
            "items": [item.as_dict() for item in self.items],
            "parallel_families": [dict(row) for row in self.parallel_families],
            "comparison_boundary": {
                "cross_programme_numeric_ranking_authorized": False,
                "same_score_unit_implies_comparability": False,
                "parallel_sibling_ordering_authorized": False,
                "parallel_sibling_addition_authorized": False,
                "single_global_information_ladder_authorized": False,
                "lattice_inference_created": False,
                "interpretation": (
                    "portfolio items are validated transfer contrasts in their own "
                    "frozen programmes; matching units do not authorize magnitude ranking "
                    "across different worlds, targets, or conditioning sets"
                ),
            },
            "action_boundary": {
                "authorizes_state_promotion": False,
                "authorizes_eog_consumption": False,
                "authorizes_spatial_patch_ranking": False,
                "authorizes_survey_site_selection": False,
                "authorizes_n4_action": False,
                "n4_survey_action_owner": "ACSP",
            },
            "fingerprint": self.fingerprint,
        }


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


def _optional_finite(value: object, *, name: str) -> float | None:
    if value is None:
        return None
    return _finite(value, name=name)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_fingerprint(payload: Mapping[str, object]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _added_information(source: TransferSource) -> tuple[str, ...]:
    if len(source.information_levels) != 2:
        raise ValueError(
            f"{source.source_id} portfolio v1 requires exactly two information levels"
        )
    lower = set(source.information_levels[0]["information"])
    upper = tuple(source.information_levels[1]["information"])
    added = tuple(value for value in upper if value not in lower)
    if not added:
        raise ValueError(f"{source.source_id} has no added information")
    return added


def _receipt_payload(root: Path, source: TransferSource) -> tuple[Path, dict[str, object]]:
    if source.validated_integration_receipt is None:
        raise ValueError(f"{source.source_id} has no validated integration receipt")
    path = root / source.validated_integration_receipt
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return path, value


def _extract_summary(
    root: Path,
    source: TransferSource,
) -> tuple[dict[str, object], dict[str, object], str]:
    path, receipt = _receipt_payload(root, source)
    receipt_id = receipt.get("receipt_id")

    if receipt_id == "esdm-v04-r5b-parallel-odsp-transfer-result-v1":
        if source.source_id == "v04_r5b_activity":
            key = "activity"
        elif source.source_id == "v04_r5b_state":
            key = "state"
        else:
            raise ValueError(
                f"{source.source_id} cannot use the R5b parallel receipt"
            )
        contrasts = receipt.get("contrasts")
        if not isinstance(contrasts, Mapping) or key not in contrasts:
            raise ValueError("R5b receipt missing requested contrast")
        row = contrasts[key]
        if not isinstance(row, Mapping):
            raise ValueError("R5b contrast must be an object")
        odsp = row.get("odsp_result")
        n3 = row.get("n3_transfer_value")
    elif receipt_id in {
        "esdm-v06a-to-odsp-to-n3-transfer-value-result-v1",
        "esdm-v07b-to-odsp-to-n3-transfer-value-result-v1",
    }:
        odsp = receipt.get("odsp_result")
        n3 = receipt.get("n3_transfer_value")
    else:
        raise ValueError(
            f"unsupported validated integration receipt for {source.source_id}: "
            f"{receipt_id!r}"
        )

    if not isinstance(odsp, Mapping) or not isinstance(n3, Mapping):
        raise ValueError(
            f"{source.source_id} integration receipt lacks normalized ODSP/N3 result"
        )
    return dict(odsp), dict(n3), _sha256(path)


def _normalize_item(root: Path, source: TransferSource) -> TransferEvidenceItem:
    if not source.exportable:
        raise ValueError(f"{source.source_id} is not exportable")
    if source.endpoint_id is None or source.score_currency is None:
        raise ValueError(f"{source.source_id} export metadata is incomplete")

    odsp, n3, receipt_sha = _extract_summary(root, source)
    levels = source.information_levels
    lower_level = str(levels[0]["name"])
    upper_level = str(levels[1]["name"])

    interval = odsp.get("population_mean_interval")
    if not isinstance(interval, list) or len(interval) != 2:
        raise ValueError(f"{source.source_id} population interval is malformed")
    lower = _finite(interval[0], name=f"{source.source_id}.interval[0]")
    upper = _finite(interval[1], name=f"{source.source_id}.interval[1]")
    if lower > upper:
        raise ValueError(f"{source.source_id} population interval is reversed")

    mean = _finite(
        odsp.get("population_mean_gain"),
        name=f"{source.source_id}.population_mean_gain",
    )
    status = str(odsp.get("population_status"))
    if status not in {"positive", "uncertain", "nonpositive"}:
        raise ValueError(f"{source.source_id} population status is invalid")

    n3_expected = _finite(
        n3.get("total_expected_gain"),
        name=f"{source.source_id}.n3.total_expected_gain",
    )
    if not math.isclose(mean, n3_expected, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(
            f"{source.source_id} ODSP mean and N3 expected value disagree"
        )
    conservative = _finite(
        n3.get("conservative_mean_value", n3.get("total_conservative_mean_value")),
        name=f"{source.source_id}.n3.conservative_mean_value",
    )
    if not math.isclose(
        conservative,
        max(0.0, lower),
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(
            f"{source.source_id} conservative value must equal max(0, lower CI)"
        )

    positive_fraction = odsp.get("population_positive_group_fraction")
    if positive_fraction is not None:
        positive_fraction = _finite(
            positive_fraction,
            name=f"{source.source_id}.positive_group_fraction",
        )
        if not 0.0 <= positive_fraction <= 1.0:
            raise ValueError(
                f"{source.source_id} positive-group fraction out of bounds"
            )

    prediction = odsp.get("prediction_interval")
    if prediction is None:
        prediction_lower = prediction_upper = None
    else:
        if not isinstance(prediction, list) or len(prediction) != 2:
            raise ValueError(f"{source.source_id} prediction interval is malformed")
        prediction_lower = _optional_finite(
            prediction[0], name=f"{source.source_id}.prediction_lower"
        )
        prediction_upper = _optional_finite(
            prediction[1], name=f"{source.source_id}.prediction_upper"
        )

    currency = source.score_currency
    kind = str(currency.get("kind"))
    name = str(currency.get("name"))
    unit = str(currency.get("unit"))
    if not kind or not name or not unit:
        raise ValueError(f"{source.source_id} score currency is incomplete")

    ordering_relation = (
        "parallel_nonordered"
        if source.parallel_family is not None
        else "standalone"
    )
    return TransferEvidenceItem(
        source_id=source.source_id,
        programme=source.programme,
        endpoint_id=source.endpoint_id,
        lower_level=lower_level,
        upper_level=upper_level,
        added_information=_added_information(source),
        population_mean_gain=mean,
        mean_interval_lower=lower,
        mean_interval_upper=upper,
        population_status=status,
        positive_group_fraction=positive_fraction,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        conservative_mean_value=conservative,
        score_kind=kind,
        score_name=name,
        score_unit=unit,
        parallel_family=source.parallel_family,
        ordering_relation=ordering_relation,
        validated_integration_receipt=source.validated_integration_receipt or "",
        receipt_sha256=receipt_sha,
    )


def build_transfer_evidence_portfolio(
    *,
    repository_root: str | Path,
    registry_id: str,
    sources: Sequence[TransferSource],
) -> TransferEvidencePortfolio:
    root = Path(repository_root)
    exportable = exportable_transfer_sources(sources)
    if not exportable:
        raise ValueError("no exportable transfer sources")

    items = tuple(
        sorted(
            (_normalize_item(root, source) for source in exportable),
            key=lambda item: item.source_id,
        )
    )

    families: dict[str, list[TransferEvidenceItem]] = {}
    for item in items:
        if item.parallel_family is not None:
            families.setdefault(item.parallel_family, []).append(item)

    parallel_rows = []
    for family, members in sorted(families.items()):
        if len(members) < 2:
            raise ValueError(f"parallel family {family!r} must contain >=2 items")
        parallel_rows.append(
            {
                "family": family,
                "members": [item.source_id for item in members],
                "shared_programme": len({item.programme for item in members}) == 1,
                "shared_score_currency": len(
                    {
                        (item.score_kind, item.score_name, item.score_unit)
                        for item in members
                    }
                )
                == 1,
                "natural_order_authorized": False,
                "combined_chain_authorized": False,
                "additive_total_authorized": False,
                "magnitude_ranking_authorized": False,
            }
        )

    core = {
        "schema": PORTFOLIO_SCHEMA,
        "registry_id": registry_id,
        "items": [item.as_dict() for item in items],
        "parallel_families": parallel_rows,
        "comparison_boundary": {
            "cross_programme_numeric_ranking_authorized": False,
            "same_score_unit_implies_comparability": False,
            "parallel_sibling_ordering_authorized": False,
            "parallel_sibling_addition_authorized": False,
            "single_global_information_ladder_authorized": False,
            "lattice_inference_created": False,
            "interpretation": (
                "portfolio items are validated transfer contrasts in their own "
                "frozen programmes; matching units do not authorize magnitude ranking "
                "across different worlds, targets, or conditioning sets"
            ),
        },
        "action_boundary": {
            "authorizes_state_promotion": False,
            "authorizes_eog_consumption": False,
            "authorizes_spatial_patch_ranking": False,
            "authorizes_survey_site_selection": False,
            "authorizes_n4_action": False,
            "n4_survey_action_owner": "ACSP",
        },
    }
    fingerprint = _canonical_fingerprint(core)
    return TransferEvidencePortfolio(
        schema=PORTFOLIO_SCHEMA,
        registry_id=registry_id,
        items=items,
        parallel_families=tuple(parallel_rows),
        fingerprint=fingerprint,
    )
