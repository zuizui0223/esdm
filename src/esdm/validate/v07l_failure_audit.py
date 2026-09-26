"""Post-outcome diagnostic audit for the frozen v0.7l selective-adaptation FAIL.

This module never reruns simulation or MCMC. It only recomputes counterfactual
policy summaries from the already frozen 64 replicate records.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, asdict
import math


_DYNAMIC_TARGETS = (
    "sp.occupancy.psi0_logit",
    "sp.occupancy.gamma_logit",
    "sp.occupancy.epsilon_logit",
)
_ALL_TARGETS = (
    "sp.suitability.alpha",
    *_DYNAMIC_TARGETS,
)
_WORLDS = (
    "strong_headroom",
    "threshold_below",
    "threshold_above",
    "negligible_headroom",
)
_TRIGGER_RATIO = 0.80

_WORLD_PROBABILITIES = {
    "strong_headroom": {
        "alpha": 0.30,
        "psi0": 0.85,
        "gamma": 0.25,
        "epsilon": 0.38,
    },
    "threshold_below": {
        "alpha": 0.30,
        "psi0": 0.85,
        "gamma": 0.25,
        "epsilon": 0.22,
    },
    "threshold_above": {
        "alpha": 0.30,
        "psi0": 0.85,
        "gamma": 0.25,
        "epsilon": 0.08,
    },
    "negligible_headroom": {
        "alpha": 0.30,
        "psi0": 0.85,
        "gamma": 0.65,
        "epsilon": 0.22,
    },
}


def _logit(probability: float) -> float:
    p = float(probability)
    return math.log(p / (1.0 - p))


def _truth(world: str) -> dict[str, float]:
    row = _WORLD_PROBABILITIES[str(world)]
    return {
        "sp.suitability.alpha": float(row["alpha"]),
        "sp.occupancy.psi0_logit": _logit(float(row["psi0"])),
        "sp.occupancy.gamma_logit": _logit(float(row["gamma"])),
        "sp.occupancy.epsilon_logit": _logit(float(row["epsilon"])),
    }


def _mean(values: Sequence[float]) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("mean requires at least one value")
    return math.fsum(rows) / len(rows)


def _actual_ratio(record: Mapping[str, object]) -> float:
    adaptive = record["adaptive_posterior_sds"]
    transferred = record["transferred_posterior_sds"]
    if not isinstance(adaptive, Mapping) or not isinstance(transferred, Mapping):
        raise ValueError("v0.7l replicate is missing posterior SD maps")
    adaptive_worst = max(float(adaptive[target]) for target in _DYNAMIC_TARGETS)
    transferred_worst = max(float(transferred[target]) for target in _DYNAMIC_TARGETS)
    if transferred_worst <= 0.0:
        raise ValueError("transferred worst dynamic posterior SD must be positive")
    return adaptive_worst / transferred_worst


def _select(record: Mapping[str, object], *, adaptive: bool, field: str) -> Mapping[str, object]:
    key = f"{'adaptive' if adaptive else 'transferred'}_{field}"
    value = record[key]
    if not isinstance(value, Mapping):
        raise ValueError(f"v0.7l replicate is missing {key}")
    return value


@dataclass(frozen=True, slots=True)
class CounterfactualPolicySummary:
    policy_id: str
    trigger_threshold: float | None
    trigger_sensitivity: float
    trigger_specificity: float
    trigger_balanced_accuracy: float
    mean_policy_to_transferred_ratio: float
    policy_harm_rate: float
    mean_policy_regret: float
    recovery_guardrails_pass: bool
    failed_recovery_checks: tuple[dict[str, object], ...]

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["failed_recovery_checks"] = list(self.failed_recovery_checks)
        return value


def _summarize_policy(
    records: Sequence[Mapping[str, object]],
    *,
    policy_id: str,
    trigger_threshold: float | None = None,
    mode: str,
) -> CounterfactualPolicySummary:
    if not records:
        raise ValueError("v0.7l audit requires replicate records")

    chosen: list[tuple[Mapping[str, object], bool, float, bool]] = []
    for record in records:
        ratio = _actual_ratio(record)
        actual = ratio <= _TRIGGER_RATIO
        if mode == "threshold":
            if trigger_threshold is None:
                raise ValueError("threshold policy requires trigger_threshold")
            adaptive = (
                float(record["pilot_predicted_adaptive_to_transferred_ratio"])
                <= float(trigger_threshold)
            )
        elif mode == "always_adaptive":
            adaptive = True
        elif mode == "always_transferred":
            adaptive = False
        elif mode == "oracle_headroom":
            adaptive = actual
        else:
            raise ValueError(f"unknown policy mode {mode!r}")
        chosen.append((record, adaptive, ratio, actual))

    tp = sum(adaptive and actual for _, adaptive, _, actual in chosen)
    fp = sum(adaptive and not actual for _, adaptive, _, actual in chosen)
    tn = sum((not adaptive) and (not actual) for _, adaptive, _, actual in chosen)
    fn = sum((not adaptive) and actual for _, adaptive, _, actual in chosen)
    sensitivity = tp / (tp + fn) if (tp + fn) else 1.0
    specificity = tn / (tn + fp) if (tn + fp) else 1.0

    policy_ratios = []
    regrets = []
    failed_recovery: list[dict[str, object]] = []
    for world in _WORLDS:
        local = [item for item in chosen if str(item[0]["world"]) == world]
        if len(local) != 16:
            raise ValueError(f"expected 16 frozen replicates in world {world!r}")
        truth = _truth(world)
        for target in _ALL_TARGETS:
            errors = []
            coverage = []
            for record, adaptive, _, _ in local:
                means = _select(record, adaptive=adaptive, field="posterior_means")
                lows = _select(record, adaptive=adaptive, field="posterior_lows")
                highs = _select(record, adaptive=adaptive, field="posterior_highs")
                errors.append(float(means[target]) - truth[target])
                coverage.append(
                    float(lows[target]) <= truth[target] <= float(highs[target])
                )
            bias = _mean(errors)
            cover = _mean([1.0 if value else 0.0 for value in coverage])
            if abs(bias) > 0.20:
                failed_recovery.append(
                    {
                        "world": world,
                        "kind": "bias",
                        "target": target,
                        "observed": bias,
                        "criterion": "abs(mean bias) <= 0.20",
                    }
                )
            if cover < 0.75:
                failed_recovery.append(
                    {
                        "world": world,
                        "kind": "coverage",
                        "target": target,
                        "observed": cover,
                        "criterion": "coverage >= 0.75",
                    }
                )

    for _, adaptive, ratio, actual in chosen:
        policy_ratio = ratio if adaptive else 1.0
        oracle_ratio = ratio if actual else 1.0
        policy_ratios.append(policy_ratio)
        regrets.append(policy_ratio - oracle_ratio)

    return CounterfactualPolicySummary(
        policy_id=str(policy_id),
        trigger_threshold=(
            None if trigger_threshold is None else float(trigger_threshold)
        ),
        trigger_sensitivity=float(sensitivity),
        trigger_specificity=float(specificity),
        trigger_balanced_accuracy=float(0.5 * (sensitivity + specificity)),
        mean_policy_to_transferred_ratio=_mean(policy_ratios),
        policy_harm_rate=_mean(
            [1.0 if value > 1.0 else 0.0 for value in policy_ratios]
        ),
        mean_policy_regret=_mean(regrets),
        recovery_guardrails_pass=not failed_recovery,
        failed_recovery_checks=tuple(failed_recovery),
    )


def _threshold_candidates(records: Sequence[Mapping[str, object]]) -> tuple[float, ...]:
    values = sorted(
        {
            float(record["pilot_predicted_adaptive_to_transferred_ratio"])
            for record in records
        }
    )
    if not values:
        raise ValueError("v0.7l audit found no pilot ratios")
    candidates = [values[0] - 1e-9, values[-1] + 1e-9]
    candidates.extend(values)
    candidates.extend(
        0.5 * (left + right)
        for left, right in zip(values[:-1], values[1:])
    )
    return tuple(sorted(set(float(value) for value in candidates)))


def audit_v07l_failure(result: Mapping[str, object]) -> dict[str, object]:
    """Diagnose whether v0.7l can be rescued by threshold choice alone."""

    if result.get("schema") != "esdm.v07l.selective_adaptation.v1":
        raise ValueError("expected frozen esdm.v07l.selective_adaptation.v1 result")
    if result.get("status") != "FAIL":
        raise ValueError("failure audit requires the frozen v0.7l FAIL result")
    if result.get("infrastructure_block") is not None:
        raise ValueError("infrastructure-blocked result cannot support failure audit")

    records = result.get("replicates")
    if not isinstance(records, list) or len(records) != 64:
        raise ValueError("v0.7l failure audit requires all 64 frozen replicates")

    threshold_below_actual = _mean(
        [
            1.0 if _actual_ratio(record) <= _TRIGGER_RATIO else 0.0
            for record in records
            if str(record["world"]) == "threshold_below"
        ]
    )

    threshold_rows = [
        _summarize_policy(
            records,
            policy_id=f"scalar_threshold_{threshold:.12f}",
            trigger_threshold=threshold,
            mode="threshold",
        )
        for threshold in _threshold_candidates(records)
    ]
    best = max(
        threshold_rows,
        key=lambda row: (
            row.trigger_balanced_accuracy,
            -row.mean_policy_regret,
            -abs((row.trigger_threshold or 0.0) - _TRIGGER_RATIO),
        ),
    )

    original = _summarize_policy(
        records,
        policy_id="frozen_threshold_0.80",
        trigger_threshold=0.80,
        mode="threshold",
    )
    always_adaptive = _summarize_policy(
        records,
        policy_id="always_adaptive",
        mode="always_adaptive",
    )
    always_transferred = _summarize_policy(
        records,
        policy_id="always_transferred",
        mode="always_transferred",
    )
    oracle = _summarize_policy(
        records,
        policy_id="oracle_material_headroom",
        mode="oracle_headroom",
    )

    any_recovery_pass = any(row.recovery_guardrails_pass for row in threshold_rows)
    threshold_only_rescue_possible = bool(
        threshold_below_actual >= 0.75
        and any(
            row.trigger_sensitivity >= 0.75
            and row.trigger_specificity >= 0.75
            and row.trigger_balanced_accuracy >= 0.75
            and row.mean_policy_to_transferred_ratio <= 0.95
            and row.policy_harm_rate <= 0.10
            and row.mean_policy_regret <= 0.05
            and row.recovery_guardrails_pass
            for row in threshold_rows
        )
    )

    return {
        "schema": "esdm.v07l.failure_audit.v1",
        "source_status": "FAIL",
        "trigger_threshold_frozen": _TRIGGER_RATIO,
        "threshold_below_actual_material_headroom_rate": threshold_below_actual,
        "threshold_below_headroom_gate_pass": threshold_below_actual >= 0.75,
        "scalar_threshold_candidate_count": len(threshold_rows),
        "any_scalar_threshold_recovery_guardrails_pass": any_recovery_pass,
        "threshold_only_rescue_possible": threshold_only_rescue_possible,
        "original_policy": original.as_dict(),
        "best_balanced_accuracy_scalar_threshold": best.as_dict(),
        "always_adaptive": always_adaptive.as_dict(),
        "always_transferred": always_transferred.as_dict(),
        "oracle_material_headroom": oracle.as_dict(),
        "interpretation": {
            "trigger_retune_is_sufficient": False,
            "placement_only_policy_family_is_sufficient": False,
            "next_confirmatory_program_requires_fresh_worlds": True,
            "next_development_need": (
                "separate absolute recovery adequacy from relative placement headroom; "
                "do not retune the v0.7l trigger on the opened confirmatory worlds"
            ),
        },
    }
