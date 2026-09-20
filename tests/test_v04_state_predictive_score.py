import math

import pytest

from esdm.domain import Grid, StateSpace
from esdm.model import Model
from esdm.observe import EffortField, KnownDetection, StateAnnotatedCount
from esdm.process import LinearActivity, LinearState, LinearSuitability


def _fixture():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability((), "intercept", {}),
                LinearActivity((), "activity_intercept", {}),
                LinearState(
                    states,
                    "resting",
                    (),
                    {"foraging": "alpha_foraging"},
                    {"foraging": {}},
                ),
            )
        },
        (
            StateAnnotatedCount(
                "annotated",
                state_space=states,
                effort=EffortField({key: 1.0 for key in grid.keys}),
                detection=KnownDetection(probability=1.0),
                informs=frozenset({"suitability", "activity", "state"}),
                targets=frozenset({"sp"}),
            ),
        ),
    )
    return model


def _logmeanexp(values):
    values = tuple(values)
    maximum = max(values)
    return maximum + math.log(
        sum(math.exp(value - maximum) for value in values) / len(values)
    )


def _poisson_log_mass(count, rate):
    if rate == 0.0:
        return 0.0 if count == 0 else -math.inf
    return count * math.log(rate) - rate - math.lgamma(count + 1.0)


def test_state_block_log_predictive_density_averages_all_state_contexts(monkeypatch):
    from esdm.model import backend_numpyro
    from esdm.validate.evidence import poisson_block_log_predictive_density

    model = _fixture()
    keys = model.domain.keys
    fake_rates = {
        "annotated.sp.resting": (
            (1.0, 2.0),
            (2.0, 4.0),
        ),
        "annotated.sp.foraging": (
            (0.5, 1.5),
            (1.0, 3.0),
        ),
    }
    monkeypatch.setattr(
        backend_numpyro,
        "posterior_observation_rates",
        lambda model, samples, covariates: fake_rates,
    )
    data = {
        "annotated": {
            "sp": {
                "resting": {keys[0]: 0, keys[1]: 2},
                "foraging": {keys[0]: 1, keys[1]: 0},
            }
        }
    }

    observed = poisson_block_log_predictive_density(
        model,
        samples={},
        covariates={key: {} for key in keys},
        data=data,
        block_names=(
            "annotated.sp.resting",
            "annotated.sp.foraging",
        ),
    )

    expected_rows = [
        _logmeanexp((_poisson_log_mass(0, 1.0), _poisson_log_mass(0, 2.0))),
        _logmeanexp((_poisson_log_mass(2, 2.0), _poisson_log_mass(2, 4.0))),
        _logmeanexp((_poisson_log_mass(1, 0.5), _poisson_log_mass(1, 1.0))),
        _logmeanexp((_poisson_log_mass(0, 1.5), _poisson_log_mass(0, 3.0))),
    ]
    assert observed == pytest.approx(sum(expected_rows) / 4.0)


def test_state_block_score_rejects_unknown_or_duplicate_blocks(monkeypatch):
    from esdm.model import backend_numpyro
    from esdm.validate.evidence import poisson_block_log_predictive_density

    model = _fixture()
    keys = model.domain.keys
    monkeypatch.setattr(
        backend_numpyro,
        "posterior_observation_rates",
        lambda model, samples, covariates: {
            "annotated.sp.resting": ((1.0, 1.0),),
            "annotated.sp.foraging": ((1.0, 1.0),),
        },
    )
    data = {
        "annotated": {
            "sp": {
                "resting": {key: 0 for key in keys},
                "foraging": {key: 0 for key in keys},
            }
        }
    }

    with pytest.raises(KeyError, match="unknown posterior observation block"):
        poisson_block_log_predictive_density(
            model,
            samples={},
            covariates={key: {} for key in keys},
            data=data,
            block_names=("missing.block",),
        )

    with pytest.raises(ValueError, match="unique"):
        poisson_block_log_predictive_density(
            model,
            samples={},
            covariates={key: {} for key in keys},
            data=data,
            block_names=("annotated.sp.resting", "annotated.sp.resting"),
        )
