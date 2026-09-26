"""Validated registry of frozen eSDM sources eligible for ODSP transfer export."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence


REGISTRY_SCHEMA_VERSION = 1
REGISTRY_ID = "esdm-odsp-transfer-source-registry-v1"
EXPORTABLE_STATUS = "validated_exportable"
ALLOWED_STATUSES = frozenset(
    {
        EXPORTABLE_STATUS,
        "gain_only_not_exportable",
        "scientific_fail_not_exportable",
        "evidence_tier_not_transfer",
        "identification_only_not_transfer",
        "non_nested_comparison_not_transfer",
    }
)


@dataclass(frozen=True, slots=True)
class TransferSource:
    source_id: str
    programme: str
    status: str
    frozen_receipt: str
    frozen_receipt_schema: str | None
    frozen_result_status: str
    source_artifact_id: int | None
    source_result_schema: str | None
    absolute_score_fields: tuple[str, ...]
    information_levels: tuple[dict, ...]
    score_currency: dict | None
    adapter_function: str | None
    endpoint_id: str | None
    validated_integration_receipt: str | None
    parallel_family: str | None
    natural_order_with_parallel_sibling: bool | None
    reason: str

    @property
    def exportable(self) -> bool:
        return self.status == EXPORTABLE_STATUS

    def as_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "programme": self.programme,
            "status": self.status,
            "exportable": self.exportable,
            "frozen_receipt": self.frozen_receipt,
            "frozen_receipt_schema": self.frozen_receipt_schema,
            "frozen_result_status": self.frozen_result_status,
            "source_artifact_id": self.source_artifact_id,
            "source_result_schema": self.source_result_schema,
            "absolute_score_fields": list(self.absolute_score_fields),
            "information_levels": [dict(level) for level in self.information_levels],
            "score_currency": (
                None if self.score_currency is None else dict(self.score_currency)
            ),
            "adapter_function": self.adapter_function,
            "endpoint_id": self.endpoint_id,
            "validated_integration_receipt": self.validated_integration_receipt,
            "parallel_family": self.parallel_family,
            "natural_order_with_parallel_sibling": (
                self.natural_order_with_parallel_sibling
            ),
            "reason": self.reason,
        }


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, *, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name=name)


def _parse_level(value: object, *, name: str) -> dict:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    if set(value) != {"name", "information", "score_field"}:
        raise ValueError(
            f"{name} must contain exactly name, information, and score_field"
        )
    level_name = _text(value.get("name"), name=f"{name}.name")
    score_field = _text(value.get("score_field"), name=f"{name}.score_field")
    information = value.get("information")
    if not isinstance(information, list) or not information:
        raise ValueError(f"{name}.information must be a non-empty list")
    labels = tuple(
        _text(item, name=f"{name}.information[{index}]")
        for index, item in enumerate(information)
    )
    if len(set(labels)) != len(labels):
        raise ValueError(f"{name}.information labels must be unique")
    return {
        "name": level_name,
        "information": list(labels),
        "score_field": score_field,
    }


def _strict_filtration(levels: Sequence[Mapping[str, object]]) -> None:
    if len(levels) < 2:
        raise ValueError("an exportable source requires at least two levels")
    names = [str(level["name"]) for level in levels]
    if len(set(names)) != len(names):
        raise ValueError("information level names must be unique")
    for lower, upper in zip(levels, levels[1:]):
        lower_set = frozenset(str(value) for value in lower["information"])
        upper_set = frozenset(str(value) for value in upper["information"])
        if not lower_set < upper_set:
            raise ValueError(
                f"information levels are not strictly nested: "
                f"{lower['name']!r} -> {upper['name']!r}"
            )


def _parse_source(value: object, *, index: int) -> TransferSource:
    if not isinstance(value, Mapping):
        raise ValueError(f"sources[{index}] must be an object")

    source_id = _text(value.get("source_id"), name=f"sources[{index}].source_id")
    programme = _text(value.get("programme"), name=f"{source_id}.programme")
    status = _text(value.get("status"), name=f"{source_id}.status")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"{source_id} has unsupported registry status {status!r}")

    frozen_receipt = _text(
        value.get("frozen_receipt"), name=f"{source_id}.frozen_receipt"
    )
    frozen_receipt_schema = _optional_text(
        value.get("frozen_receipt_schema"),
        name=f"{source_id}.frozen_receipt_schema",
    )
    frozen_result_status = _text(
        value.get("frozen_result_status"),
        name=f"{source_id}.frozen_result_status",
    )

    artifact = value.get("source_artifact_id")
    if artifact is not None and (
        not isinstance(artifact, int) or isinstance(artifact, bool) or artifact <= 0
    ):
        raise ValueError(f"{source_id}.source_artifact_id must be a positive integer")

    source_result_schema = _optional_text(
        value.get("source_result_schema"),
        name=f"{source_id}.source_result_schema",
    )

    absolute_raw = value.get("absolute_score_fields")
    if not isinstance(absolute_raw, list):
        raise ValueError(f"{source_id}.absolute_score_fields must be a list")
    absolute_score_fields = tuple(
        _text(item, name=f"{source_id}.absolute_score_fields[{i}]")
        for i, item in enumerate(absolute_raw)
    )
    if len(set(absolute_score_fields)) != len(absolute_score_fields):
        raise ValueError(f"{source_id}.absolute_score_fields must be unique")

    levels_raw = value.get("information_levels")
    if not isinstance(levels_raw, list):
        raise ValueError(f"{source_id}.information_levels must be a list")
    levels = tuple(
        _parse_level(item, name=f"{source_id}.information_levels[{i}]")
        for i, item in enumerate(levels_raw)
    )

    currency_raw = value.get("score_currency")
    score_currency: dict | None
    if currency_raw is None:
        score_currency = None
    else:
        if not isinstance(currency_raw, Mapping):
            raise ValueError(f"{source_id}.score_currency must be an object or null")
        if set(currency_raw) != {"kind", "name", "unit"}:
            raise ValueError(
                f"{source_id}.score_currency must contain exactly kind, name, unit"
            )
        score_currency = {
            "kind": _text(currency_raw.get("kind"), name=f"{source_id}.score_currency.kind"),
            "name": _text(currency_raw.get("name"), name=f"{source_id}.score_currency.name"),
            "unit": _text(currency_raw.get("unit"), name=f"{source_id}.score_currency.unit"),
        }

    adapter_function = _optional_text(
        value.get("adapter_function"), name=f"{source_id}.adapter_function"
    )
    endpoint_id = _optional_text(
        value.get("endpoint_id"), name=f"{source_id}.endpoint_id"
    )
    validated_receipt = _optional_text(
        value.get("validated_integration_receipt"),
        name=f"{source_id}.validated_integration_receipt",
    )
    parallel_family = _optional_text(
        value.get("parallel_family"), name=f"{source_id}.parallel_family"
    )

    natural_order = value.get("natural_order_with_parallel_sibling")
    if natural_order is not None and not isinstance(natural_order, bool):
        raise ValueError(
            f"{source_id}.natural_order_with_parallel_sibling must be boolean or null"
        )

    reason = _text(value.get("reason"), name=f"{source_id}.reason")

    source = TransferSource(
        source_id=source_id,
        programme=programme,
        status=status,
        frozen_receipt=frozen_receipt,
        frozen_receipt_schema=frozen_receipt_schema,
        frozen_result_status=frozen_result_status,
        source_artifact_id=artifact,
        source_result_schema=source_result_schema,
        absolute_score_fields=absolute_score_fields,
        information_levels=levels,
        score_currency=score_currency,
        adapter_function=adapter_function,
        endpoint_id=endpoint_id,
        validated_integration_receipt=validated_receipt,
        parallel_family=parallel_family,
        natural_order_with_parallel_sibling=natural_order,
        reason=reason,
    )
    _validate_source_semantics(source)
    return source


def _validate_source_semantics(source: TransferSource) -> None:
    if source.exportable:
        if source.frozen_result_status != "PASS":
            raise ValueError(
                f"{source.source_id} cannot be exportable without frozen PASS status"
            )
        if source.source_artifact_id is None:
            raise ValueError(f"{source.source_id} exportable source needs an artifact")
        if source.source_result_schema is None:
            raise ValueError(
                f"{source.source_id} exportable source needs a result schema"
            )
        if len(source.absolute_score_fields) < 2:
            raise ValueError(
                f"{source.source_id} exportable source needs absolute lower/full scores"
            )
        if source.score_currency is None:
            raise ValueError(
                f"{source.source_id} exportable source needs score currency"
            )
        if source.adapter_function is None or source.endpoint_id is None:
            raise ValueError(
                f"{source.source_id} exportable source needs adapter and endpoint"
            )
        if source.validated_integration_receipt is None:
            raise ValueError(
                f"{source.source_id} exportable source needs validated integration receipt"
            )
        _strict_filtration(source.information_levels)
        used_fields = tuple(
            str(level["score_field"]) for level in source.information_levels
        )
        if set(used_fields) != set(source.absolute_score_fields):
            raise ValueError(
                f"{source.source_id} level score fields must equal declared absolute score fields"
            )
    else:
        if source.absolute_score_fields:
            raise ValueError(
                f"{source.source_id} non-exportable source cannot declare absolute score fields"
            )
        if source.information_levels:
            raise ValueError(
                f"{source.source_id} non-exportable source cannot declare information levels"
            )
        if source.score_currency is not None:
            raise ValueError(
                f"{source.source_id} non-exportable source cannot declare score currency"
            )
        if source.adapter_function is not None or source.endpoint_id is not None:
            raise ValueError(
                f"{source.source_id} non-exportable source cannot declare an adapter"
            )
        if source.validated_integration_receipt is not None:
            raise ValueError(
                f"{source.source_id} non-exportable source cannot claim validated integration"
            )

    if source.status == "scientific_fail_not_exportable":
        if source.frozen_result_status != "FAIL":
            raise ValueError(
                f"{source.source_id} scientific_fail status requires frozen FAIL"
            )

    if source.parallel_family is None:
        if source.natural_order_with_parallel_sibling is not None:
            raise ValueError(
                f"{source.source_id} natural-order flag requires parallel_family"
            )
    elif source.natural_order_with_parallel_sibling is None:
        raise ValueError(
            f"{source.source_id} parallel source requires an explicit natural-order flag"
        )


def load_transfer_source_registry(path: str | Path) -> tuple[TransferSource, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError("unsupported transfer-source registry schema_version")
    if payload.get("registry_id") != REGISTRY_ID:
        raise ValueError("unexpected transfer-source registry_id")

    statuses = payload.get("statuses")
    if not isinstance(statuses, list) or set(statuses) != set(ALLOWED_STATUSES):
        raise ValueError("registry status declaration drifted")

    boundary = payload.get("boundary")
    if not isinstance(boundary, Mapping):
        raise ValueError("registry boundary must be an object")
    for key in (
        "registry_authorizes_new_scientific_result",
        "registry_authorizes_rerun",
        "registry_authorizes_score_reconstruction",
        "registry_authorizes_new_information_order",
        "registry_authorizes_eog_consumption",
        "registry_authorizes_n4_action",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"registry boundary {key} must be false")

    values = payload.get("sources")
    if not isinstance(values, list) or not values:
        raise ValueError("registry sources must be a non-empty list")
    sources = tuple(_parse_source(value, index=i) for i, value in enumerate(values))

    ids = [source.source_id for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("registry source_id values must be unique")
    endpoints = [
        source.endpoint_id for source in sources if source.endpoint_id is not None
    ]
    if len(endpoints) != len(set(endpoints)):
        raise ValueError("registry endpoint_id values must be unique")

    families: dict[str, list[TransferSource]] = {}
    for source in sources:
        if source.parallel_family is not None:
            families.setdefault(source.parallel_family, []).append(source)
    for family, members in families.items():
        if len(members) < 2:
            raise ValueError(f"parallel family {family!r} must contain >=2 sources")
        if any(member.natural_order_with_parallel_sibling is not False for member in members):
            raise ValueError(
                f"parallel family {family!r} must explicitly refuse natural ordering"
            )
    return sources


def transfer_source_by_id(
    sources: Sequence[TransferSource],
    source_id: str,
) -> TransferSource:
    matches = [source for source in sources if source.source_id == str(source_id)]
    if len(matches) != 1:
        raise KeyError(f"unknown transfer source {source_id!r}")
    return matches[0]


def exportable_transfer_sources(
    sources: Sequence[TransferSource],
) -> tuple[TransferSource, ...]:
    return tuple(source for source in sources if source.exportable)


def require_exportable_transfer_source(
    sources: Sequence[TransferSource],
    source_id: str,
) -> TransferSource:
    source = transfer_source_by_id(sources, source_id)
    if not source.exportable:
        raise ValueError(
            f"{source.source_id} is not ODSP-exportable: "
            f"status={source.status}; reason={source.reason}"
        )
    return source
