"""Deterministic budget-neutral design selectors for v0.4-R3a."""

from __future__ import annotations

import math


def _spatial_point(space, covariates) -> tuple[float, float]:
    key = (str(space), 15, 0)
    if key not in covariates:
        raise KeyError(f"missing selector covariates for {key!r}")
    values = covariates[key]
    if "precip_z_train" not in values:
        raise KeyError("precip_z_train")
    if "eastness_z_train" not in values:
        raise KeyError("eastness_z_train")
    point = (
        float(values["precip_z_train"]),
        float(values["eastness_z_train"]),
    )
    if any(not math.isfinite(value) for value in point):
        raise ValueError("spatial selector coordinates must be finite")
    return point


def spatial_maximin_sequence(
    train_spaces,
    covariates,
    *,
    count: int,
) -> tuple[str, ...]:
    """Return a deterministic environmental maximin sequence of training spaces."""

    spaces = tuple(str(space) for space in train_spaces)
    requested = int(count)
    if requested < 1 or requested > len(spaces):
        raise ValueError("invalid spatial maximin request")
    if len(set(spaces)) != len(spaces):
        raise ValueError("training spaces must be unique")

    points = {
        space: _spatial_point(space, covariates)
        for space in spaces
    }
    first = min(
        (
            (-(point[0] ** 2 + point[1] ** 2), space)
            for space, point in points.items()
        )
    )[1]
    selected = [first]
    remaining = set(spaces) - {first}

    while len(selected) < requested:
        scored = []
        for space in remaining:
            p, e = points[space]
            minimum_distance = min(
                (p - points[other][0]) ** 2
                + (e - points[other][1]) ** 2
                for other in selected
            )
            scored.append((-minimum_distance, space))
        chosen = min(scored)[1]
        selected.append(chosen)
        remaining.remove(chosen)

    return tuple(selected)


def _temporal_point(doy: int, hour: int) -> tuple[float, float, float, float]:
    season = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
    daily = 2.0 * math.pi * float(hour) / 24.0
    return (
        math.sin(season),
        math.cos(season),
        math.sin(daily),
        math.cos(daily),
    )


def temporal_maximin_sequence(
    doy_values,
    hour_values,
    *,
    count: int,
) -> tuple[tuple[int, int], ...]:
    """Return a deterministic maximin sequence in cyclic season/hour space."""

    candidates = tuple(
        sorted(
            (int(doy), int(hour))
            for doy in doy_values
            for hour in hour_values
        )
    )
    requested = int(count)
    if requested < 1 or requested > len(candidates):
        raise ValueError("invalid temporal maximin request")
    if len(set(candidates)) != len(candidates):
        raise ValueError("temporal candidates must be unique")

    points = {
        key: _temporal_point(*key)
        for key in candidates
    }
    selected = [candidates[0]]
    remaining = set(candidates) - {candidates[0]}

    while len(selected) < requested:
        scored = []
        for candidate in remaining:
            point = points[candidate]
            minimum_distance = min(
                sum(
                    (value - points[other][index]) ** 2
                    for index, value in enumerate(point)
                )
                for other in selected
            )
            scored.append((-minimum_distance, candidate))
        chosen = min(scored)[1]
        selected.append(chosen)
        remaining.remove(chosen)

    return tuple(selected)
