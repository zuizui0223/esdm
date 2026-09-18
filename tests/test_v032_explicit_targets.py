import pytest

from esdm.domain import Grid
from esdm.model import MissingTargetDataError, Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability


def _process():
    return LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )


def test_presence_only_rejects_missing_target_declaration():
    with pytest.raises(ValueError, match="targets must be declared explicitly"):
        PresenceOnly(
            name="opportunistic",
            effort=EffortField({("a", 1, 0): 1.0}),
            informs=frozenset({"suitability"}),
            targets=None,
        )


def test_explicit_target_does_not_turn_an_omitted_species_into_zero_history():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    stream = PresenceOnly(
        name="opportunistic",
        effort=EffortField({grid.keys[0]: 1.0}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp_a"}),
    )
    model = Model(
        grid,
        {"sp_a": (_process(),), "sp_b": (_process(),)},
        (stream,),
    )
    covariates = {grid.keys[0]: {"x": 0.0}}
    theta = {
        "sp_a": {"intercept": 0.0, "beta_x": 0.0},
        "sp_b": {"intercept": 0.0, "beta_x": 0.0},
    }

    with pytest.raises(MissingTargetDataError, match="missing target species blocks"):
        model.log_likelihood(
            {"opportunistic": {}},
            theta,
            covariates,
        )
