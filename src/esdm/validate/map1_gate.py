"""Mechanical MAP1 qualification gate; no fitting logic."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .map1_known_truth import make_map1_worlds


ComparisonKey = tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class Map1ComparisonSummary:
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
class Map1GateConfig:
    replicates_per_world: int = 16
    positive_min_rate: float = 0.75
    positive_min_mean_gain: float = 0.005
    null_max_material_rate: float = 0.25
    null_max_mean_gain: float = 0.005
    material_gain_threshold: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class Map1GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class Map1GateDecision:
    passed: bool
    checks: tuple[Map1GateCheck, ...]
    claims: object

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claims",
            MappingProxyType(
                {str(name): bool(value) for name, value in dict(self.claims).items()}
            ),
        )


def summarize_map1_gains(
    world_id: str,
    candidate_model: str,
    reference_model: str,
    holdout: str,
    gains,
    *,
    config: Map1GateConfig | None = None,
) -> Map1ComparisonSummary:
    cfg = Map1GateConfig() if config is None else config
    values = tuple(float(value) for value in gains)
    if not values:
        raise ValueError("MAP1 gains must be non-empty")
    return Map1ComparisonSummary(
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


def _expected():
    positive = set()
    null = set()
    for world in make_map1_worlds():
        for candidate, reference, holdout in world.expected_positive_comparisons:
            positive.add((world.world_id, candidate, reference, holdout))
        for candidate, reference, holdout in world.expected_null_comparisons:
            null.add((world.world_id, candidate, reference, holdout))
    overlap = positive & null
    if overlap:
        raise RuntimeError(f"MAP1 comparison both positive and null: {sorted(overlap)!r}")
    return frozenset(positive), frozenset(null)


def evaluate_map1_gate(
    summaries,
    *,
    mean_divergences_per_fit: float,
    config: Map1GateConfig | None = None,
) -> Map1GateDecision:
    cfg = Map1GateConfig() if config is None else config
    rows = tuple(summaries)
    by_key = {}
    for row in rows:
        if not isinstance(row, Map1ComparisonSummary):
            raise TypeError("MAP1 summaries must be Map1ComparisonSummary values")
        if row.key in by_key:
            raise ValueError(f"duplicate MAP1 summary: {row.key!r}")
        by_key[row.key] = row

    positive, null = _expected()
    required = positive | null
    missing = sorted(required - set(by_key))
    extra = sorted(set(by_key) - required)
    if missing:
        raise ValueError(f"MAP1 gate summaries missing comparisons: {missing!r}")
    if extra:
        raise ValueError(f"MAP1 gate summaries contain undeclared comparisons: {extra!r}")

    checks = []
    comparison_pass = {}

    def add(name, passed, observed, criterion):
        checks.append(
            Map1GateCheck(str(name), bool(passed), observed, str(criterion))
        )

    for key in sorted(required):
        row = by_key[key]
        rep_ok = row.replicates == cfg.replicates_per_world
        add(
            f"{':'.join(key)}:replicates",
            rep_ok,
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
            comparison_pass[key] = rep_ok and rate_ok and mean_ok
        else:
            material_ok = row.material_gain_rate <= cfg.null_max_material_rate
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
            comparison_pass[key] = rep_ok and material_ok and mean_ok

    divergence_ok = (
        float(mean_divergences_per_fit) <= cfg.max_mean_divergences_per_fit
    )
    add(
        "sampling:mean_divergences_per_fit",
        divergence_ok,
        float(mean_divergences_per_fit),
        f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}",
    )

    coherent = all(comparison_pass.values()) and divergence_ok
    claims = {"COHERENT_MAP_SUPPORTED": coherent}
    return Map1GateDecision(
        passed=coherent,
        checks=tuple(checks),
        claims=claims,
    )
