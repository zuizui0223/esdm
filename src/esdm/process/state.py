"""Reference-coded categorical ecological state process."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from esdm.domain import StateSpace
from .base import PriorSpec, ProcessContribution


_KNOCKOUT = "preserve_baseline_neutralize_environmental_slopes"


def _validate_state_definition(state_space, reference_state, intercept_parameters):
    if not isinstance(state_space, StateSpace):
        raise TypeError("state_space must be a StateSpace")
    reference = str(reference_state).strip()
    if reference not in state_space.states:
        raise ValueError("reference_state must belong to state_space")
    non_reference = tuple(
        state for state in state_space.states if state != reference
    )
    intercepts = {
        str(state).strip(): str(parameter).strip()
        for state, parameter in intercept_parameters.items()
    }
    if set(intercepts) != set(non_reference):
        raise ValueError(
            "intercept_parameters must match non-reference states exactly"
        )
    if any(not state or not parameter for state, parameter in intercepts.items()):
        raise ValueError("state/intercept parameter names must be non-empty")
    if len(set(intercepts.values())) != len(intercepts):
        raise ValueError("state intercept parameter names must be unique")
    return reference, non_reference, intercepts


@dataclass(frozen=True, slots=True)
class NeutralState:
    """State knockout preserving baseline composition while removing gradients."""

    state_space: StateSpace
    reference_state: str
    intercept_parameters: Mapping[str, str]
    name: str = "state"
    output_channel: str = "state"
    requires: frozenset[str] = frozenset()
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        reference, _non_reference, intercepts = _validate_state_definition(
            self.state_space,
            self.reference_state,
            self.intercept_parameters,
        )
        name = str(self.name).strip()
        if not name:
            raise ValueError("state process name must be non-empty")
        object.__setattr__(self, "reference_state", reference)
        object.__setattr__(
            self,
            "intercept_parameters",
            MappingProxyType(intercepts),
        )
        object.__setattr__(self, "name", name)

    def priors(self) -> dict[str, PriorSpec]:
        return {
            parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 2.0})
            for parameter in self.intercept_parameters.values()
        }

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        values = tuple(
            0.0
            if state == self.reference_state
            else theta[self.intercept_parameters[state]]
            for state in self.state_space.states
        )
        return ProcessContribution(
            self.output_channel,
            values,
            self.state_space.states,
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        columns = []
        for state in self.state_space.states:
            if state == self.reference_state:
                columns.append(array_module.zeros((len(keys),)))
            else:
                baseline = array_module.asarray(
                    theta[self.intercept_parameters[state]]
                )
                columns.append(
                    array_module.broadcast_to(baseline, (len(keys),))
                )
        return ProcessContribution(
            self.output_channel,
            array_module.stack(columns, axis=1),
            self.state_space.states,
        )

    def knockout(self) -> "NeutralState":
        return self


@dataclass(frozen=True, slots=True)
class LinearState:
    """Environmental model for conditional categorical state composition."""

    state_space: StateSpace
    reference_state: str
    covariates: tuple[str, ...]
    intercept_parameters: Mapping[str, str]
    coefficient_parameters: Mapping[str, Mapping[str, str]]
    name: str = "state"
    output_channel: str = "state"
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = _KNOCKOUT

    def __post_init__(self) -> None:
        reference, non_reference, intercepts = _validate_state_definition(
            self.state_space,
            self.reference_state,
            self.intercept_parameters,
        )
        covariates = tuple(str(value).strip() for value in self.covariates)
        if (
            len(set(covariates)) != len(covariates)
            or any(not value for value in covariates)
        ):
            raise ValueError("covariates must be unique non-empty names")

        coefficients: dict[str, Mapping[str, str]] = {}
        cleaned_outer = {
            str(state).strip(): values
            for state, values in self.coefficient_parameters.items()
        }
        if set(cleaned_outer) != set(non_reference):
            raise ValueError(
                "coefficient_parameters must match non-reference states exactly"
            )
        for state in non_reference:
            cleaned = {
                str(covariate).strip(): str(parameter).strip()
                for covariate, parameter in cleaned_outer[state].items()
            }
            if set(cleaned) != set(covariates):
                raise ValueError(
                    "state coefficient parameters must match covariates exactly"
                )
            if any(
                not covariate or not parameter
                for covariate, parameter in cleaned.items()
            ):
                raise ValueError(
                    "state coefficient parameter names must be non-empty"
                )
            coefficients[state] = MappingProxyType(cleaned)

        all_parameter_names = list(intercepts.values())
        for state in non_reference:
            all_parameter_names.extend(coefficients[state].values())
        if len(set(all_parameter_names)) != len(all_parameter_names):
            raise ValueError("state free parameter names must be unique")

        name = str(self.name).strip()
        if not name:
            raise ValueError("state process name must be non-empty")
        object.__setattr__(self, "reference_state", reference)
        object.__setattr__(self, "covariates", covariates)
        object.__setattr__(
            self,
            "intercept_parameters",
            MappingProxyType(intercepts),
        )
        object.__setattr__(
            self,
            "coefficient_parameters",
            MappingProxyType(coefficients),
        )
        object.__setattr__(self, "name", name)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(self.covariates)

    def priors(self) -> dict[str, PriorSpec]:
        priors = {
            parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 2.0})
            for parameter in self.intercept_parameters.values()
        }
        for state in self.state_space.states:
            if state == self.reference_state:
                continue
            for parameter in self.coefficient_parameters[state].values():
                priors[parameter] = PriorSpec(
                    "Normal", {"loc": 0.0, "scale": 1.0}
                )
        return priors

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        values = []
        for state in self.state_space.states:
            if state == self.reference_state:
                values.append(0.0)
                continue
            value = theta[self.intercept_parameters[state]]
            for covariate in self.covariates:
                value = (
                    value
                    + theta[self.coefficient_parameters[state][covariate]]
                    * covariates[covariate]
                )
            values.append(value)
        return ProcessContribution(
            self.output_channel,
            tuple(values),
            self.state_space.states,
        )

    def contribution_array(
        self,
        keys,
        theta,
        covariates,
        *,
        array_module,
        latent_fields=None,
    ):
        columns = []
        for state in self.state_space.states:
            if state == self.reference_state:
                columns.append(array_module.zeros((len(keys),)))
                continue
            value = array_module.broadcast_to(
                array_module.asarray(theta[self.intercept_parameters[state]]),
                (len(keys),),
            )
            for covariate in self.covariates:
                if covariate not in covariates:
                    raise KeyError(
                        f"missing state covariate array {covariate!r}"
                    )
                value = (
                    value
                    + theta[self.coefficient_parameters[state][covariate]]
                    * covariates[covariate]
                )
            columns.append(value)
        return ProcessContribution(
            self.output_channel,
            array_module.stack(columns, axis=1),
            self.state_space.states,
        )

    def knockout(self) -> NeutralState:
        return NeutralState(
            state_space=self.state_space,
            reference_state=self.reference_state,
            intercept_parameters=self.intercept_parameters,
            name=self.name,
        )
