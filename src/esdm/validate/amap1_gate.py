"""Mechanical AMAP1 low-regret qualification gate."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .amap1_known_truth import make_amap1_worlds


@dataclass(frozen=True, slots=True)
class AMap1WorldSummary:
    world_id: str
    geometry_id: str
    truth_id: str
    oracle_model_id: str
    replicates: int
    material_regret_rate: float
    mean_regret: float
    detectability_positive_rate: float | None = None
    detectability_mean_gain: float | None = None


@dataclass(frozen=True, slots=True)
class AMap1GateConfig:
    replicates_per_world: int = 16
    materiality: float = 0.005
    positive_min_rate: float = 0.75
    positive_min_mean_gain: float = 0.005
    low_regret_max_material_rate: float = 0.25
    low_regret_max_mean_regret: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class AMap1GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class AMap1GateDecision:
    passed: bool
    checks: tuple[AMap1GateCheck, ...]
    claims: object

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claims",
            MappingProxyType(
                {str(name): bool(value) for name, value in dict(self.claims).items()}
            ),
        )


def summarize_amap1_world(
    world_id: str,
    regrets,
    *,
    detectability_gains=None,
    config: AMap1GateConfig | None = None,
) -> AMap1WorldSummary:
    cfg = AMap1GateConfig() if config is None else config
    worlds = {world.world_id: world for world in make_amap1_worlds()}
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown AMAP1 world {world_id!r}")
    world = worlds[name]

    regret_values = tuple(float(value) for value in regrets)
    if not regret_values:
        raise ValueError("AMAP1 regrets must be non-empty")

    detectability_positive_rate = None
    detectability_mean_gain = None
    if world.detectability_reference is None:
        if detectability_gains not in (None, (), []):
            values = tuple(detectability_gains)
            if values:
                raise ValueError(
                    "T0 AMAP1 world cannot carry detectability gains"
                )
    else:
        if detectability_gains is None:
            raise ValueError(
                "field-positive AMAP1 world requires detectability gains"
            )
        gain_values = tuple(float(value) for value in detectability_gains)
        if len(gain_values) != len(regret_values):
            raise ValueError(
                "AMAP1 regret and detectability vectors must have equal length"
            )
        detectability_positive_rate = (
            sum(value > 0.0 for value in gain_values) / len(gain_values)
        )
        detectability_mean_gain = sum(gain_values) / len(gain_values)

    return AMap1WorldSummary(
        world_id=name,
        geometry_id=world.geometry_id,
        truth_id=world.truth_id,
        oracle_model_id=world.oracle_model_id,
        replicates=len(regret_values),
        material_regret_rate=(
            sum(value > cfg.materiality for value in regret_values)
            / len(regret_values)
        ),
        mean_regret=sum(regret_values) / len(regret_values),
        detectability_positive_rate=detectability_positive_rate,
        detectability_mean_gain=detectability_mean_gain,
    )


def evaluate_amap1_gate(
    summaries,
    *,
    mean_divergences_per_fit: float,
    config: AMap1GateConfig | None = None,
) -> AMap1GateDecision:
    cfg = AMap1GateConfig() if config is None else config
    expected_worlds = {world.world_id: world for world in make_amap1_worlds()}
    rows = tuple(summaries)
    by_world = {}
    for row in rows:
        if not isinstance(row, AMap1WorldSummary):
            raise TypeError("AMAP1 summaries must be AMap1WorldSummary values")
        if row.world_id in by_world:
            raise ValueError(f"duplicate AMAP1 world summary: {row.world_id!r}")
        by_world[row.world_id] = row

    missing = sorted(set(expected_worlds) - set(by_world))
    extra = sorted(set(by_world) - set(expected_worlds))
    if missing:
        raise ValueError(f"AMAP1 gate missing worlds: {missing!r}")
    if extra:
        raise ValueError(f"AMAP1 gate contains undeclared worlds: {extra!r}")

    checks = []
    world_pass = {}

    def add(name, passed, observed, criterion):
        checks.append(
            AMap1GateCheck(
                str(name),
                bool(passed),
                observed,
                str(criterion),
            )
        )

    for world_id in sorted(expected_worlds):
        world = expected_worlds[world_id]
        row = by_world[world_id]
        metadata_ok = (
            row.geometry_id == world.geometry_id
            and row.truth_id == world.truth_id
            and row.oracle_model_id == world.oracle_model_id
        )
        add(
            f"{world_id}:metadata",
            metadata_ok,
            (row.geometry_id, row.truth_id, row.oracle_model_id),
            (
                f"metadata == ({world.geometry_id}, {world.truth_id}, "
                f"{world.oracle_model_id})"
            ),
        )

        replicate_ok = row.replicates == cfg.replicates_per_world
        add(
            f"{world_id}:replicates",
            replicate_ok,
            row.replicates,
            f"replicates == {cfg.replicates_per_world}",
        )

        regret_rate_ok = (
            row.material_regret_rate <= cfg.low_regret_max_material_rate
        )
        regret_mean_ok = row.mean_regret <= cfg.low_regret_max_mean_regret
        add(
            f"{world_id}:material_regret_rate",
            regret_rate_ok,
            row.material_regret_rate,
            (
                "material regret rate <= "
                f"{cfg.low_regret_max_material_rate}"
            ),
        )
        add(
            f"{world_id}:mean_regret",
            regret_mean_ok,
            row.mean_regret,
            f"mean regret <= {cfg.low_regret_max_mean_regret}",
        )

        detectability_ok = True
        if world.detectability_reference is not None:
            rate = row.detectability_positive_rate
            gain = row.detectability_mean_gain
            detectability_ok = (
                rate is not None
                and gain is not None
                and rate >= cfg.positive_min_rate
                and gain >= cfg.positive_min_mean_gain
            )
            add(
                f"{world_id}:oracle_detectability_rate",
                rate is not None and rate >= cfg.positive_min_rate,
                rate,
                f"positive gain rate >= {cfg.positive_min_rate}",
            )
            add(
                f"{world_id}:oracle_detectability_mean_gain",
                gain is not None and gain >= cfg.positive_min_mean_gain,
                gain,
                f"mean gain >= {cfg.positive_min_mean_gain}",
            )
        else:
            add(
                f"{world_id}:oracle_detectability_not_applicable",
                (
                    row.detectability_positive_rate is None
                    and row.detectability_mean_gain is None
                ),
                (
                    row.detectability_positive_rate,
                    row.detectability_mean_gain,
                ),
                "T0 carries no detectability comparison",
            )

        world_pass[world_id] = (
            metadata_ok
            and replicate_ok
            and regret_rate_ok
            and regret_mean_ok
            and detectability_ok
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

    supported = all(world_pass.values()) and divergence_ok
    return AMap1GateDecision(
        passed=supported,
        checks=tuple(checks),
        claims={"LOW_REGRET_MAP_SUPPORTED": supported},
    )
