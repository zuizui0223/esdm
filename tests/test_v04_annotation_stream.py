import math

from esdm.domain import Grid, Partition, StateSpace
from esdm.model import Model
from esdm.observe import Annotation
from esdm.process import CategoricalStateProcess
from esdm.simulate import simulate_annotations


def _state_model():
    state_space = StateSpace(("juvenile", "adult", "reproductive"))
    process = CategoricalStateProcess(
        state_space=state_space,
        reference_state="juvenile",
        covariates=(),
        intercept_parameters={"adult": "state_adult", "reproductive": "state_reproductive"},
        coefficient_parameters={"adult": {}, "reproductive": {}},
    )
    coarse = Partition(
        "maturity",
        {
            "immature": ("juvenile",),
            "mature": ("adult", "reproductive"),
        },
    )
    stream = Annotation(
        name="field_state",
        partition=coarse,
        state_process="state",
        informs=frozenset({"state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=Grid(space=("a", "b", "c"), doy=(120,), hour=(12,)),
        species={"sp": (process,)},
        streams=(stream,),
    )
    covariates = {key: {} for key in model.domain.keys}
    return model, stream, covariates


def test_annotation_aggregates_fine_state_probability_to_declared_partition():
    model, stream, covariates = _state_model()
    theta = {"sp": {"state_adult": math.log(2.0), "state_reproductive": math.log(3.0)}}
    fields = model.latent_fields(theta, covariates)

    probabilities = stream.expected_probabilities("sp", fields, ("a", 120, 12))
    # Fine weights are 1:2:3, so mature = (2+3)/6.
    assert math.isclose(probabilities["immature"], 1 / 6, abs_tol=1e-12)
    assert math.isclose(probabilities["mature"], 5 / 6, abs_tol=1e-12)

    log_lik = model.log_likelihood(
        {"field_state": {"sp": {("a", 120, 12): "mature"}}},
        theta,
        covariates,
    )
    assert math.isclose(log_lik, math.log(5 / 6), abs_tol=1e-12)


def test_annotation_simulation_uses_the_same_latent_state_field():
    model, _stream, covariates = _state_model()
    theta = {"sp": {"state_adult": 1.0, "state_reproductive": -0.5}}
    generated = simulate_annotations(model, theta, covariates, seed=23)

    assert set(generated.labels) == {"field_state"}
    assert set(generated.labels["field_state"]["sp"]) == set(model.domain.keys)
    assert set(generated.expected_probabilities["field_state"]["sp"][("a", 120, 12)]) == {
        "immature",
        "mature",
    }
