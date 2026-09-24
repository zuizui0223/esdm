"""Frozen train/held-out geometry for v0.7b dynamic recovery/transfer."""
from __future__ import annotations

from dataclasses import dataclass

from esdm.domain import Grid
from esdm.model import Model
from .v07a_fixture import V07A_TRUTH, V07AFixture, build_v07a_fixture


V07B_RECOVERY_TRUTH = dict(V07A_TRUTH)
V07B_TRAIN_DOY = tuple(range(1, 9))
V07B_HELDOUT_DOY = tuple(range(9, 13))


@dataclass(frozen=True, slots=True)
class V07BFixture:
    base: V07AFixture
    train_keys: tuple
    heldout_keys: tuple


def build_v07b_fixture() -> V07BFixture:
    base = build_v07a_fixture()
    train_keys = tuple(
        key for key in base.positive_model.domain.keys
        if int(key[1]) in V07B_TRAIN_DOY
    )
    heldout_keys = tuple(
        key for key in base.positive_model.domain.keys
        if int(key[1]) in V07B_HELDOUT_DOY
    )
    if len(train_keys) != 8 or len(heldout_keys) != 4:
        raise AssertionError("v0.7b frozen split must be 8 training + 4 held-out contexts")
    return V07BFixture(base=base, train_keys=train_keys, heldout_keys=heldout_keys)


def training_model(fixture: V07BFixture, *, knockout: bool) -> tuple[Model, dict]:
    grid = Grid(
        space=fixture.base.positive_model.domain.space,
        doy=V07B_TRAIN_DOY,
        hour=fixture.base.positive_model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.base.positive_model.species,
        streams=fixture.base.positive_model.streams,
    )
    if knockout:
        model = model.knockout("sp", "occupancy")
    covariates = {
        key: dict(fixture.base.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def full_trajectory_model(
    fixture: V07BFixture,
    *,
    knockout: bool,
) -> tuple[Model, dict]:
    model = fixture.base.positive_model
    if knockout:
        model = model.knockout("sp", "occupancy")
    model.check_design()
    return model, dict(fixture.base.covariates)
