import math

import pytest

from esdm.observe import MultiLogLinearEffort


class _Vector(tuple):
    def __new__(cls, values):
        return super().__new__(cls, (float(value) for value in values))

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return _Vector(value + float(other) for value in self)
        return _Vector(a + b for a, b in zip(self, other, strict=True))

    __radd__ = __add__

    def __mul__(self, scalar):
        return _Vector(value * float(scalar) for value in self)

    __rmul__ = __mul__


class _ArrayModule:
    @staticmethod
    def zeros(shape):
        return _Vector(0.0 for _ in range(shape[0]))

    @staticmethod
    def asarray(values):
        return _Vector(values)

    @staticmethod
    def exp(values):
        return _Vector(math.exp(value) for value in values)


def test_multi_log_linear_effort_scalar_and_priors():
    effort = MultiLogLinearEffort(
        baseline=4.0,
        covariates=("precip", "season", "hour"),
        coefficient_parameters={
            "precip": "gamma_precip",
            "season": "gamma_season",
            "hour": "gamma_hour",
        },
    )
    key = ("s1", 15, 6)
    theta = {
        "gamma_precip": 0.35,
        "gamma_season": 0.30,
        "gamma_hour": -0.25,
    }
    covariates = {
        key: {
            "precip": 1.0,
            "season": 0.5,
            "hour": -1.0,
        }
    }

    expected = 4.0 * math.exp(0.35 + 0.30 * 0.5 + (-0.25) * (-1.0))
    assert effort.at(key, theta=theta, covariates=covariates) == pytest.approx(
        expected
    )
    assert set(effort.priors()) == {
        "gamma_precip",
        "gamma_season",
        "gamma_hour",
    }
    assert effort.requires == frozenset({"precip", "season", "hour"})


def test_multi_log_linear_effort_array_is_context_vectorized():
    effort = MultiLogLinearEffort(
        baseline=2.0,
        covariates=("x", "t"),
        coefficient_parameters={
            "x": "gamma_x",
            "t": "gamma_t",
        },
    )
    keys = (("a", 1, 0), ("b", 1, 6), ("c", 1, 12))
    theta = {"gamma_x": 0.4, "gamma_t": -0.2}
    covariates = {
        keys[0]: {"x": -1.0, "t": 0.0},
        keys[1]: {"x": 0.5, "t": 1.0},
        keys[2]: {"x": 2.0, "t": -1.0},
    }

    observed = effort.array(
        keys,
        theta=theta,
        covariates=covariates,
        array_module=_ArrayModule,
    )
    expected = (
        2.0 * math.exp(-0.4),
        2.0 * math.exp(0.2 - 0.2),
        2.0 * math.exp(0.8 + 0.2),
    )
    assert tuple(observed) == pytest.approx(expected)
    assert effort.structural_exposure_mask(keys) == (True, True, True)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "baseline": 0.0,
            "covariates": ("x",),
            "coefficient_parameters": {"x": "gamma_x"},
        },
        {
            "baseline": 1.0,
            "covariates": ("x", "x"),
            "coefficient_parameters": {"x": "gamma_x"},
        },
        {
            "baseline": 1.0,
            "covariates": ("x", "t"),
            "coefficient_parameters": {"x": "gamma_x"},
        },
        {
            "baseline": 1.0,
            "covariates": ("x", "t"),
            "coefficient_parameters": {
                "x": "gamma_shared",
                "t": "gamma_shared",
            },
        },
    ],
)
def test_multi_log_linear_effort_rejects_invalid_declarations(kwargs):
    with pytest.raises((ValueError, TypeError)):
        MultiLogLinearEffort(**kwargs)


def test_multi_log_linear_effort_requires_all_parameters_and_covariates():
    effort = MultiLogLinearEffort(
        baseline=1.0,
        covariates=("x", "t"),
        coefficient_parameters={"x": "gamma_x", "t": "gamma_t"},
    )
    key = ("a", 1, 0)

    with pytest.raises(KeyError, match="gamma_t"):
        effort.at(
            key,
            theta={"gamma_x": 0.2},
            covariates={key: {"x": 1.0, "t": 0.5}},
        )
    with pytest.raises(KeyError, match="t"):
        effort.at(
            key,
            theta={"gamma_x": 0.2, "gamma_t": 0.1},
            covariates={key: {"x": 1.0}},
        )
