"""Identification qualification for the fresh v0.5a directed-effect gate."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import diagnose_identification
from .v05a_directed import V05A_TARGET, V05A_WORLDS, build_v05a_fixture, v05a_theta


_STRUCTURAL_OPTIONS = {
    "method": "jax",
    "rtol": 1e-8,
    "atol": 1e-10,
}

_PRACTICAL_OPTIONS = {
    "rtol": 1e-8,
    "atol": 1e-10,
    "relative_singular_value_threshold": 1e-3,
    "condition_number_threshold": 1e3,
    "target_sd_threshold": 0.25,
    "fisher_ridge": 1e-10,
}


@dataclass(frozen=True, slots=True)
class V05AQualification:
    interaction_structural_pass: bool
    interaction_practical_pass: bool
    null_structural_pass: bool
    null_practical_pass: bool
    evidence: dict


def _training_model(fixture):
    grid = Grid(
        space=fixture.train_spaces,
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=fixture.model.streams,
    )
    covariates = {key: dict(fixture.covariates[key]) for key in grid.keys}
    model.check_design()
    return model, covariates


def evaluate_v05a_identification() -> V05AQualification:
    fixture = build_v05a_fixture()
    model, covariates = _training_model(fixture)
    evidence = {}
    for world in V05A_WORLDS:
        row = diagnose_identification(
            model,
            covariates,
            theta=v05a_theta(fixture, world),
            theta_obs=fixture.theta_obs,
            target=V05A_TARGET,
            practical=True,
            structural_kwargs=_STRUCTURAL_OPTIONS,
            practical_kwargs=_PRACTICAL_OPTIONS,
        )
        evidence[world] = row

    interaction = evidence["interaction"]
    null = evidence["measured_shared_null"]
    return V05AQualification(
        interaction_structural_pass=(
            interaction.structural.status is IdentificationStatus.IDENTIFIED
        ),
        interaction_practical_pass=(
            interaction.practical is not None and not interaction.practical.weak
        ),
        null_structural_pass=(
            null.structural.status is IdentificationStatus.IDENTIFIED
        ),
        null_practical_pass=(
            null.practical is not None and not null.practical.weak
        ),
        evidence=evidence,
    )
