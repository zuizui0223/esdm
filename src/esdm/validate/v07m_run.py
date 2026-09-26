"""Three-way absolute-adequacy-first calibration policy for v0.7m."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.simulate import simulate_observations
from .v07b_fixture import V07B_TRUTH
from .v07l_run import (
    _confirm_data,
    _heldout_score,
    _pilot_data,
    _posterior_summary,
)
from .v07i_selector import theta_from_posterior_means
from .v07m_fixture import (
    V07M_WORLDS,
    build_v07m_confirm_fixture,
    build_v07m_local_pilot_fixture,
    truth_sites_for_v07m_world,
)
from .v07m_policy import (
    V07M_EXPECTED_ACTIONS,
    decide_v07m_from_scores,
    decide_v07m_from_theta,
)


@dataclass(frozen=True, slots=True)
class V07MReplicate:
    world: str
    replicate: int
    pilot_seed: int
    confirm_seed: int
    adaptive_placement: tuple[int, ...]
    pilot_predicted_adaptive_worst_dynamic_sd: float
    pilot_predicted_transferred_worst_dynamic_sd: float
    pilot_predicted_adaptive_to_transferred_ratio: float
    policy_action: str
    policy_reason: str
    pilot_divergences: int
    adaptive_posterior_sds: dict
    transferred_posterior_sds: dict
    adaptive_posterior_means: dict
    adaptive_posterior_lows: dict
    adaptive_posterior_highs: dict
    transferred_posterior_means: dict
    transferred_posterior_lows: dict
    transferred_posterior_highs: dict
    adaptive_heldout_log_score: float
    transferred_heldout_log_score: float
    adaptive_divergences: int
    transferred_divergences: int

    def __post_init__(self) -> None:
        if self.world not in V07M_WORLDS:
            raise ValueError(f"unknown v0.7m world {self.world!r}")
        if self.policy_action not in {"adaptive", "transferred", "abstain"}:
            raise ValueError("v0.7m policy_action must be adaptive/transferred/abstain")
        placement = tuple(int(day) for day in self.adaptive_placement)
        if len(placement) != 4 or len(set(placement)) != 4:
            raise ValueError("v0.7m adaptive placement must have four unique days")
        object.__setattr__(self, "adaptive_placement", placement)

    @property
    def adaptive_worst_dynamic_sd(self) -> float:
        return max(
            float(self.adaptive_posterior_sds[target])
            for target in (
                "sp.occupancy.psi0_logit",
                "sp.occupancy.gamma_logit",
                "sp.occupancy.epsilon_logit",
            )
        )

    @property
    def transferred_worst_dynamic_sd(self) -> float:
        return max(
            float(self.transferred_posterior_sds[target])
            for target in (
                "sp.occupancy.psi0_logit",
                "sp.occupancy.gamma_logit",
                "sp.occupancy.epsilon_logit",
            )
        )

    @property
    def actual_ratio(self) -> float:
        return self.adaptive_worst_dynamic_sd / self.transferred_worst_dynamic_sd

    @property
    def oracle_action(self) -> str:
        return decide_v07m_from_scores(
            adaptive_placement=self.adaptive_placement,
            adaptive_worst_dynamic_sd=self.adaptive_worst_dynamic_sd,
            transferred_worst_dynamic_sd=self.transferred_worst_dynamic_sd,
        ).action

    @property
    def action_correct(self) -> bool:
        return self.policy_action == self.oracle_action

    @property
    def expected_action_correct(self) -> bool:
        return self.policy_action == V07M_EXPECTED_ACTIONS[self.world]

    @property
    def oracle_expected_action_correct(self) -> bool:
        return self.oracle_action == V07M_EXPECTED_ACTIONS[self.world]

    @property
    def policy_to_transferred_ratio(self) -> float | None:
        if self.policy_action == "abstain":
            return None
        if self.policy_action == "adaptive":
            return self.actual_ratio
        return 1.0

    @property
    def policy_heldout_log_score(self) -> float | None:
        if self.policy_action == "adaptive":
            return float(self.adaptive_heldout_log_score)
        if self.policy_action == "transferred":
            return float(self.transferred_heldout_log_score)
        return None

    def policy_mean(self, target: str) -> float:
        if self.policy_action == "adaptive":
            return float(self.adaptive_posterior_means[target])
        if self.policy_action == "transferred":
            return float(self.transferred_posterior_means[target])
        raise ValueError("abstain action has no deployed recovery estimate")

    def policy_covers_truth(self, target: str) -> bool:
        truth = truth_sites_for_v07m_world(self.world)[target]
        if self.policy_action == "adaptive":
            low = float(self.adaptive_posterior_lows[target])
            high = float(self.adaptive_posterior_highs[target])
        elif self.policy_action == "transferred":
            low = float(self.transferred_posterior_lows[target])
            high = float(self.transferred_posterior_highs[target])
        else:
            raise ValueError("abstain action has no deployed recovery interval")
        return low <= truth <= high


@dataclass(frozen=True, slots=True)
class V07MWorldSummary:
    world: str
    expected_action: str
    replicates: int
    fit_count: int
    pilot_expected_action_rate: float
    oracle_expected_action_rate: float
    action_accuracy: float
    policy_non_abstain_count: int
    policy_abstain_rate: float
    oracle_abstain_rate: float
    policy_mean_biases: dict
    policy_coverages: dict
    mean_policy_to_transferred_ratio: float | None
    policy_harm_rate: float | None
    mean_policy_heldout_log_score: float | None
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V07MSummary:
    worlds: dict
    replicates: int
    fit_count: int
    action_correct_count: int
    action_accuracy: float
    oracle_abstain_count: int
    pilot_abstain_true_positive: int
    pilot_abstain_false_positive: int
    pilot_abstain_true_negative: int
    pilot_abstain_false_negative: int
    abstain_sensitivity: float
    non_abstain_specificity: float
    mean_policy_to_transferred_ratio: float
    policy_harm_rate: float
    total_divergences: int


def run_v07m_replicate(
    *,
    world: str,
    replicate: int,
    pilot_seed: int,
    confirm_seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07MReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    name = str(world)
    if name not in V07M_WORLDS:
        raise KeyError(f"unknown v0.7m world {name!r}")
    if int(pilot_seed) == int(confirm_seed):
        raise ValueError("pilot and confirmatory seeds must be disjoint")

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }

    pilot = build_v07m_local_pilot_fixture(name)
    pilot_generated = simulate_observations(
        pilot.generator_model,
        pilot.generating_theta,
        pilot.covariates,
        theta_obs=pilot.generating_theta_obs,
        seed=int(pilot_seed),
    )
    pilot_fit = fit_numpyro(
        pilot.training_model,
        _pilot_data(pilot_generated.counts, pilot),
        pilot.covariates,
        rng_seed=int(pilot_seed) + 1,
        **fit_kwargs,
    )
    pilot_theta = theta_from_posterior_means(pilot_fit.samples)
    policy = decide_v07m_from_theta(pilot_theta)

    confirm = build_v07m_confirm_fixture(
        name,
        policy.adaptive_placement,
    )
    generated = simulate_observations(
        confirm.generator_model,
        confirm.generating_theta,
        confirm.covariates,
        theta_obs=confirm.generating_theta_obs,
        seed=int(confirm_seed),
    )
    adaptive_fit = fit_numpyro(
        confirm.adaptive_model,
        _confirm_data(generated.counts, confirm, adaptive=True),
        confirm.covariates,
        rng_seed=int(confirm_seed) + 1,
        **fit_kwargs,
    )
    transferred_fit = fit_numpyro(
        confirm.transferred_model,
        _confirm_data(generated.counts, confirm, adaptive=False),
        confirm.covariates,
        rng_seed=int(confirm_seed) + 2,
        **fit_kwargs,
    )

    a_means, a_lows, a_highs, a_sds = _posterior_summary(
        adaptive_fit.samples,
        credible_mass=credible_mass,
    )
    t_means, t_lows, t_highs, t_sds = _posterior_summary(
        transferred_fit.samples,
        credible_mass=credible_mass,
    )

    return V07MReplicate(
        world=name,
        replicate=int(replicate),
        pilot_seed=int(pilot_seed),
        confirm_seed=int(confirm_seed),
        adaptive_placement=policy.adaptive_placement,
        pilot_predicted_adaptive_worst_dynamic_sd=(
            policy.adaptive_worst_dynamic_sd
        ),
        pilot_predicted_transferred_worst_dynamic_sd=(
            policy.transferred_worst_dynamic_sd
        ),
        pilot_predicted_adaptive_to_transferred_ratio=(
            policy.adaptive_to_transferred_ratio
        ),
        policy_action=policy.action,
        policy_reason=policy.reason,
        pilot_divergences=int(pilot_fit.num_divergences),
        adaptive_posterior_sds=a_sds,
        transferred_posterior_sds=t_sds,
        adaptive_posterior_means=a_means,
        adaptive_posterior_lows=a_lows,
        adaptive_posterior_highs=a_highs,
        transferred_posterior_means=t_means,
        transferred_posterior_lows=t_lows,
        transferred_posterior_highs=t_highs,
        adaptive_heldout_log_score=_heldout_score(
            confirm.scoring_model,
            adaptive_fit.samples,
            confirm.covariates,
            generated.counts,
            confirm.heldout_keys,
        ),
        transferred_heldout_log_score=_heldout_score(
            confirm.scoring_model,
            transferred_fit.samples,
            confirm.covariates,
            generated.counts,
            confirm.heldout_keys,
        ),
        adaptive_divergences=int(adaptive_fit.num_divergences),
        transferred_divergences=int(transferred_fit.num_divergences),
    )


def _mean(values) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("mean requires at least one value")
    return math.fsum(rows) / len(rows)


def _summarize_world(world: str, rows) -> V07MWorldSummary:
    selected = tuple(row for row in rows if row.world == world)
    if len(selected) != 16:
        raise ValueError(f"v0.7m world {world!r} must contain 16 replicates")

    expected = V07M_EXPECTED_ACTIONS[world]
    deployed = tuple(row for row in selected if row.policy_action != "abstain")
    biases = {}
    coverages = {}
    if deployed:
        truth = truth_sites_for_v07m_world(world)
        for target in V07B_TRUTH:
            biases[target] = _mean(
                row.policy_mean(target) - truth[target]
                for row in deployed
            )
            coverages[target] = _mean(
                1.0 if row.policy_covers_truth(target) else 0.0
                for row in deployed
            )

    ratios = tuple(
        row.policy_to_transferred_ratio
        for row in deployed
        if row.policy_to_transferred_ratio is not None
    )
    heldout = tuple(
        row.policy_heldout_log_score
        for row in deployed
        if row.policy_heldout_log_score is not None
    )

    return V07MWorldSummary(
        world=world,
        expected_action=expected,
        replicates=len(selected),
        fit_count=3 * len(selected),
        pilot_expected_action_rate=_mean(
            1.0 if row.policy_action == expected else 0.0
            for row in selected
        ),
        oracle_expected_action_rate=_mean(
            1.0 if row.oracle_action == expected else 0.0
            for row in selected
        ),
        action_accuracy=_mean(
            1.0 if row.action_correct else 0.0
            for row in selected
        ),
        policy_non_abstain_count=len(deployed),
        policy_abstain_rate=_mean(
            1.0 if row.policy_action == "abstain" else 0.0
            for row in selected
        ),
        oracle_abstain_rate=_mean(
            1.0 if row.oracle_action == "abstain" else 0.0
            for row in selected
        ),
        policy_mean_biases=biases,
        policy_coverages=coverages,
        mean_policy_to_transferred_ratio=(
            None if not ratios else _mean(ratios)
        ),
        policy_harm_rate=(
            None
            if not ratios
            else _mean(1.0 if value > 1.0 else 0.0 for value in ratios)
        ),
        mean_policy_heldout_log_score=(
            None if not heldout else _mean(heldout)
        ),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.adaptive_divergences)
            + int(row.transferred_divergences)
            for row in selected
        ),
    )


def summarize_v07m(records: Sequence[V07MReplicate]) -> V07MSummary:
    rows = tuple(records)
    if len(rows) != 64:
        raise ValueError("v0.7m requires exactly 64 confirmatory records")
    worlds = {
        world: _summarize_world(world, rows)
        for world in V07M_WORLDS
    }

    tp = sum(
        row.policy_action == "abstain" and row.oracle_action == "abstain"
        for row in rows
    )
    fp = sum(
        row.policy_action == "abstain" and row.oracle_action != "abstain"
        for row in rows
    )
    tn = sum(
        row.policy_action != "abstain" and row.oracle_action != "abstain"
        for row in rows
    )
    fn = sum(
        row.policy_action != "abstain" and row.oracle_action == "abstain"
        for row in rows
    )
    sensitivity = tp / (tp + fn) if (tp + fn) else 1.0
    specificity = tn / (tn + fp) if (tn + fp) else 1.0

    deployed_ratios = tuple(
        row.policy_to_transferred_ratio
        for row in rows
        if row.policy_to_transferred_ratio is not None
    )

    return V07MSummary(
        worlds=worlds,
        replicates=len(rows),
        fit_count=3 * len(rows),
        action_correct_count=sum(row.action_correct for row in rows),
        action_accuracy=_mean(
            1.0 if row.action_correct else 0.0
            for row in rows
        ),
        oracle_abstain_count=sum(
            row.oracle_action == "abstain" for row in rows
        ),
        pilot_abstain_true_positive=tp,
        pilot_abstain_false_positive=fp,
        pilot_abstain_true_negative=tn,
        pilot_abstain_false_negative=fn,
        abstain_sensitivity=float(sensitivity),
        non_abstain_specificity=float(specificity),
        mean_policy_to_transferred_ratio=_mean(deployed_ratios),
        policy_harm_rate=_mean(
            1.0 if value > 1.0 else 0.0
            for value in deployed_ratios
        ),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.adaptive_divergences)
            + int(row.transferred_divergences)
            for row in rows
        ),
    )
