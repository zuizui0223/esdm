import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import CategoricalActivityProcess, LinearSuitability


def _model(activity_process):
    grid = Grid(space=("site",), doy=(100,), hour=(0, 6, 12, 18))
    suitability = LinearSuitability(
        covariates=(),
        intercept_parameter="intercept",
        coefficient_parameters={},
    )
    stream = PresenceOnly(
        name="opportunistic",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability", "activity"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=grid,
        species={"sp": (suitability, activity_process)},
        streams=(stream,),
    )
    return model, {key: {} for key in grid.keys}


def test_activity_probabilities_are_latent_outputs_and_modulate_log_intensity():
    activity = CategoricalActivityProcess(
        hours=(0, 6, 12, 18),
        reference_hour=0,
        covariates=(),
        intercept_parameters={6: "act_6", 12: "act_12", 18: "act_18"},
        coefficient_parameters={6: {}, 12: {}, 18: {}},
    )
    model, covariates = _model(activity)
    theta = {
        "sp": {
            "intercept": 0.0,
            "act_6": 0.0,
            "act_12": math.log(4.0),
            "act_18": 0.0,
        }
    }
    fields = model.latent_fields(theta, covariates)

    by_context = fields.activity_probability["sp"]["activity"]
    assert math.isclose(sum(by_context[key] for key in model.domain.keys), 1.0, abs_tol=1e-12)
    assert by_context[("site", 100, 12)] > by_context[("site", 100, 0)]
    assert fields.log_intensity["sp"][("site", 100, 12)] > fields.log_intensity["sp"][("site", 100, 0)]


def test_activity_knockout_is_uniform_and_removes_hour_effect_without_changing_baseline():
    activity = CategoricalActivityProcess(
        hours=(0, 6, 12, 18),
        reference_hour=0,
        covariates=(),
        intercept_parameters={6: "act_6", 12: "act_12", 18: "act_18"},
        coefficient_parameters={6: {}, 12: {}, 18: {}},
    )
    model, covariates = _model(activity)
    neutral = model.knockout("sp", "activity")
    theta = {"sp": {"intercept": 1.3}}
    fields = neutral.latent_fields(theta, covariates)

    assert all(
        math.isclose(value, 1.3, abs_tol=1e-12)
        for value in fields.log_intensity["sp"].values()
    )
    assert all(
        math.isclose(value, 0.25, abs_tol=1e-12)
        for value in fields.activity_probability["sp"]["activity"].values()
    )
