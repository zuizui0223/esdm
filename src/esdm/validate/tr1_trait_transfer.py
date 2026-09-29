"""Known-truth trait-transfer programme for unseen taxa."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import random
from typing import Iterable, Sequence


TR1_INTERCEPT = -0.2
TR1_ENVIRONMENT_BETA = 1.0
TR1_POSITIVE_TRAIT_BETA = 1.0
TR1_NULL_TRAIT_BETA = 0.0
TR1_TAXON_COUNT = 30
TR1_TRAINING_TAXA = 20
TR1_HELDOUT_TAXA = 10
TR1_ENVIRONMENT_COUNT = 41
TR1_POSITIVE_REPLICATES = 32
TR1_NULL_REPLICATES = 32
TR1_POSITIVE_BASE_SEED = 20261101
TR1_NULL_BASE_SEED = 20262101
TR1_SEED_STRIDE = 97


@dataclass(frozen=True, slots=True)
class TR1Replicate:
    world: str
    replicate: int
    seed: int
    environment_only_heldout_log_score: float
    environment_trait_heldout_log_score: float
    fitted_trait_coefficient: float
    lower_iterations: int
    full_iterations: int

    @property
    def trait_gain(self) -> float:
        return (
            float(self.environment_trait_heldout_log_score)
            - float(self.environment_only_heldout_log_score)
        )

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["trait_gain"] = self.trait_gain
        return value


@dataclass(frozen=True, slots=True)
class TR1WorldSummary:
    world: str
    replicates: int
    mean_gain: float
    minimum_gain: float
    maximum_gain: float
    positive_gain_rate: float
    material_gain_count: int
    material_gain_threshold: float
    mean_fitted_trait_coefficient: float
    mean_trait_coefficient_bias: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def trait_values() -> tuple[float, ...]:
    return tuple(-1.45 + 0.10 * index for index in range(TR1_TAXON_COUNT))


def environment_values() -> tuple[float, ...]:
    return tuple(-2.0 + 0.10 * index for index in range(TR1_ENVIRONMENT_COUNT))


def heldout_taxon_indices() -> tuple[int, ...]:
    values = tuple(index for index in range(TR1_TAXON_COUNT) if index % 3 == 1)
    if len(values) != TR1_HELDOUT_TAXA:
        raise AssertionError("TR1 heldout taxon rule drifted")
    return values


def training_taxon_indices() -> tuple[int, ...]:
    heldout = set(heldout_taxon_indices())
    values = tuple(index for index in range(TR1_TAXON_COUNT) if index not in heldout)
    if len(values) != TR1_TRAINING_TAXA:
        raise AssertionError("TR1 training taxon count drifted")
    return values


def seed_for(world: str, replicate: int) -> int:
    index = int(replicate)
    if not 0 <= index < 32:
        raise ValueError("TR1 replicate must lie in [0, 31]")
    if world == "positive":
        return TR1_POSITIVE_BASE_SEED + TR1_SEED_STRIDE * index
    if world == "null":
        return TR1_NULL_BASE_SEED + TR1_SEED_STRIDE * index
    raise ValueError("TR1 world must be 'positive' or 'null'")


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _log_bernoulli_probability(y: int, probability: float) -> float:
    p = min(max(float(probability), 1e-15), 1.0 - 1e-15)
    return math.log(p) if int(y) == 1 else math.log1p(-p)


def _solve_linear(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> tuple[float, ...]:
    n = len(vector)
    augmented = [
        [float(matrix[row][col]) for col in range(n)] + [float(vector[row])]
        for row in range(n)
    ]
    for pivot in range(n):
        best = max(range(pivot, n), key=lambda row: abs(augmented[row][pivot]))
        if abs(augmented[best][pivot]) < 1e-12:
            raise ValueError("logistic information matrix is singular")
        if best != pivot:
            augmented[pivot], augmented[best] = augmented[best], augmented[pivot]
        scale = augmented[pivot][pivot]
        for col in range(pivot, n + 1):
            augmented[pivot][col] /= scale
        for row in range(n):
            if row == pivot:
                continue
            factor = augmented[row][pivot]
            if factor == 0.0:
                continue
            for col in range(pivot, n + 1):
                augmented[row][col] -= factor * augmented[pivot][col]
    return tuple(augmented[row][n] for row in range(n))


def _log_likelihood(
    rows: Sequence[tuple[tuple[float, ...], int]],
    coefficients: Sequence[float],
) -> float:
    total = 0.0
    for features, y in rows:
        eta = math.fsum(
            coefficient * feature
            for coefficient, feature in zip(coefficients, features)
        )
        p = _sigmoid(eta)
        total += _log_bernoulli_probability(y, p)
    return total


def fit_logistic(
    rows: Sequence[tuple[tuple[float, ...], int]],
    *,
    maximum_iterations: int = 100,
    tolerance: float = 1e-9,
    coefficient_limit: float = 40.0,
) -> tuple[tuple[float, ...], int]:
    if not rows:
        raise ValueError("logistic fit requires non-empty rows")
    dimension = len(rows[0][0])
    if dimension < 1:
        raise ValueError("logistic fit requires at least one feature")
    if any(len(features) != dimension for features, _ in rows):
        raise ValueError("logistic feature dimensions are inconsistent")
    if len({int(y) for _, y in rows}) < 2:
        raise ValueError("logistic fit requires both response classes")

    coefficients = [0.0] * dimension
    previous = _log_likelihood(rows, coefficients)

    for iteration in range(1, maximum_iterations + 1):
        gradient = [0.0] * dimension
        information = [[0.0] * dimension for _ in range(dimension)]

        for features, y in rows:
            eta = math.fsum(
                coefficient * feature
                for coefficient, feature in zip(coefficients, features)
            )
            p = _sigmoid(eta)
            weight = max(p * (1.0 - p), 1e-14)
            residual = float(y) - p
            for i in range(dimension):
                gradient[i] += features[i] * residual
                for j in range(dimension):
                    information[i][j] += weight * features[i] * features[j]

        step = _solve_linear(information, gradient)
        scale = 1.0
        accepted = None
        accepted_ll = None
        for _ in range(30):
            candidate = [
                coefficient + scale * delta
                for coefficient, delta in zip(coefficients, step)
            ]
            if max(abs(value) for value in candidate) > coefficient_limit:
                scale *= 0.5
                continue
            candidate_ll = _log_likelihood(rows, candidate)
            if math.isfinite(candidate_ll) and candidate_ll >= previous - 1e-10:
                accepted = candidate
                accepted_ll = candidate_ll
                break
            scale *= 0.5
        if accepted is None or accepted_ll is None:
            raise ValueError("logistic Newton step failed closed")

        change = max(
            abs(new - old)
            for new, old in zip(accepted, coefficients)
        )
        coefficients = accepted
        previous = accepted_ll
        if change <= tolerance:
            return tuple(coefficients), iteration

    raise ValueError("logistic fit did not converge within frozen iteration limit")


def _world_beta(world: str) -> float:
    if world == "positive":
        return TR1_POSITIVE_TRAIT_BETA
    if world == "null":
        return TR1_NULL_TRAIT_BETA
    raise ValueError("TR1 world must be 'positive' or 'null'")


def generate_rows(
    *,
    world: str,
    seed: int,
) -> tuple[
    tuple[tuple[int, float, float, int], ...],
    tuple[tuple[int, float, float, int], ...],
]:
    rng = random.Random(int(seed))
    beta_trait = _world_beta(world)
    traits = trait_values()
    environments = environment_values()
    heldout = set(heldout_taxon_indices())
    train_rows = []
    heldout_rows = []

    for taxon_index, trait in enumerate(traits):
        target = heldout_rows if taxon_index in heldout else train_rows
        for environment in environments:
            eta = (
                TR1_INTERCEPT
                + TR1_ENVIRONMENT_BETA * environment
                + beta_trait * trait
            )
            probability = _sigmoid(eta)
            y = 1 if rng.random() < probability else 0
            target.append((taxon_index, environment, trait, y))

    return tuple(train_rows), tuple(heldout_rows)


def _score_rows(
    rows: Sequence[tuple[int, float, float, int]],
    coefficients: Sequence[float],
    *,
    include_trait: bool,
) -> float:
    scores = []
    for _, environment, trait, y in rows:
        features = (
            (1.0, environment, trait)
            if include_trait
            else (1.0, environment)
        )
        eta = math.fsum(
            coefficient * feature
            for coefficient, feature in zip(coefficients, features)
        )
        scores.append(_log_bernoulli_probability(y, _sigmoid(eta)))
    return math.fsum(scores) / len(scores)


def run_tr1_replicate(
    *,
    world: str,
    replicate: int,
) -> TR1Replicate:
    seed = seed_for(world, replicate)
    train, heldout = generate_rows(world=world, seed=seed)

    lower_fit_rows = tuple(
        ((1.0, environment), y)
        for _, environment, _, y in train
    )
    full_fit_rows = tuple(
        ((1.0, environment, trait), y)
        for _, environment, trait, y in train
    )

    lower_coef, lower_iterations = fit_logistic(lower_fit_rows)
    full_coef, full_iterations = fit_logistic(full_fit_rows)

    return TR1Replicate(
        world=world,
        replicate=int(replicate),
        seed=seed,
        environment_only_heldout_log_score=_score_rows(
            heldout,
            lower_coef,
            include_trait=False,
        ),
        environment_trait_heldout_log_score=_score_rows(
            heldout,
            full_coef,
            include_trait=True,
        ),
        fitted_trait_coefficient=float(full_coef[2]),
        lower_iterations=int(lower_iterations),
        full_iterations=int(full_iterations),
    )


def summarize_tr1_world(
    rows: Iterable[TR1Replicate],
    *,
    material_gain_threshold: float = 0.01,
) -> TR1WorldSummary:
    records = tuple(rows)
    if not records:
        raise ValueError("TR1 summary requires records")
    worlds = {row.world for row in records}
    if len(worlds) != 1:
        raise ValueError("TR1 world summary cannot mix positive and null worlds")
    world = next(iter(worlds))
    gains = tuple(row.trait_gain for row in records)
    fitted = tuple(row.fitted_trait_coefficient for row in records)
    truth = _world_beta(world)
    return TR1WorldSummary(
        world=world,
        replicates=len(records),
        mean_gain=math.fsum(gains) / len(gains),
        minimum_gain=min(gains),
        maximum_gain=max(gains),
        positive_gain_rate=sum(gain > 0.0 for gain in gains) / len(gains),
        material_gain_count=sum(
            gain > material_gain_threshold for gain in gains
        ),
        material_gain_threshold=float(material_gain_threshold),
        mean_fitted_trait_coefficient=math.fsum(fitted) / len(fitted),
        mean_trait_coefficient_bias=(
            math.fsum(value - truth for value in fitted) / len(fitted)
        ),
    )
