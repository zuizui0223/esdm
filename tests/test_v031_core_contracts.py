import math

import pytest

from esdm.claims import ClaimStatus
from esdm.domain import Grid
from esdm.identify import contraction_diagnostic, identify_from_contraction
from esdm.model import MissingTargetDataError, Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability


def _grid():
    return Grid(space=("a", "b"), doy=(1,), hour=(0,))


def _suitability():
    return LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )


def _covariates(grid):
    return {key: {"x": (-1.0 if key[0] == "a" else 1.0)} for key in grid.keys}


def _effort(grid):
    return EffortField({key: 5.0 for key in grid.keys})


def test_contraction_identifies_parameter_but_never_supports_scientific_claim():
    diagnostic = contraction_diagnostic(
        prior_sd=2.0,
        posterior_samples=(0.9, 1.0, 1.1, 1.0),
    )
    result = identify_from_contraction(
        diagnostic,
        minimum_contraction=0.5,
        target="beta_x",
    )
    assert result.status.value == "Identified"
    assert result.status is not ClaimStatus.SUPPORTED


def test_stream_target_set_excludes_untargeted_species_from_likelihood():
    grid = _grid()
    stream = PresenceOnly(
        name="records",
        effort=_effort(grid),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp1"}),
    )
    model = Model(
        domain=grid,
        species={"sp1": (_suitability(),), "sp2": (_suitability(),)},
        streams=(stream,),
    )
    theta = {
        "sp1": {"intercept": 0.0, "beta_x": 0.0},
        "sp2": {"intercept": 8.0, "beta_x": 4.0},
    }
    data = {"records": {"sp1": {key: 1 for key in grid.keys}}}
    value = model.log_likelihood(data, theta, _covariates(grid))
    assert math.isfinite(value)


def test_missing_target_species_block_is_not_silently_treated_as_zero_counts():
    grid = _grid()
    stream = PresenceOnly(
        name="records",
        effort=_effort(grid),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp1", "sp2"}),
    )
    model = Model(
        domain=grid,
        species={"sp1": (_suitability(),), "sp2": (_suitability(),)},
        streams=(stream,),
    )
    theta = {
        "sp1": {"intercept": 0.0, "beta_x": 0.0},
        "sp2": {"intercept": 0.0, "beta_x": 0.0},
    }
    data = {"records": {"sp1": {key: 0 for key in grid.keys}}}
    with pytest.raises(MissingTargetDataError):
        model.log_likelihood(data, theta, _covariates(grid))


def test_suitability_knockout_preserves_baseline_intercept_and_neutralizes_slopes():
    grid = _grid()
    stream = PresenceOnly(
        name="records",
        effort=_effort(grid),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    full = Model(
        domain=grid,
        species={"sp": (_suitability(),)},
        streams=(stream,),
    )
    knockout = full.knockout("sp", "suitability")
    process = knockout.species["sp"][0]
    assert set(process.priors()) == {"intercept"}
    fields = knockout.latent_fields(
        {"sp": {"intercept": 2.0}},
        _covariates(grid),
    )
    assert all(value == pytest.approx(2.0) for value in fields.log_intensity["sp"].values())
