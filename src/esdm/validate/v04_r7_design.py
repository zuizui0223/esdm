"""Budget-matched direct versus passive state calibration for v0.4-R7."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.model import Model
from esdm.observe import EffortField, KnownDetection, StateAnnotatedCount
from .v04_r4a_design import build_v04_r4a_fixture
from .v04_r5a_design import build_v04_r5a_fixture


R7_EXPECTED_LABEL_BUDGET = 432.0


@dataclass(frozen=True, slots=True)
class V04R7PassiveFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    annotated_spaces: tuple[str, ...]
    annotated_times: tuple[tuple[int, int], ...]
    generating_theta: Mapping[str, Mapping[str, float]]
    generating_theta_obs: Mapping[str, Mapping[str, float]]
    passive_effort: float
    expected_passive_labels: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.generating_theta.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.generating_theta_obs.items()
            }),
        )


def _training_annotation_keys(r4):
    return tuple(
        (space, doy, hour)
        for space in r4.annotated_spaces
        for doy, hour in r4.annotated_times
    )


def _passive_effort_for_budget(r4) -> float:
    keys = _training_annotation_keys(r4)
    fields = r4.model.latent_fields(
        r4.generating_theta,
        r4.covariates,
    )
    total_per_unit_effort = math.fsum(
        math.exp(float(fields.log_intensity["sp"][key]))
        * float(fields.activity["sp"][key])
        * 0.85
        for key in keys
    )
    if not math.isfinite(total_per_unit_effort) or total_per_unit_effort <= 0.0:
        raise ValueError("R7 passive budget denominator must be finite and positive")
    return R7_EXPECTED_LABEL_BUDGET / total_per_unit_effort


def build_v04_r7_direct_fixture(source_csv_text: str):
    """The promoted direct-composition design used as the R7 direct arm."""

    return build_v04_r5a_fixture(source_csv_text)


def build_v04_r7_passive_fixture(source_csv_text: str) -> V04R7PassiveFixture:
    """Add equal-expected-label passive state annotations to the R4 geometry."""

    r4 = build_v04_r4a_fixture(source_csv_text)
    keys = _training_annotation_keys(r4)
    effort_value = _passive_effort_for_budget(r4)

    passive = StateAnnotatedCount(
        name="passive_calibration",
        state_space=r4.model.streams[2].state_space,
        effort=EffortField({key: effort_value for key in keys}),
        detection=KnownDetection(probability=0.85),
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=r4.model.domain,
        species=r4.model.species,
        streams=(*r4.model.streams, passive),
    )
    model.check_design()

    theta_obs = {
        name: dict(values)
        for name, values in r4.generating_theta_obs.items()
    }
    theta_obs["passive_calibration"] = {}

    fields = model.latent_fields(r4.generating_theta, r4.covariates)
    blocks = passive.observation_blocks(
        "sp",
        fields,
        theta_obs={},
        covariates=r4.covariates,
    )
    expected = math.fsum(
        float(rate)
        for block in blocks
        for key, rate in zip(block.keys, block.rates, strict=True)
        if key in set(keys)
    )

    return V04R7PassiveFixture(
        model=model,
        covariates=r4.covariates,
        train_spaces=r4.train_spaces,
        heldout_spaces=r4.heldout_spaces,
        annotated_spaces=r4.annotated_spaces,
        annotated_times=r4.annotated_times,
        generating_theta=r4.generating_theta,
        generating_theta_obs=theta_obs,
        passive_effort=effort_value,
        expected_passive_labels=expected,
    )


def expected_direct_labels(source_csv_text: str) -> float:
    fixture = build_v04_r7_direct_fixture(source_csv_text)
    stream = {stream.name: stream for stream in fixture.model.streams}["state_calibration"]
    keys = {
        (space, doy, hour)
        for space in fixture.annotated_spaces
        for doy, hour in fixture.annotated_times
    }
    fields = fixture.model.latent_fields(
        fixture.generating_theta,
        fixture.covariates,
    )
    blocks = stream.observation_blocks(
        "sp",
        fields,
        theta_obs={},
        covariates=fixture.covariates,
    )
    return math.fsum(
        float(rate)
        for block in blocks
        for key, rate in zip(block.keys, block.rates, strict=True)
        if key in keys
    )
