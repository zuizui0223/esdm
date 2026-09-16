import math
import pytest

from esdm.domain import Grid
from esdm.model import DesignUninformedError, Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability


def build_model(*, informs=frozenset({"suitability"})):
    grid = Grid(space=("s1", "s2"), doy=(1,), hour=(0,))
    process = LinearSuitability(
        covariates=("temp",),
        intercept_parameter="alpha",
        coefficient_parameters={"temp": "beta_temp"},
    )
    effort = EffortField({("s1", 1, 0): 1.0, ("s2", 1, 0): 2.0})
    stream = PresenceOnly("records", effort=effort, informs=informs)
    return Model(
        domain=grid,
        species={"sp": (process,)},
        streams=(stream,),
    )


def test_model_design_requires_declared_and_computational_path():
    model = build_model()
    report = model.check_design()
    assert report.informed_processes == (("sp", "suitability"),)

    with pytest.raises(DesignUninformedError):
        build_model(informs=frozenset()).check_design()


def test_same_process_code_builds_latent_field_and_knockout():
    model = build_model()
    covariates = {
        ("s1", 1, 0): {"temp": 0.0},
        ("s2", 1, 0): {"temp": 1.0},
    }
    theta = {"sp": {"alpha": math.log(2.0), "beta_temp": math.log(3.0)}}
    fields = model.latent_fields(theta, covariates)
    assert fields.log_intensity["sp"][("s1", 1, 0)] == pytest.approx(math.log(2.0))
    assert fields.log_intensity["sp"][("s2", 1, 0)] == pytest.approx(math.log(6.0))

    knocked = model.knockout("sp", "suitability")
    knocked_fields = knocked.latent_fields(theta, covariates)
    assert set(knocked_fields.log_intensity["sp"].values()) == {0.0}


def test_process_knockout_is_explicit_no_effect_semantics():
    process = LinearSuitability(
        covariates=("temp",),
        intercept_parameter="alpha",
        coefficient_parameters={"temp": "beta_temp"},
    )
    knockout = process.knockout()
    assert knockout.knockout_semantics == "no_effect_log_contribution_zero"
