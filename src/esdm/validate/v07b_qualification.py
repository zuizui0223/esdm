"""Pre-MCMC identification qualification for frozen v0.7b training split."""
from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v07b_fixture import V07B_RECOVERY_TRUTH, build_v07b_fixture, training_model


_STRUCTURAL = {
    "method": "jax",
    "rtol": 1e-8,
    "atol": 1e-10,
}

_PRACTICAL = {
    "rtol": 1e-8,
    "atol": 1e-10,
    "relative_singular_value_threshold": 1e-3,
    "condition_number_threshold": 1e3,
    "target_sd_threshold": 0.35,
    "fisher_ridge": 1e-10,
}


@dataclass(frozen=True, slots=True)
class V07BQualification:
    positive_structural_pass: bool
    positive_practical_pass: bool
    joint_only_refusal_pass: bool
    positive_evidence: dict
    refusal_evidence: dict


def evaluate_v07b_identification() -> V07BQualification:
    fixture = build_v07b_fixture()
    positive_model, positive_cov = training_model(fixture, knockout=False)

    positive = {}
    for target in V07B_RECOVERY_TRUTH:
        positive[target] = diagnose_identification(
            positive_model,
            positive_cov,
            theta=fixture.base.theta,
            theta_obs=fixture.base.theta_obs_positive,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    refusal_model = fixture.base.refusal_model
    refusal_grid_model, refusal_cov = training_model(fixture, knockout=False)
    # Rebuild the refusal design on the frozen eight training contexts while
    # preserving the exact joint-only process family from v0.7a.
    from esdm.domain import Grid
    from esdm.model import Model

    grid = Grid(
        space=refusal_model.domain.space,
        doy=tuple(range(1, 9)),
        hour=refusal_model.domain.hour,
    )
    refusal_training = Model(
        domain=grid,
        species=refusal_model.species,
        streams=refusal_model.streams,
    )
    refusal_cov = {
        key: dict(fixture.base.covariates[key])
        for key in grid.keys
    }
    refusal_training.check_design()

    refusal = {}
    for target in V07B_RECOVERY_TRUTH:
        refusal[target] = diagnose_identification(
            refusal_training,
            refusal_cov,
            theta=fixture.base.theta,
            theta_obs=fixture.base.theta_obs_refusal,
            target=target,
            practical=False,
            structural_kwargs=_STRUCTURAL,
        )

    return V07BQualification(
        positive_structural_pass=all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in positive.values()
        ),
        positive_practical_pass=all(
            row.practical is not None and not row.practical.weak
            for row in positive.values()
        ),
        joint_only_refusal_pass=all(
            row.structural.status is IdentificationStatus.NOT_IDENTIFIED
            for row in refusal.values()
        ),
        positive_evidence=positive,
        refusal_evidence=refusal,
    )
