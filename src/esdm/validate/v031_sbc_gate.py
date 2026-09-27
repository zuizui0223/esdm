"""Frozen v0.3.1 all-parameter SBC promotion component.

This module is intentionally separate from the retired v0.3 binned-TV gate.  It uses
replicate-specific finite rank supports after ESS-aware thinning and a familywise
simulation-based ECDF envelope across every declared free parameter.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.identify import SBCSimultaneousECDFResult, sbc_ecdf_simultaneous_test


@dataclass(frozen=True, slots=True)
class V031GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V031SBCGateConfig:
    replicates: int = 100
    alpha: float = 0.05
    envelope_simulations: int = 20_000
    evaluation_points: int = 49
    envelope_seed: int = 20260919
    required_num_chains: int = 2
    max_mean_divergences_per_fit: float = 0.10

    def __post_init__(self) -> None:
        if int(self.replicates) < 1:
            raise ValueError("replicates must be positive")
        if not math.isfinite(float(self.alpha)) or not 0.0 < float(self.alpha) < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        if int(self.envelope_simulations) < 100:
            raise ValueError("envelope_simulations must be at least 100")
        if int(self.evaluation_points) < 3:
            raise ValueError("evaluation_points must be at least 3")
        if int(self.required_num_chains) < 1:
            raise ValueError("required_num_chains must be positive")
        threshold = float(self.max_mean_divergences_per_fit)
        if not math.isfinite(threshold) or threshold < 0.0:
            raise ValueError("max_mean_divergences_per_fit must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class V031SBCGateDecision:
    passed: bool
    ecdf: SBCSimultaneousECDFResult
    mean_divergences: float
    checks: tuple[V031GateCheck, ...]


def evaluate_v031_sbc_gate(
    result,
    *,
    config: V031SBCGateConfig | None = None,
) -> V031SBCGateDecision:
    """Mechanically evaluate the frozen v0.3.1 SBC component.

    The decision covers only Gate E from ``docs/validation/V031_PROMOTION_GATE.md``.
    Passing it must never be reported as overall v0.3.1 promotion because Gates A–D
    and the mandatory semi-synthetic Gate F are independent requirements.
    """

    cfg = V031SBCGateConfig() if config is None else config
    if result.replicates < 1:
        raise ValueError("SBC result must contain at least one replicate")
    if len(result.divergences_by_replicate) != result.replicates:
        raise ValueError("SBC divergence vector length must equal replicate count")
    ranks = dict(result.ranks)
    draw_counts = dict(result.draw_counts_by_site)
    ess = dict(result.effective_sample_sizes_by_site)
    if not ranks:
        raise ValueError("SBC result must contain at least one free parameter")
    if set(ranks) != set(draw_counts) or set(ranks) != set(ess):
        raise ValueError("SBC ranks, draw counts, and ESS parameter sets must match")
    for site in ranks:
        if not (
            len(ranks[site])
            == len(draw_counts[site])
            == len(ess[site])
            == result.replicates
        ):
            raise ValueError("all per-parameter SBC vectors must match replicate count")
        if any(int(count) < 1 for count in draw_counts[site]):
            raise ValueError("ESS-thinned draw supports must be positive")
        if any(not math.isfinite(float(value)) or float(value) <= 0.0 for value in ess[site]):
            raise ValueError("ESS values must be finite and positive")

    ecdf = sbc_ecdf_simultaneous_test(
        ranks=ranks,
        draw_counts=draw_counts,
        alpha=cfg.alpha,
        simulations=cfg.envelope_simulations,
        seed=cfg.envelope_seed,
        evaluation_points=cfg.evaluation_points,
    )
    mean_divergences = (
        sum(int(value) for value in result.divergences_by_replicate) / result.replicates
    )
    checks = (
        V031GateCheck(
            name="sbc_replicates",
            passed=result.replicates == cfg.replicates,
            observed=result.replicates,
            criterion=f"replicates == {cfg.replicates}",
        ),
        V031GateCheck(
            name="sbc_num_chains",
            passed=int(result.num_chains) == int(cfg.required_num_chains),
            observed=int(result.num_chains),
            criterion=f"num_chains == {cfg.required_num_chains}",
        ),
        V031GateCheck(
            name="sbc_all_parameter_ecdf",
            passed=ecdf.passed,
            observed=ecdf.observed_max_deviation,
            criterion=(
                "familywise observed max ECDF deviation <= simulation-based "
                f"critical envelope ({ecdf.critical_max_deviation})"
            ),
        ),
        V031GateCheck(
            name="sbc_divergences",
            passed=mean_divergences <= cfg.max_mean_divergences_per_fit,
            observed=mean_divergences,
            criterion=(
                "mean divergences per fit <= "
                f"{cfg.max_mean_divergences_per_fit}"
            ),
        ),
    )
    return V031SBCGateDecision(
        passed=all(check.passed for check in checks),
        ecdf=ecdf,
        mean_divergences=mean_divergences,
        checks=checks,
    )
