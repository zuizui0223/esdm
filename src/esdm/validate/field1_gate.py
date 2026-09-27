"""Mechanical FIELD1 qualification gate; contains no fitting logic."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from .field1_known_truth import (
    make_field1_mean_covariance_factorial,
    make_field1_primary_worlds,
)


ComparisonKey = tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class Field1ComparisonSummary:
    world_id: str
    candidate_model: str
    reference_model: str
    holdout: str
    replicates: int
    positive_gain_rate: float
    material_gain_rate: float
    mean_gain: float

    @property
    def key(self) -> ComparisonKey:
        return (
            str(self.world_id),
            str(self.candidate_model),
            str(self.reference_model),
            str(self.holdout),
        )


@dataclass(frozen=True, slots=True)
class Field1GateConfig:
    replicates_per_world: int = 16
    positive_min_rate: float = 0.75
    positive_min_mean_gain: float = 0.005
    null_max_material_rate: float = 0.25
    null_max_mean_gain: float = 0.005
    material_gain_threshold: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class Field1GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class Field1GateDecision:
    passed: bool
    checks: tuple[Field1GateCheck, ...]
    claims: Mapping[str, bool]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claims",
            MappingProxyType(
                {str(name): bool(value) for name, value in self.claims.items()}
            ),
        )


def summarize_field1_gains(
    world_id: str,
    candidate_model: str,
    reference_model: str,
    holdout: str,
    gains,
    *,
    config: Field1GateConfig | None = None,
) -> Field1ComparisonSummary:
    """Convert replicate-level held-out gains into the frozen FIELD1 summary."""

    cfg = Field1GateConfig() if config is None else config
    values = tuple(float(value) for value in gains)
    if not values:
        raise ValueError("FIELD1 gains must be non-empty")
    return Field1ComparisonSummary(
        world_id=str(world_id),
        candidate_model=str(candidate_model),
        reference_model=str(reference_model),
        holdout=str(holdout),
        replicates=len(values),
        positive_gain_rate=sum(value > 0.0 for value in values) / len(values),
        material_gain_rate=(
            sum(value > cfg.material_gain_threshold for value in values)
            / len(values)
        ),
        mean_gain=sum(values) / len(values),
    )


def _expected_comparisons():
    positive: set[ComparisonKey] = set()
    null: set[ComparisonKey] = set()

    for world in make_field1_primary_worlds():
        for candidate, reference, holdout in world.expected_positive_comparisons:
            positive.add((world.world_id, candidate, reference, holdout))
        for candidate, reference, holdout in world.expected_null_comparisons:
            null.add((world.world_id, candidate, reference, holdout))

    for world in make_field1_mean_covariance_factorial():
        for candidate, reference, holdout in world.expected_positive_comparisons:
            positive.add((world.world_id, candidate, reference, holdout))
        for candidate, reference, holdout in world.expected_null_comparisons:
            null.add((world.world_id, candidate, reference, holdout))

    overlap = positive & null
    if overlap:
        raise RuntimeError(
            f"FIELD1 comparison cannot be both positive and null: {sorted(overlap)!r}"
        )
    return frozenset(positive), frozenset(null)


def evaluate_field1_gate(
    summaries,
    *,
    k6_distance_match_passed: bool,
    h2_barrier_transfer_passed: bool,
    mean_divergences_per_fit: float,
    config: Field1GateConfig | None = None,
) -> Field1GateDecision:
    """Apply the frozen FIELD1 predictive qualification rules."""

    cfg = Field1GateConfig() if config is None else config
    rows = tuple(summaries)
    by_key = {}
    for row in rows:
        if not isinstance(row, Field1ComparisonSummary):
            raise TypeError("FIELD1 summaries must be Field1ComparisonSummary values")
        if row.key in by_key:
            raise ValueError(f"duplicate FIELD1 comparison summary: {row.key!r}")
        by_key[row.key] = row

    positive, null = _expected_comparisons()
    required = positive | null
    missing = sorted(required - set(by_key))
    if missing:
        raise ValueError(f"FIELD1 gate summaries missing comparisons: {missing!r}")
    unexpected = sorted(set(by_key) - required)
    if unexpected:
        raise ValueError(
            f"FIELD1 gate summaries contain undeclared comparisons: {unexpected!r}"
        )

    checks: list[Field1GateCheck] = []
    comparison_pass: dict[ComparisonKey, bool] = {}

    def add(name, passed, observed, criterion):
        checks.append(
            Field1GateCheck(
                str(name),
                bool(passed),
                observed,
                str(criterion),
            )
        )

    for key in sorted(required):
        row = by_key[key]
        replicate_ok = row.replicates == cfg.replicates_per_world
        add(
            f"{':'.join(key)}:replicates",
            replicate_ok,
            row.replicates,
            f"replicates == {cfg.replicates_per_world}",
        )

        if key in positive:
            rate_ok = row.positive_gain_rate >= cfg.positive_min_rate
            mean_ok = row.mean_gain >= cfg.positive_min_mean_gain
            add(
                f"{':'.join(key)}:positive_rate",
                rate_ok,
                row.positive_gain_rate,
                f"positive gain rate >= {cfg.positive_min_rate}",
            )
            add(
                f"{':'.join(key)}:mean_gain",
                mean_ok,
                row.mean_gain,
                f"mean gain >= {cfg.positive_min_mean_gain}",
            )
            comparison_pass[key] = replicate_ok and rate_ok and mean_ok
        else:
            material_ok = (
                row.material_gain_rate <= cfg.null_max_material_rate
            )
            mean_ok = row.mean_gain <= cfg.null_max_mean_gain
            add(
                f"{':'.join(key)}:material_rate",
                material_ok,
                row.material_gain_rate,
                f"material gain rate <= {cfg.null_max_material_rate}",
            )
            add(
                f"{':'.join(key)}:mean_gain",
                mean_ok,
                row.mean_gain,
                f"mean gain <= {cfg.null_max_mean_gain}",
            )
            comparison_pass[key] = replicate_ok and material_ok and mean_ok

    add(
        "K6:distance_match",
        bool(k6_distance_match_passed),
        bool(k6_distance_match_passed),
        "at least one matched edge-distance stratum has barrier and non-barrier edges",
    )
    add(
        "K6:H2_barrier_transfer_geometry",
        bool(h2_barrier_transfer_passed),
        bool(h2_barrier_transfer_passed),
        (
            "H2 training contains an observed-side barrier edge and the heldout "
            "boundary contains a separate barrier edge"
        ),
    )
    divergence_ok = (
        float(mean_divergences_per_fit) <= cfg.max_mean_divergences_per_fit
    )
    add(
        "sampling:mean_divergences_per_fit",
        divergence_ok,
        float(mean_divergences_per_fit),
        f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}",
    )

    def ok(world, candidate, reference, holdout):
        return comparison_pass[(world, candidate, reference, holdout)]

    field_present = (
        ok("K1", "M1", "M0", "H1")
        and ok("K0", "M1", "M0", "H1")
    )

    k5_worlds = (
        "K5_mean0_cov0",
        "K5_mean1_cov0",
        "K5_mean0_cov1",
        "K5_mean1_cov1",
    )
    env_supported = (
        ok("K2", "M2", "M1", "H1")
        and ok("K1", "M2", "M1", "H1")
        and all(ok(world, "M2", "M1", "H1") for world in k5_worlds)
    )

    barrier_supported = (
        ok("K3", "M3", "M1", "H2")
        and ok("K1", "M3", "M1", "H2")
        and bool(k6_distance_match_passed)
        and bool(h2_barrier_transfer_passed)
    )

    full_supported = (
        field_present
        and env_supported
        and barrier_supported
        and ok("K4", "M4", "M2", "H2")
        and ok("K4", "M4", "M3", "H1")
    )

    claims = {
        "FIELD_PRESENT": field_present,
        "ENV_DEPENDENCE_SUPPORTED": env_supported,
        "BARRIER_DEPENDENCE_SUPPORTED": barrier_supported,
        "FULL_MAP_STRUCTURE_SUPPORTED": full_supported,
    }
    check_tuple = tuple(checks)
    return Field1GateDecision(
        passed=all(check.passed for check in check_tuple),
        checks=check_tuple,
        claims=claims,
    )
