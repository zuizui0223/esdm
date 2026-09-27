import importlib.util
import math
import sys

import pytest

from esdm.domain import Grid, StateSpace
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    PresenceOnly,
    StateAnnotatedCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability
from esdm.simulate import simulate_observations


NUMPYRO_AVAILABLE = (
    sys.version_info >= (3, 11)
    and importlib.util.find_spec("numpyro") is not None
)


def _fixture():
    grid = Grid(
        space=("s0", "s1", "s2", "s3"),
        doy=(1,),
        hour=(0,),
    )
    states = StateSpace(("resting", "foraging"))
    processes = (
        LinearSuitability(
            ("x",),
            "intercept",
            {"x": "beta_x"},
        ),
        LinearActivity(
            ("x",),
            "activity_intercept",
            {"x": "activity_beta_x"},
        ),
        LinearState(
            states,
            "resting",
            ("x",),
            {"foraging": "alpha_foraging"},
            {"foraging": {"x": "beta_foraging_x"}},
        ),
    )
    presence = PresenceOnly(
        "records",
        effort=EffortField({key: 8.0 for key in grid.keys}),
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    annotated = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({key: 6.0 for key in grid.keys}),
        detection=KnownDetection(0.9),
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": processes},
        (presence, annotated),
    )
    covariates = {
        key: {"x": value}
        for key, value in zip(
            grid.keys,
            (-1.5, -0.5, 0.5, 1.5),
            strict=True,
        )
    }
    theta = {
        "sp": {
            "intercept": 0.2,
            "beta_x": 0.3,
            "activity_intercept": 0.4,
            "activity_beta_x": 0.2,
            "alpha_foraging": 0.1,
            "beta_foraging_x": -0.3,
        }
    }
    generated = simulate_observations(
        model,
        theta,
        covariates,
        seed=31,
    )
    return model, covariates, generated.counts


@pytest.mark.skipif(
    not NUMPYRO_AVAILABLE,
    reason="NumPyro optional backend not installed",
)
def test_numpyro_uses_generic_annotated_blocks_and_exposes_posterior_fields():
    from esdm.model.backend_numpyro import fit_numpyro

    model, covariates, data = _fixture()
    fit = fit_numpyro(
        model,
        data,
        covariates,
        rng_seed=19,
        num_warmup=80,
        num_samples=100,
        num_chains=1,
        progress_bar=False,
        target_accept_prob=0.9,
    )

    assert "sp.activity.activity_intercept" in fit.samples
    assert "sp.state.alpha_foraging" in fit.samples
    assert "sp.state.alpha_resting" not in fit.samples

    from esdm.model.backend_numpyro import (
        posterior_latent_fields,
        posterior_observation_rates,
    )

    posterior = posterior_latent_fields(model, fit.samples, covariates)
    assert tuple(posterior.activity["sp"].shape) == (100, 4)
    assert tuple(posterior.state_probabilities["sp"].shape) == (100, 4, 2)
    assert posterior.state_labels["sp"] == ("resting", "foraging")
    assert float(posterior.state_probabilities["sp"][0, 0].sum()) == pytest.approx(
        1.0
    )

    rates = posterior_observation_rates(model, fit.samples, covariates)
    assert set(rates) == {
        "records.sp",
        "annotated.sp.resting",
        "annotated.sp.foraging",
    }
    assert len(rates["records.sp"]) == 100
