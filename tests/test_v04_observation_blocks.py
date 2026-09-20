import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PoissonObservationBlock, PresenceOnly
from esdm.process import LinearSuitability


def _fixture():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 2.0, grid.keys[1]: 4.0}),
        detection_probability=0.5,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": (LinearSuitability((), "intercept", {}),)},
        (stream,),
    )
    theta = {"sp": {"intercept": 0.0}}
    covariates = {key: {} for key in grid.keys}
    return grid, stream, model, theta, covariates


def test_presence_only_block_matches_existing_expected_rates():
    grid, stream, model, theta, covariates = _fixture()
    fields = model.latent_fields(theta, covariates)

    block, = stream.observation_blocks(
        "sp",
        fields,
        data={grid.keys[0]: 1, grid.keys[1]: 2},
        covariates=covariates,
    )

    assert isinstance(block, PoissonObservationBlock)
    assert block.name == "records.sp"
    assert block.keys == grid.keys
    assert tuple(block.rates) == pytest.approx((1.0, 2.0))
    assert tuple(block.observed) == (1, 2)
    assert block.structural_exposure_mask == (True, True)


def test_poisson_observation_block_validates_lengths():
    keys = (("a", 1, 0), ("b", 1, 0))

    with pytest.raises(ValueError, match="rates"):
        PoissonObservationBlock(
            name="x",
            keys=keys,
            rates=(1.0,),
            observed=(0, 0),
            structural_exposure_mask=(True, True),
        )

    with pytest.raises(ValueError, match="observed"):
        PoissonObservationBlock(
            name="x",
            keys=keys,
            rates=(1.0, 2.0),
            observed=(0,),
            structural_exposure_mask=(True, True),
        )

    with pytest.raises(ValueError, match="exposure"):
        PoissonObservationBlock(
            name="x",
            keys=keys,
            rates=(1.0, 2.0),
            observed=(0, 0),
            structural_exposure_mask=(True,),
        )


def test_presence_only_block_keeps_static_zero_exposure():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 0.0, grid.keys[1]: 2.0}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": (LinearSuitability((), "intercept", {}),)},
        (stream,),
    )
    fields = model.latent_fields(
        {"sp": {"intercept": 0.0}},
        {key: {} for key in grid.keys},
    )

    block, = stream.observation_blocks(
        "sp",
        fields,
        covariates={key: {} for key in grid.keys},
    )

    assert tuple(block.rates) == pytest.approx((0.0, 2.0))
    assert block.structural_exposure_mask == (False, True)
