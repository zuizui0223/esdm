"""Exact removal of contexts with zero structural observation exposure."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from types import MappingProxyType

from esdm.domain import ExplicitGrid
from .compose import Model


def _canonical_key_sha256(keys) -> str:
    payload = json.dumps(
        [list(key) for key in sorted(tuple(keys))],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class StructuralExposureCompaction:
    dense_context_count: int
    compact_context_count: int
    reduction_factor: float
    retained_keys_sha256: str
    exposed_contexts_by_stream: object

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "exposed_contexts_by_stream",
            MappingProxyType(dict(self.exposed_contexts_by_stream)),
        )


def structural_exposure_keys(model: Model):
    """Return the ordered union of contexts exposed by at least one stream."""

    ordered = tuple(model.domain.keys)
    retained = [False for _ in ordered]
    by_stream = {}
    for stream in model.streams:
        mask_fn = getattr(stream, "structural_exposure_mask", None)
        if mask_fn is None:
            mask = tuple(True for _ in ordered)
        else:
            mask = tuple(bool(value) for value in mask_fn(ordered))
        if len(mask) != len(ordered):
            raise ValueError(
                f"stream {stream.name!r} structural mask length drifted"
            )
        by_stream[stream.name] = sum(mask)
        retained = [
            old or exposed
            for old, exposed in zip(retained, mask, strict=True)
        ]

    keys = tuple(
        key for key, exposed in zip(ordered, retained, strict=True)
        if exposed
    )
    if not keys:
        raise ValueError("model has no structurally exposed contexts")
    report = StructuralExposureCompaction(
        dense_context_count=len(ordered),
        compact_context_count=len(keys),
        reduction_factor=float(len(ordered)) / float(len(keys)),
        retained_keys_sha256=_canonical_key_sha256(keys),
        exposed_contexts_by_stream=by_stream,
    )
    return keys, report


def _filter_stream_species_data(stream, source, allowed):
    state_space = getattr(stream, "state_space", None)
    if state_space is None:
        outside_positive = [
            key for key, value in source.items()
            if key not in allowed and int(value) != 0
        ]
        if outside_positive:
            raise ValueError(
                f"nonzero data outside structural exposure for {stream.name}: "
                f"{outside_positive[0]!r}"
            )
        return {
            key: int(value)
            for key, value in source.items()
            if key in allowed
        }

    if set(source) != set(state_space.states):
        raise ValueError(
            f"state labels drifted while compacting stream {stream.name!r}"
        )
    output = {}
    for state in state_space.states:
        counts = source[state]
        outside_positive = [
            key for key, value in counts.items()
            if key not in allowed and int(value) != 0
        ]
        if outside_positive:
            raise ValueError(
                f"nonzero {state!r} data outside structural exposure for "
                f"{stream.name}: {outside_positive[0]!r}"
            )
        output[state] = {
            key: int(value)
            for key, value in counts.items()
            if key in allowed
        }
    return output


def compact_model_by_structural_exposure(
    model: Model,
    covariates,
    data,
):
    """Compact a model exactly by deleting zero-exposure contexts.

    The transformation is likelihood-preserving because every removed context has
    structural exposure false for every retained stream. Nonzero observations
    outside the retained union fail closed instead of being silently discarded.
    """

    keys, report = structural_exposure_keys(model)
    allowed = frozenset(keys)
    compact_model = Model(
        domain=ExplicitGrid(keys),
        species=model.species,
        streams=model.streams,
    )
    compact_covariates = {
        key: covariates[key]
        for key in keys
    }

    compact_data = {}
    known_streams = {stream.name for stream in model.streams}
    unknown_streams = set(data) - known_streams
    if unknown_streams:
        raise ValueError(
            f"data contain unknown streams during compaction: "
            f"{sorted(unknown_streams)}"
        )

    for stream in model.streams:
        if stream.name not in data:
            raise ValueError(
                f"missing stream {stream.name!r} during structural compaction"
            )
        compact_data[stream.name] = {}
        targets = tuple(model.stream_targets(stream))
        source_by_species = data[stream.name]
        if set(source_by_species) != set(targets):
            raise ValueError(
                f"stream {stream.name!r} target data drifted during compaction"
            )
        for species in targets:
            compact_data[stream.name][species] = _filter_stream_species_data(
                stream,
                source_by_species[species],
                allowed,
            )

    compact_model.check_design()
    return compact_model, compact_covariates, compact_data, report
