"""Generic v0.3 known-truth benchmark worlds and repeated-fit diagnostics.

The worlds are deliberately ecological-domain neutral. They exercise the generative
contracts around suitability, observation effort, omitted environmental structure, and
process knockout before any interaction family is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability
from esdm.simulate import simulate_presence_only
from esdm.simulate.misspecified import (
    effort_gradient_apparent_slope,
    omitted_driver_apparent_slope,
)


@dataclass(frozen=True, slots=True)
class KnownTruthWorld:
    name: str
    generating_model: Model
    fitting_model: Model
    generating_covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    fitting_covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    generating_theta: Mapping[str, Mapping[str, float]]
    truth: Mapping[str, float]
    target_parameter: str
    expected_apparent_value: float
    world_class: str

    def __post_init__(self) -> None:
        if self.world_class not in {"in_model", "misspecified", "knockout"}:
            raise ValueError("unknown known-truth world_class")
        if self.target_parameter not in self.truth:
            raise ValueError("truth must contain target_parameter")
        object.__setattr__(
            self,
            "generating_covariates",
            MappingProxyType({key: MappingProxyType(dict(values)) for key, values in self.generating_covariates.items()}),
        )
        object.__setattr__(
            self,
            "fitting_covariates",
            MappingProxyType({key: MappingProxyType(dict(values)) for key, values in self.fitting_covariates.items()}),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({species: MappingProxyType(dict(values)) for species, values in self.generating_theta.items()}),
        )
        object.__setattr__(self, "truth", MappingProxyType(dict(self.truth)))


@dataclass(frozen=True, slots=True)
class BenchmarkReplicate:
    world: str
    replicate: int
    posterior_mean: float
    interval_low: float
    interval_high: float
    truth: float
    expected_apparent: float
    num_divergences: int
    world_class: str = "unspecified"

    @property
    def covers_truth(self) -> bool:
        return self.interval_low <= self.truth <= self.interval_high

    @property
    def covers_expected(self) -> bool:
        return self.interval_low <= self.expected_apparent <= self.interval_high

    @property
    def nonzero(self) -> bool:
        return self.interval_low > 0.0 or self.interval_high < 0.0


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    world: str
    replicates: int
    mean_posterior: float
    mean_bias_from_truth: float
    mean_bias_from_expected: float
    truth_coverage: float
    expected_coverage: float
    nonzero_rate: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class KnownTruthBenchmarkResult:
    replicates: tuple[BenchmarkReplicate, ...]
    summary: Mapping[str, BenchmarkSummary]

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", MappingProxyType(dict(self.summary)))


@dataclass(frozen=True, slots=True)
class V03PromotionGateConfig:
    """Frozen numerical gate corresponding to docs/validation/V03_KNOWN_TRUTH_GATE.md."""

    replicates_per_world: int = 100
    correct_max_abs_bias: float = 0.15
    correct_min_truth_coverage: float = 0.80
    correct_max_truth_coverage: float = 0.98
    correct_min_nonzero_rate: float = 0.80
    knockout_max_abs_mean: float = 0.15
    knockout_min_truth_coverage: float = 0.80
    knockout_max_nonzero_rate: float = 0.15
    misspecified_min_positive_bias: float = 0.25
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class PromotionGateCheck:
    name: str
    passed: bool
    observed: float | bool | int
    criterion: str


@dataclass(frozen=True, slots=True)
class V03PromotionGateDecision:
    passed: bool
    checks: tuple[PromotionGateCheck, ...]


def summarize_known_truth_benchmark(
    records: Sequence[BenchmarkReplicate],
) -> dict[str, BenchmarkSummary]:
    rows = tuple(records)
    if not rows:
        raise ValueError("benchmark records must be non-empty")
    grouped: dict[str, list[BenchmarkReplicate]] = {}
    for row in rows:
        grouped.setdefault(row.world, []).append(row)
    output: dict[str, BenchmarkSummary] = {}
    for world, group in grouped.items():
        n = len(group)
        mean_posterior = sum(row.posterior_mean for row in group) / n
        output[world] = BenchmarkSummary(
            world=world,
            replicates=n,
            mean_posterior=mean_posterior,
            mean_bias_from_truth=sum(row.posterior_mean - row.truth for row in group) / n,
            mean_bias_from_expected=sum(row.posterior_mean - row.expected_apparent for row in group) / n,
            truth_coverage=sum(row.covers_truth for row in group) / n,
            expected_coverage=sum(row.covers_expected for row in group) / n,
            nonzero_rate=sum(row.nonzero for row in group) / n,
            total_divergences=sum(int(row.num_divergences) for row in group),
        )
    return output


def evaluate_v03_promotion_gate(
    summaries: Mapping[str, BenchmarkSummary],
    *,
    config: V03PromotionGateConfig | None = None,
) -> V03PromotionGateDecision:
    """Mechanically evaluate the pre-outcome v0.3 known-truth promotion rules."""

    cfg = V03PromotionGateConfig() if config is None else config
    required = (
        "correct_effort",
        "wrong_effort_geometry",
        "hidden_driver",
        "suitability_knockout",
    )
    missing = [name for name in required if name not in summaries]
    if missing:
        raise ValueError(f"promotion summaries missing worlds: {missing}")

    checks: list[PromotionGateCheck] = []

    def add(name: str, passed: bool, observed, criterion: str) -> None:
        checks.append(PromotionGateCheck(name, bool(passed), observed, criterion))

    def divergence_check(name: str, row: BenchmarkSummary) -> None:
        mean_divergences = row.total_divergences / row.replicates if row.replicates else math.inf
        add(
            f"{name}_divergences",
            mean_divergences <= cfg.max_mean_divergences_per_fit,
            mean_divergences,
            f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}",
        )

    correct = summaries["correct_effort"]
    add(
        "correct_effort_replicates",
        correct.replicates == cfg.replicates_per_world,
        correct.replicates,
        f"replicates == {cfg.replicates_per_world}",
    )
    add(
        "correct_effort_bias",
        abs(correct.mean_bias_from_truth) <= cfg.correct_max_abs_bias,
        correct.mean_bias_from_truth,
        f"abs(mean bias from truth) <= {cfg.correct_max_abs_bias}",
    )
    add(
        "correct_effort_coverage",
        cfg.correct_min_truth_coverage <= correct.truth_coverage <= cfg.correct_max_truth_coverage,
        correct.truth_coverage,
        f"truth coverage in [{cfg.correct_min_truth_coverage}, {cfg.correct_max_truth_coverage}]",
    )
    add(
        "correct_effort_nonzero",
        correct.nonzero_rate >= cfg.correct_min_nonzero_rate,
        correct.nonzero_rate,
        f"nonzero interval rate >= {cfg.correct_min_nonzero_rate}",
    )
    divergence_check("correct_effort", correct)

    knockout = summaries["suitability_knockout"]
    add(
        "suitability_knockout_replicates",
        knockout.replicates == cfg.replicates_per_world,
        knockout.replicates,
        f"replicates == {cfg.replicates_per_world}",
    )
    add(
        "suitability_knockout_mean",
        abs(knockout.mean_posterior) <= cfg.knockout_max_abs_mean,
        knockout.mean_posterior,
        f"abs(mean posterior) <= {cfg.knockout_max_abs_mean}",
    )
    add(
        "suitability_knockout_coverage",
        knockout.truth_coverage >= cfg.knockout_min_truth_coverage,
        knockout.truth_coverage,
        f"zero coverage >= {cfg.knockout_min_truth_coverage}",
    )
    add(
        "suitability_knockout_nonzero",
        knockout.nonzero_rate <= cfg.knockout_max_nonzero_rate,
        knockout.nonzero_rate,
        f"nonzero interval rate <= {cfg.knockout_max_nonzero_rate}",
    )
    divergence_check("suitability_knockout", knockout)

    for world_name, check_name in (
        ("wrong_effort_geometry", "wrong_effort_negative_control"),
        ("hidden_driver", "hidden_driver_negative_control"),
    ):
        row = summaries[world_name]
        add(
            f"{world_name}_replicates",
            row.replicates == cfg.replicates_per_world,
            row.replicates,
            f"replicates == {cfg.replicates_per_world}",
        )
        negative_control_pass = (
            row.mean_bias_from_truth >= cfg.misspecified_min_positive_bias
            and abs(row.mean_bias_from_expected) < abs(row.mean_bias_from_truth)
        )
        add(
            check_name,
            negative_control_pass,
            row.mean_bias_from_truth,
            (
                f"bias from truth >= {cfg.misspecified_min_positive_bias} and "
                "mean posterior closer to predeclared apparent value than ecological truth"
            ),
        )
        divergence_check(world_name, row)

    check_tuple = tuple(checks)
    return V03PromotionGateDecision(
        passed=all(check.passed for check in check_tuple),
        checks=check_tuple,
    )


def _quantile(values, probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("posterior draws must be non-empty")
    p = float(probability)
    if not 0.0 <= p <= 1.0:
        raise ValueError("quantile probability must be in [0, 1]")
    if len(ordered) == 1:
        return ordered[0]
    position = p * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _grid_and_x() -> tuple[Grid, tuple[float, ...]]:
    x = (-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75)
    grid = Grid(space=tuple(f"s{i}" for i in range(len(x))), doy=(1,), hour=(0,))
    return grid, x


def _covariates(grid: Grid, **columns: tuple[float, ...]):
    for name, values in columns.items():
        if len(values) != len(grid.keys):
            raise ValueError(f"covariate {name!r} length does not match domain")
    return {
        key: {name: float(values[index]) for name, values in columns.items()}
        for index, key in enumerate(grid.keys)
    }


def _suitability(*covariates: str) -> LinearSuitability:
    coefficient_parameters = {
        covariate: ("beta_x" if covariate == "x" else f"beta_{covariate}")
        for covariate in covariates
    }
    return LinearSuitability(
        covariates=tuple(covariates),
        intercept_parameter="intercept",
        coefficient_parameters=coefficient_parameters,
    )


def _model(grid: Grid, process, effort_values) -> Model:
    effort = EffortField({
        key: float(value)
        for key, value in zip(grid.keys, effort_values, strict=True)
    })
    stream = PresenceOnly(
        name="records",
        effort=effort,
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    return Model(domain=grid, species={"sp": (process,)}, streams=(stream,))


def make_v03_known_truth_worlds() -> tuple[KnownTruthWorld, ...]:
    """Return the frozen generic v0.3 benchmark universe.

    The first and fourth worlds are in-model/knockout controls. The middle two are
    deliberate misspecifications and therefore are not SBC worlds.
    """

    grid, x = _grid_and_x()
    target = "sp.suitability.beta_x"

    correct_effort = (5.0, 8.0, 5.0, 8.0, 8.0, 5.0, 8.0, 5.0)
    correct_process = _suitability("x")
    correct_model = _model(grid, correct_process, correct_effort)
    correct_covariates = _covariates(grid, x=x)
    correct_truth = 0.6
    correct = KnownTruthWorld(
        name="correct_effort",
        generating_model=correct_model,
        fitting_model=correct_model,
        generating_covariates=correct_covariates,
        fitting_covariates=correct_covariates,
        generating_theta={"sp": {"intercept": 2.0, "beta_x": correct_truth}},
        truth={target: correct_truth},
        target_parameter=target,
        expected_apparent_value=correct_truth,
        world_class="in_model",
    )

    gamma_effort = 0.7
    effort_scale = 5.0
    true_effort = tuple(effort_scale * math.exp(gamma_effort * value) for value in x)
    wrong_fit_effort = tuple(effort_scale for _ in x)
    wrong_generating_model = _model(grid, _suitability("x"), true_effort)
    wrong_fitting_model = _model(grid, _suitability("x"), wrong_fit_effort)
    wrong_truth = 0.6
    wrong_expected = effort_gradient_apparent_slope(
        true_beta=wrong_truth,
        covariate=x,
        true_effort=true_effort,
        assumed_effort=effort_scale,
    )
    wrong = KnownTruthWorld(
        name="wrong_effort_geometry",
        generating_model=wrong_generating_model,
        fitting_model=wrong_fitting_model,
        generating_covariates=correct_covariates,
        fitting_covariates=correct_covariates,
        generating_theta={"sp": {"intercept": 2.0, "beta_x": wrong_truth}},
        truth={target: wrong_truth},
        target_parameter=target,
        expected_apparent_value=wrong_expected,
        world_class="misspecified",
    )

    hidden = tuple(0.8 * value for value in x)
    hidden_generating_model = _model(grid, _suitability("x", "hidden"), correct_effort)
    hidden_fitting_model = _model(grid, _suitability("x"), correct_effort)
    beta_x = 0.4
    beta_hidden = 0.75
    hidden_expected = omitted_driver_apparent_slope(
        true_beta=beta_x,
        omitted_beta=beta_hidden,
        covariate=x,
        hidden_driver=hidden,
    )
    hidden_world = KnownTruthWorld(
        name="hidden_driver",
        generating_model=hidden_generating_model,
        fitting_model=hidden_fitting_model,
        generating_covariates=_covariates(grid, x=x, hidden=hidden),
        fitting_covariates=correct_covariates,
        generating_theta={
            "sp": {
                "intercept": 2.0,
                "beta_x": beta_x,
                "beta_hidden": beta_hidden,
            }
        },
        truth={target: beta_x},
        target_parameter=target,
        expected_apparent_value=hidden_expected,
        world_class="misspecified",
    )

    full_knockout_fit = _model(grid, _suitability("x"), correct_effort)
    knockout_generating = full_knockout_fit.knockout("sp", "suitability")
    knockout = KnownTruthWorld(
        name="suitability_knockout",
        generating_model=knockout_generating,
        fitting_model=full_knockout_fit,
        generating_covariates=correct_covariates,
        fitting_covariates=correct_covariates,
        generating_theta={"sp": {}},
        truth={target: 0.0},
        target_parameter=target,
        expected_apparent_value=0.0,
        world_class="knockout",
    )

    return (correct, wrong, hidden_world, knockout)


def run_v03_known_truth_benchmark(
    *,
    world_names: Sequence[str] | None = None,
    replicates: int,
    base_seed: int = 0,
    num_warmup: int = 250,
    num_samples: int = 300,
    credible_mass: float = 0.9,
    progress_bar: bool = False,
) -> KnownTruthBenchmarkResult:
    """Repeatedly simulate and fit selected v0.3 known-truth worlds with NumPyro.

    CI should use small smoke settings. Promotion studies can increase `replicates`,
    warmup, and posterior draws without changing the estimand or world definitions.
    """

    from esdm.model.backend_numpyro import fit_numpyro

    n_rep = int(replicates)
    if n_rep < 1:
        raise ValueError("replicates must be positive")
    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")
    all_worlds = {world.name: world for world in make_v03_known_truth_worlds()}
    selected_names = tuple(all_worlds) if world_names is None else tuple(world_names)
    if not selected_names or len(set(selected_names)) != len(selected_names):
        raise ValueError("world_names must be a non-empty unique sequence")
    unknown = set(selected_names) - set(all_worlds)
    if unknown:
        raise KeyError(f"unknown known-truth worlds: {sorted(unknown)}")

    alpha = (1.0 - mass) / 2.0
    records: list[BenchmarkReplicate] = []
    for world_index, name in enumerate(selected_names):
        world = all_worlds[name]
        for replicate in range(n_rep):
            seed = int(base_seed) + world_index * 100_000 + replicate * 17
            generated = simulate_presence_only(
                world.generating_model,
                world.generating_theta,
                world.generating_covariates,
                seed=seed,
            )
            fit = fit_numpyro(
                world.fitting_model,
                generated.counts,
                world.fitting_covariates,
                rng_seed=seed + 1,
                num_warmup=int(num_warmup),
                num_samples=int(num_samples),
                num_chains=1,
                progress_bar=bool(progress_bar),
            )
            draws = tuple(float(value) for value in fit.samples[world.target_parameter])
            posterior_mean = sum(draws) / len(draws)
            records.append(
                BenchmarkReplicate(
                    world=name,
                    replicate=replicate,
                    posterior_mean=posterior_mean,
                    interval_low=_quantile(draws, alpha),
                    interval_high=_quantile(draws, 1.0 - alpha),
                    truth=float(world.truth[world.target_parameter]),
                    expected_apparent=float(world.expected_apparent_value),
                    num_divergences=fit.num_divergences,
                    world_class=world.world_class,
                )
            )

    record_tuple = tuple(records)
    return KnownTruthBenchmarkResult(
        replicates=record_tuple,
        summary=summarize_known_truth_benchmark(record_tuple),
    )
