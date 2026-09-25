"""Validated portfolio of ODSP information-transfer values from frozen eSDM sources."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .source_registry import (
    TransferSource,
    exportable_transfer_sources,
    load_transfer_source_registry,
)


PORTFOLIO_SCHEMA_ID = "esdm-odsp-transfer-portfolio-v1"


@dataclass(frozen=True, slots=True)
class TransferPortfolioEntry:
    source_id: str
    programme: str
    endpoint_id: str
    information_levels: tuple[dict, ...]
    score_currency: dict
    population_mean_gain: float
    population_interval_lower: float
    population_interval_upper: float
    population_status: str
    population_positive_group_fraction: float
    conservative_mean_value: float
    prediction_lower: float | None
    prediction_upper: float | None
    handoff_fingerprint: str
    source_population_fingerprint: str
    integration_receipt: str
    integration_receipt_sha256: str
    source_artifact_id: int
    parallel_family: str | None
    natural_order_with_parallel_sibling: bool | None

    def as_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "information_levels": [dict(level) for level in self.information_levels],
            "score_currency": dict(self.score_currency),
        }


@dataclass(frozen=True, slots=True)
class TransferPortfolio:
    registry_id: str
    registry_sha256: str
    entries: tuple[TransferPortfolioEntry, ...]
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        families: dict[str, list[str]] = {}
        for entry in self.entries:
            if entry.parallel_family is not None:
                families.setdefault(entry.parallel_family, []).append(entry.source_id)
        return {
            "schema_id": PORTFOLIO_SCHEMA_ID,
            "registry_id": self.registry_id,
            "registry_sha256": self.registry_sha256,
            "entries": [entry.as_dict() for entry in self.entries],
            "parallel_families": {
                family: {
                    "source_ids": sorted(source_ids),
                    "natural_order_authorized": False,
                }
                for family, source_ids in sorted(families.items())
            },
            "boundary": {
                "cross_source_numeric_ranking_authorized": False,
                "cross_source_effect_size_comparison_authorized": False,
                "portfolio_authorizes_information_order": False,
                "portfolio_authorizes_eog_consumption": False,
                "portfolio_authorizes_spatial_patch_ranking": False,
                "portfolio_authorizes_survey_site_selection": False,
                "portfolio_authorizes_n4_action": False,
                "n4_survey_action_owner": "ACSP",
                "interpretation": (
                    "the portfolio enumerates individually validated transfer-value "
                    "evidence; values remain tied to their own score currency, biological "
                    "target, comparator, and frozen programme"
                ),
            },
            "fingerprint": self.fingerprint,
        }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_fingerprint(payload: Mapping[str, object]) -> str:
    return _sha256_bytes(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )


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


def _receipt_sections(
    source: TransferSource,
    payload: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    if source.parallel_family == "v04_r5b_activity_state":
        contrasts = payload.get("contrasts")
        if not isinstance(contrasts, Mapping):
            raise ValueError(
                f"{source.source_id} integration receipt is missing contrasts"
            )
        contrast_name = (
            "activity" if source.source_id == "v04_r5b_activity" else "state"
        )
        contrast = contrasts.get(contrast_name)
        if not isinstance(contrast, Mapping):
            raise ValueError(
                f"{source.source_id} integration receipt is missing {contrast_name}"
            )
        odsp = contrast.get("odsp_result")
        handoff = contrast.get("n3_transfer_value")
    else:
        odsp = payload.get("odsp_result")
        handoff = payload.get("n3_transfer_value")
    if not isinstance(odsp, Mapping) or not isinstance(handoff, Mapping):
        raise ValueError(
            f"{source.source_id} integration receipt lacks ODSP/N3 sections"
        )
    return odsp, handoff


def _entry_from_source(
    source: TransferSource,
    *,
    root: Path,
) -> TransferPortfolioEntry:
    if not source.exportable:
        raise ValueError(f"{source.source_id} is not exportable")
    if (
        source.endpoint_id is None
        or source.score_currency is None
        or source.validated_integration_receipt is None
        or source.source_artifact_id is None
    ):
        raise ValueError(f"{source.source_id} exportable metadata is incomplete")

    receipt_path = root / source.validated_integration_receipt
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)
    raw = receipt_path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, Mapping):
        raise ValueError(f"{source.source_id} integration receipt must be an object")
    odsp, handoff = _receipt_sections(source, payload)

    if odsp.get("endpoint_id") != source.endpoint_id:
        raise ValueError(f"{source.source_id} endpoint_id drifted")

    mean = _finite(odsp.get("population_mean_gain"), name=f"{source.source_id}.mean")
    interval = odsp.get("population_mean_interval")
    if (
        not isinstance(interval, list)
        or len(interval) != 2
    ):
        raise ValueError(f"{source.source_id} population interval must have two bounds")
    lower = _finite(interval[0], name=f"{source.source_id}.interval[0]")
    upper = _finite(interval[1], name=f"{source.source_id}.interval[1]")
    if lower > upper:
        raise ValueError(f"{source.source_id} population interval is reversed")

    status = str(odsp.get("population_status"))
    if status not in {"positive", "uncertain", "nonpositive"}:
        raise ValueError(f"{source.source_id} population status drifted")
    if status == "positive" and not lower > 0.0:
        raise ValueError(f"{source.source_id} positive status lacks positive lower bound")
    if status == "uncertain" and not lower <= 0.0 < upper:
        raise ValueError(f"{source.source_id} uncertain status must cross zero")
    if status == "nonpositive" and not upper <= 0.0:
        raise ValueError(f"{source.source_id} nonpositive status must end at/below zero")

    positive_fraction = _finite(
        odsp.get("population_positive_group_fraction"),
        name=f"{source.source_id}.positive_fraction",
    )
    if not 0.0 <= positive_fraction <= 1.0:
        raise ValueError(f"{source.source_id} positive fraction is out of range")

    prediction = odsp.get("prediction_interval")
    if (
        not isinstance(prediction, list)
        or len(prediction) != 2
    ):
        raise ValueError(f"{source.source_id} prediction interval must have two bounds")
    prediction_lower = _finite(
        prediction[0], name=f"{source.source_id}.prediction[0]"
    )
    prediction_upper = _finite(
        prediction[1], name=f"{source.source_id}.prediction[1]"
    )
    if prediction_lower > prediction_upper:
        raise ValueError(f"{source.source_id} prediction interval is reversed")

    expected = _finite(
        handoff.get("total_expected_gain"),
        name=f"{source.source_id}.handoff.expected_gain",
    )
    conservative_key = (
        "conservative_mean_value"
        if "conservative_mean_value" in handoff
        else "total_conservative_mean_value"
    )
    conservative = _finite(
        handoff.get(conservative_key),
        name=f"{source.source_id}.handoff.conservative_mean_value",
    )
    if not math.isclose(expected, mean, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"{source.source_id} handoff/ODSP mean mismatch")
    expected_conservative = max(0.0, lower)
    if not math.isclose(
        conservative,
        expected_conservative,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(
            f"{source.source_id} conservative value is not max(0, lower CI)"
        )

    fingerprint = handoff.get("fingerprint")
    source_population_fingerprint = handoff.get("source_population_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ValueError(f"{source.source_id} handoff fingerprint is invalid")
    if (
        not isinstance(source_population_fingerprint, str)
        or len(source_population_fingerprint) != 64
    ):
        raise ValueError(
            f"{source.source_id} source population fingerprint is invalid"
        )

    return TransferPortfolioEntry(
        source_id=source.source_id,
        programme=source.programme,
        endpoint_id=source.endpoint_id,
        information_levels=tuple(dict(level) for level in source.information_levels),
        score_currency=dict(source.score_currency),
        population_mean_gain=mean,
        population_interval_lower=lower,
        population_interval_upper=upper,
        population_status=status,
        population_positive_group_fraction=positive_fraction,
        conservative_mean_value=conservative,
        prediction_lower=prediction_lower,
        prediction_upper=prediction_upper,
        handoff_fingerprint=fingerprint,
        source_population_fingerprint=source_population_fingerprint,
        integration_receipt=source.validated_integration_receipt,
        integration_receipt_sha256=_sha256_bytes(raw),
        source_artifact_id=source.source_artifact_id,
        parallel_family=source.parallel_family,
        natural_order_with_parallel_sibling=source.natural_order_with_parallel_sibling,
    )


def build_validated_transfer_portfolio(
    registry_path: str | Path,
) -> TransferPortfolio:
    path = Path(registry_path)
    root = path.resolve().parent
    raw_registry = path.read_bytes()
    sources = load_transfer_source_registry(path)
    entries = tuple(
        _entry_from_source(source, root=root)
        for source in exportable_transfer_sources(sources)
    )
    if not entries:
        raise ValueError("transfer portfolio requires at least one exportable source")

    source_ids = [entry.source_id for entry in entries]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("transfer portfolio source ids must be unique")
    endpoint_ids = [entry.endpoint_id for entry in entries]
    if len(endpoint_ids) != len(set(endpoint_ids)):
        raise ValueError("transfer portfolio endpoint ids must be unique")

    registry_payload = json.loads(raw_registry)
    registry_id = str(registry_payload.get("registry_id"))
    registry_sha = _sha256_bytes(raw_registry)

    core = {
        "schema_id": PORTFOLIO_SCHEMA_ID,
        "registry_id": registry_id,
        "registry_sha256": registry_sha,
        "entries": [entry.as_dict() for entry in entries],
        "parallel_families": {
            family: {
                "source_ids": sorted(
                    entry.source_id
                    for entry in entries
                    if entry.parallel_family == family
                ),
                "natural_order_authorized": False,
            }
            for family in sorted(
                {
                    entry.parallel_family
                    for entry in entries
                    if entry.parallel_family is not None
                }
            )
        },
        "boundary": {
            "cross_source_numeric_ranking_authorized": False,
            "cross_source_effect_size_comparison_authorized": False,
            "portfolio_authorizes_information_order": False,
            "portfolio_authorizes_eog_consumption": False,
            "portfolio_authorizes_spatial_patch_ranking": False,
            "portfolio_authorizes_survey_site_selection": False,
            "portfolio_authorizes_n4_action": False,
            "n4_survey_action_owner": "ACSP",
            "interpretation": (
                "the portfolio enumerates individually validated transfer-value "
                "evidence; values remain tied to their own score currency, biological "
                "target, comparator, and frozen programme"
            ),
        },
    }
    return TransferPortfolio(
        registry_id=registry_id,
        registry_sha256=registry_sha,
        entries=entries,
        fingerprint=_canonical_fingerprint(core),
    )


def validate_transfer_portfolio(payload: Mapping[str, object]) -> str:
    if payload.get("schema_id") != PORTFOLIO_SCHEMA_ID:
        raise ValueError("unsupported transfer portfolio schema")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("transfer portfolio entries must be a non-empty list")

    source_ids = []
    endpoint_ids = []
    for index, value in enumerate(entries):
        if not isinstance(value, Mapping):
            raise ValueError(f"entries[{index}] must be an object")
        source_id = value.get("source_id")
        endpoint_id = value.get("endpoint_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError(f"entries[{index}].source_id is invalid")
        if not isinstance(endpoint_id, str) or not endpoint_id:
            raise ValueError(f"entries[{index}].endpoint_id is invalid")
        source_ids.append(source_id)
        endpoint_ids.append(endpoint_id)

    if len(source_ids) != len(set(source_ids)):
        raise ValueError("transfer portfolio source ids must be unique")
    if len(endpoint_ids) != len(set(endpoint_ids)):
        raise ValueError("transfer portfolio endpoint ids must be unique")

    boundary = payload.get("boundary")
    if not isinstance(boundary, Mapping):
        raise ValueError("transfer portfolio boundary must be an object")
    for key in (
        "cross_source_numeric_ranking_authorized",
        "cross_source_effect_size_comparison_authorized",
        "portfolio_authorizes_information_order",
        "portfolio_authorizes_eog_consumption",
        "portfolio_authorizes_spatial_patch_ranking",
        "portfolio_authorizes_survey_site_selection",
        "portfolio_authorizes_n4_action",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"portfolio boundary {key} must be false")
    if boundary.get("n4_survey_action_owner") != "ACSP":
        raise ValueError("portfolio must preserve ACSP action ownership")

    fingerprint = payload.get("fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ValueError("portfolio fingerprint is invalid")
    core = dict(payload)
    core.pop("fingerprint", None)
    expected = _canonical_fingerprint(core)
    if fingerprint != expected:
        raise ValueError("transfer portfolio fingerprint mismatch")
    return fingerprint
