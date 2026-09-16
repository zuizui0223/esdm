import math
import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability
from esdm.simulate import simulate_presence_only


def make_model():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    process = LinearSuitability(
        covariates=("env",),
        intercept_parameter="alpha",
        coefficient_parameters={"env": "beta"},
    )
    effort = EffortField({("a", 1, 0): 1.0, ("b", 1, 0): 4.0})
    stream = PresenceOnly("inat", effort=effort, informs=frozenset({"suitability"}))
    return Model(grid, {"sp": (process,)}, (stream,))


def test_presence_only_rate_uses_ecology_times_effort():
    model = make_model()
    covariates = {("a", 1, 0): {"env": 0.0}, ("b", 1, 0): {"env": 0.0}}
    theta = {"sp": {"alpha": math.log(2.0), "beta": 0.0}}
    fields = model.latent_fields(theta, covariates)
    stream = model.streams[0]
    rates = stream.expected_rates("sp", fields)
    assert rates[("a", 1, 0)] == pytest.approx(2.0)
    assert rates[("b", 1, 0)] == pytest.approx(8.0)


def test_simulation_and_likelihood_share_the_same_rate_path():
    model = make_model()
    covariates = {("a", 1, 0): {"env": 0.0}, ("b", 1, 0): {"env": 0.0}}
    theta = {"sp": {"alpha": math.log(2.0), "beta": 0.0}}
    generated = simulate_presence_only(model, theta, covariates, seed=7)
    assert generated.expected_rates["inat"]["sp"][("b", 1, 0)] == pytest.approx(8.0)
    ll = model.log_likelihood(generated.counts, theta, covariates)
    assert math.isfinite(ll)


def test_zero_effort_cell_cannot_generate_records():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    process = LinearSuitability((), "alpha", {})
    stream = PresenceOnly(
        "inat",
        effort=EffortField({("a", 1, 0): 0.0}),
        informs=frozenset({"suitability"}),
    )
    model = Model(grid, {"sp": (process,)}, (stream,))
    generated = simulate_presence_only(
        model,
        {"sp": {"alpha": 10.0}},
        {("a", 1, 0): {}},
        seed=1,
    )
    assert generated.counts["inat"]["sp"][("a", 1, 0)] == 0
