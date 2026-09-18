import math

import pytest

from esdm.domain import Context
from esdm.process import LinearSuitability, Process, ProcessContribution


class _Vector(tuple):
    def __new__(cls, values):
        return super().__new__(cls, (float(value) for value in values))

    def __add__(self, other):
        return _Vector(a + b for a, b in zip(self, other, strict=True))

    __radd__ = __add__

    def __mul__(self, scalar):
        return _Vector(value * float(scalar) for value in self)

    __rmul__ = __mul__


class _ArrayModule:
    @staticmethod
    def asarray(value):
        if isinstance(value, (tuple, list, _Vector)):
            return _Vector(value)
        return float(value)

    @staticmethod
    def broadcast_to(value, shape):
        return _Vector(value for _ in range(shape[0]))


def test_suitability_exposes_generic_contribution_without_changing_value():
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    ctx = Context("s1", 1, 0)
    theta = {"intercept": math.log(2.0), "beta_x": math.log(3.0)}
    covariates = {"x": 1.0}

    contribution = process.contribution(ctx, theta, covariates)

    assert isinstance(contribution, ProcessContribution)
    assert contribution.channel == "log_intensity"
    assert contribution.labels == ()
    assert contribution.values == process.log_intensity(ctx, theta, covariates)


def test_suitability_array_contribution_preserves_context_axis():
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    keys = (("a", 1, 0), ("b", 1, 0))
    theta = {"intercept": 0.2, "beta_x": 0.5}
    covariates = {"x": _Vector((-1.0, 2.0))}

    contribution = process.contribution_array(
        keys,
        theta,
        covariates,
        array_module=_ArrayModule,
    )

    assert contribution.channel == "log_intensity"
    assert contribution.labels == ()
    assert tuple(contribution.values) == pytest.approx((-0.3, 1.2))


def test_process_protocol_retains_v03_intensity_compatibility_surface():
    assert hasattr(Process, "contribution")
    assert hasattr(Process, "contribution_array")
    assert hasattr(Process, "log_intensity")
    assert hasattr(Process, "log_intensity_array")
