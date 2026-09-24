"""Composition of ecological processes and observation streams."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from collections.abc import Mapping
import math

from esdm.domain import Grid
from esdm.process.base import ProcessContribution
from .arrays import ContextArray, ContextStateArray, LatentFieldArrays


class DesignUninformedError(ValueError):
    """Raised when a declared process has no observation path."""


class CyclicProcessDependencyError(ValueError):
    """Raised when latent-species dependencies are cyclic."""


class MissingTargetDataError(ValueError):
    """Raised when a stream-target species has no data block.

    A missing species block is not interpreted as an observed all-zero record history.
    """


@dataclass(frozen=True, slots=True)
class DesignReport:
    informed_processes: tuple[tuple[str, str], ...]


def _freeze_context_fields(values):
    return MappingProxyType(
        {
            str(species): MappingProxyType(dict(context_values))
            for species, context_values in values.items()
        }
    )


def _freeze_state_fields(values):
    return MappingProxyType(
        {
            str(species): MappingProxyType(
                {
                    key: tuple(state_values)
                    for key, state_values in context_values.items()
                }
            )
            for species, context_values in values.items()
        }
    )


def _sigmoid(value) -> float:
    numeric = float(value)
    if numeric >= 0.0:
        z = math.exp(-numeric)
        return 1.0 / (1.0 + z)
    z = math.exp(numeric)
    return z / (1.0 + z)


def _softmax(values) -> tuple[float, ...]:
    numeric = tuple(float(value) for value in values)
    if not numeric:
        raise ValueError("state logits must contain at least one state")
    maximum = max(numeric)
    weights = tuple(math.exp(value - maximum) for value in numeric)
    total = math.fsum(weights)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("state softmax normalization must be finite and positive")
    return tuple(weight / total for weight in weights)


def _scalar_process_contribution(
    process, ctx, theta, covariates, *, latent_fields
):
    generic = getattr(process, "contribution", None)
    if generic is not None:
        contribution = generic(
            ctx, theta, covariates, latent_fields=latent_fields
        )
    elif (
        getattr(process, "output_channel", None) == "log_intensity"
        and hasattr(process, "log_intensity")
    ):
        contribution = ProcessContribution(
            "log_intensity",
            process.log_intensity(
                ctx, theta, covariates, latent_fields=latent_fields
            ),
        )
    else:
        raise TypeError(
            f"process {process.name!r} does not support scalar contribution evaluation"
        )
    if contribution.channel != process.output_channel:
        raise ValueError("process contribution channel does not match output_channel")
    return contribution


def _array_process_contribution(
    process, keys, theta, covariates, *, array_module, latent_fields
):
    generic = getattr(process, "contribution_array", None)
    if generic is not None:
        contribution = generic(
            keys,
            theta,
            covariates,
            array_module=array_module,
            latent_fields=latent_fields,
        )
    elif (
        getattr(process, "output_channel", None) == "log_intensity"
        and hasattr(process, "log_intensity_array")
    ):
        contribution = ProcessContribution(
            "log_intensity",
            process.log_intensity_array(
                keys,
                theta,
                covariates,
                array_module=array_module,
                latent_fields=latent_fields,
            ),
        )
    else:
        raise TypeError(
            f"process {process.name!r} does not support array contribution evaluation"
        )
    if contribution.channel != process.output_channel:
        raise ValueError("process contribution channel does not match output_channel")
    return contribution


@dataclass(frozen=True, slots=True)
class LatentFields:
    log_intensity: Mapping[str, Mapping[tuple[str, int, int], object]]
    activity_logit: Mapping[str, Mapping[tuple[str, int, int], object]] = field(
        default_factory=dict
    )
    activity: Mapping[str, Mapping[tuple[str, int, int], object]] = field(
        default_factory=dict
    )
    state_logits: Mapping[
        str, Mapping[tuple[str, int, int], tuple[object, ...]]
    ] = field(default_factory=dict)
    state_probabilities: Mapping[
        str, Mapping[tuple[str, int, int], tuple[object, ...]]
    ] = field(default_factory=dict)
    state_labels: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "log_intensity", _freeze_context_fields(self.log_intensity)
        )
        object.__setattr__(
            self, "activity_logit", _freeze_context_fields(self.activity_logit)
        )
        object.__setattr__(
            self, "activity", _freeze_context_fields(self.activity)
        )
        object.__setattr__(
            self, "state_logits", _freeze_state_fields(self.state_logits)
        )
        object.__setattr__(
            self,
            "state_probabilities",
            _freeze_state_fields(self.state_probabilities),
        )
        object.__setattr__(
            self,
            "state_labels",
            MappingProxyType(
                {
                    str(species): tuple(str(label) for label in labels)
                    for species, labels in self.state_labels.items()
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class Model:
    domain: Grid
    species: Mapping[str, tuple[object, ...]]
    streams: tuple[object, ...]

    def __post_init__(self) -> None:
        species = {
            str(name).strip(): tuple(processes)
            for name, processes in self.species.items()
        }
        if not species or any(not name for name in species):
            raise ValueError("species must contain non-empty names")
        for name, processes in species.items():
            if not processes:
                raise ValueError(f"species {name!r} must declare at least one process")
            process_names = [str(process.name) for process in processes]
            if len(set(process_names)) != len(process_names):
                raise ValueError(f"species {name!r} has duplicate process names")
            seen_parameters: set[str] = set()
            for process in processes:
                for parameter in getattr(process, "priors", lambda: {})():
                    parameter_name = str(parameter)
                    if parameter_name in seen_parameters:
                        raise ValueError(
                            f"species {name!r} has duplicate parameter name {parameter_name!r}"
                        )
                    seen_parameters.add(parameter_name)
        streams = tuple(self.streams)
        if not streams:
            raise ValueError("at least one observation stream is required")
        stream_names = [str(stream.name) for stream in streams]
        if len(set(stream_names)) != len(stream_names):
            raise ValueError("stream names must be unique")
        object.__setattr__(self, "species", MappingProxyType(species))
        object.__setattr__(self, "streams", streams)
        for stream in streams:
            declared = getattr(stream, "targets", None)
            if declared is None:
                raise ValueError(
                    f"stream {stream.name!r} must declare targets explicitly"
                )
            unknown = set(declared) - set(species)
            if unknown:
                raise ValueError(
                    f"stream {stream.name!r} targets unknown species: {sorted(unknown)}"
                )
        self._check_acyclic()

    def stream_targets(self, stream) -> tuple[str, ...]:
        """Resolve the explicitly declared species represented by one stream."""

        declared = getattr(stream, "targets", None)
        if declared is None:
            raise ValueError(
                f"stream {stream.name!r} must declare targets explicitly"
            )
        return tuple(species for species in self.species if species in declared)

    def _dependency_graph(self):
        graph: dict[str, set[str]] = {species: set() for species in self.species}
        indegree: dict[str, int] = {species: 0 for species in self.species}
        for target, processes in self.species.items():
            sources = set()
            for process in processes:
                for source in getattr(
                    process, "latent_species_dependencies", frozenset()
                ):
                    if source not in graph:
                        raise ValueError(
                            f"unknown latent species dependency {source!r}"
                        )
                    sources.add(source)
            for source in sources:
                if target not in graph[source]:
                    graph[source].add(target)
                    indegree[target] += 1
        return graph, indegree

    def _species_topological_order(self) -> tuple[str, ...]:
        graph, indegree = self._dependency_graph()
        declared = tuple(self.species)
        ready = [species for species in declared if indegree[species] == 0]
        ordered: list[str] = []

        while ready:
            node = ready.pop(0)
            ordered.append(node)
            for child in declared:
                if child not in graph[node]:
                    continue
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)

        if len(ordered) != len(declared):
            raise CyclicProcessDependencyError(
                "cyclic latent-species dependency"
            )
        return tuple(ordered)

    def _check_acyclic(self) -> None:
        self._species_topological_order()

    def check_design(self) -> DesignReport:
        for stream in self.streams:
            required = frozenset(
                getattr(stream, "required_latent_channels", frozenset())
            )
            if not required:
                continue
            for species in self.stream_targets(stream):
                processes = self.species[species]
                available = frozenset(
                    str(process.output_channel) for process in processes
                )
                missing = required - available
                if missing:
                    raise DesignUninformedError(
                        f"stream {stream.name!r} target {species!r} lacks required "
                        f"latent channel(s): {sorted(missing)}"
                    )
                state_space = getattr(stream, "state_space", None)
                if state_space is not None and "state" in required:
                    state_processes = tuple(
                        process
                        for process in processes
                        if getattr(process, "output_channel", None) == "state"
                    )
                    for process in state_processes:
                        process_state_space = getattr(process, "state_space", None)
                        if (
                            process_state_space is not None
                            and process_state_space.states != state_space.states
                        ):
                            raise DesignUninformedError(
                                f"stream {stream.name!r} target {species!r} has "
                                "incompatible state labels"
                            )

        informed: list[tuple[str, str]] = []
        for species, processes in self.species.items():
            for process in processes:
                has_path = any(
                    species in self.stream_targets(stream)
                    and process.name in getattr(stream, "informs", frozenset())
                    and process.output_channel in getattr(stream, "consumes", frozenset())
                    for stream in self.streams
                )
                if not has_path:
                    raise DesignUninformedError(
                        f"process {species}:{process.name} has no process->channel->targeted-stream path"
                    )
                informed.append((species, process.name))
        return DesignReport(tuple(informed))

    def latent_fields(
        self,
        theta: Mapping[str, Mapping[str, object]],
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]],
    ) -> LatentFields:
        """Construct mapping-based latent ecological fields for scalar workflows."""

        missing_contexts = set(self.domain.keys) - set(covariates)
        if missing_contexts:
            raise ValueError("covariates are missing domain contexts")

        log_fields = {}
        activity_logits = {}
        activities = {}
        state_logits = {}
        state_probabilities = {}
        state_labels = {}

        for species in self._species_topological_order():
            processes = self.species[species]
            if species not in theta:
                raise KeyError(f"missing parameter block for species {species!r}")
            log_block = {}
            activity_logit_block = {}
            activity_block = {}
            state_logit_block = {}
            state_probability_block = {}
            species_state_labels = None
            available_fields = LatentFields(
                log_intensity=log_fields,
                activity_logit=activity_logits,
                activity=activities,
                state_logits=state_logits,
                state_probabilities=state_probabilities,
                state_labels=state_labels,
            )

            for ctx in self.domain.contexts():
                context_covariates = covariates[ctx.key]
                log_total = 0.0
                activity_total = 0.0
                has_activity = False
                state_total = None
                context_state_labels = None

                for process in processes:
                    contribution = _scalar_process_contribution(
                        process,
                        ctx,
                        theta[species],
                        context_covariates,
                        latent_fields=available_fields,
                    )
                    if contribution.channel == "log_intensity":
                        if contribution.labels:
                            raise ValueError(
                                "log-intensity contributions cannot declare labels"
                            )
                        log_total = log_total + contribution.values
                    elif contribution.channel == "activity":
                        if contribution.labels:
                            raise ValueError(
                                "activity contributions cannot declare labels"
                            )
                        activity_total = activity_total + contribution.values
                        has_activity = True
                    elif contribution.channel == "state":
                        labels = tuple(contribution.labels)
                        values = tuple(contribution.values)
                        if not labels or len(labels) != len(values):
                            raise ValueError(
                                "state contribution labels must match state values"
                            )
                        if context_state_labels is None:
                            context_state_labels = labels
                            state_total = [0.0 for _ in labels]
                        elif labels != context_state_labels:
                            raise ValueError(
                                "state contribution labels must agree within species"
                            )
                        for index, value in enumerate(values):
                            state_total[index] = state_total[index] + value
                    else:
                        raise ValueError(
                            f"unsupported latent output channel {contribution.channel!r}"
                        )

                log_block[ctx.key] = log_total
                if has_activity:
                    activity_logit_block[ctx.key] = activity_total
                    activity_block[ctx.key] = _sigmoid(activity_total)
                else:
                    activity_block[ctx.key] = 1.0

                if state_total is not None:
                    labels = context_state_labels
                    if species_state_labels is None:
                        species_state_labels = labels
                    elif labels != species_state_labels:
                        raise ValueError(
                            "state contribution labels must agree within species"
                        )
                    logits = tuple(state_total)
                    state_logit_block[ctx.key] = logits
                    state_probability_block[ctx.key] = _softmax(logits)

            log_fields[species] = log_block
            activities[species] = activity_block
            if activity_logit_block:
                activity_logits[species] = activity_logit_block
            if species_state_labels is not None:
                state_labels[species] = species_state_labels
                state_logits[species] = state_logit_block
                state_probabilities[species] = state_probability_block

        return LatentFields(
            log_intensity=log_fields,
            activity_logit=activity_logits,
            activity=activities,
            state_logits=state_logits,
            state_probabilities=state_probabilities,
            state_labels=state_labels,
        )

    def latent_field_arrays(
        self,
        theta: Mapping[str, Mapping[str, object]],
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]],
        *,
        array_module,
    ) -> LatentFieldArrays:
        """Construct latent channels with all contexts on one array axis."""

        keys = tuple(self.domain.keys)
        missing_contexts = set(keys) - set(covariates)
        if missing_contexts:
            raise ValueError("covariates are missing domain contexts")

        required_covariates: set[str] = set()
        for processes in self.species.values():
            for process in processes:
                required_covariates.update(
                    getattr(process, "requires", frozenset())
                )
        covariate_arrays = {}
        for name in sorted(required_covariates):
            missing = [key for key in keys if name not in covariates[key]]
            if missing:
                raise KeyError(
                    f"missing ecological covariate {name!r} for {missing[0]!r}"
                )
            covariate_arrays[name] = array_module.asarray(
                [covariates[key][name] for key in keys]
            )

        log_fields = {}
        activity_logits = {}
        activities = {}
        state_logits = {}
        state_probabilities = {}

        for species in self._species_topological_order():
            processes = self.species[species]
            if species not in theta:
                raise KeyError(f"missing parameter block for species {species!r}")
            log_total = array_module.zeros((len(keys),))
            activity_total = array_module.zeros((len(keys),))
            has_activity = False
            state_total = None
            state_labels = None
            available_fields = LatentFieldArrays(
                log_intensity=log_fields,
                activity_logit=activity_logits,
                activity=activities,
                state_logits=state_logits,
                state_probabilities=state_probabilities,
            )

            for process in processes:
                contribution = _array_process_contribution(
                    process,
                    keys,
                    theta[species],
                    covariate_arrays,
                    array_module=array_module,
                    latent_fields=available_fields,
                )
                if contribution.channel == "log_intensity":
                    if contribution.labels:
                        raise ValueError(
                            "log-intensity contributions cannot declare labels"
                        )
                    log_total = log_total + ContextArray(
                        keys, contribution.values
                    ).values
                elif contribution.channel == "activity":
                    if contribution.labels:
                        raise ValueError(
                            "activity contributions cannot declare labels"
                        )
                    activity_total = activity_total + ContextArray(
                        keys, contribution.values
                    ).values
                    has_activity = True
                elif contribution.channel == "state":
                    labels = tuple(contribution.labels)
                    if not labels:
                        raise ValueError(
                            "state contributions require ordered labels"
                        )
                    values = ContextStateArray(
                        keys, labels, contribution.values
                    ).values
                    if state_labels is None:
                        state_labels = labels
                        state_total = array_module.zeros(
                            (len(keys), len(labels))
                        )
                    elif labels != state_labels:
                        raise ValueError(
                            "state contribution labels must agree within species"
                        )
                    state_total = state_total + values
                else:
                    raise ValueError(
                        f"unsupported latent output channel {contribution.channel!r}"
                    )

            log_fields[species] = ContextArray(keys, log_total)
            if has_activity:
                activity_logits[species] = ContextArray(keys, activity_total)
                activity_values = 1.0 / (
                    1.0 + array_module.exp(-activity_total)
                )
            else:
                activity_values = array_module.ones((len(keys),))
            activities[species] = ContextArray(keys, activity_values)

            if state_total is not None:
                shifted = state_total - array_module.max(
                    state_total, axis=1, keepdims=True
                )
                weights = array_module.exp(shifted)
                probabilities = weights / array_module.sum(
                    weights, axis=1, keepdims=True
                )
                state_logits[species] = ContextStateArray(
                    keys, state_labels, state_total
                )
                state_probabilities[species] = ContextStateArray(
                    keys, state_labels, probabilities
                )

        return LatentFieldArrays(
            log_intensity=log_fields,
            activity_logit=activity_logits,
            activity=activities,
            state_logits=state_logits,
            state_probabilities=state_probabilities,
        )

    def knockout(self, species: str, process_name: str) -> "Model":
        if species not in self.species:
            raise KeyError(species)
        found = False
        new_species: dict[str, tuple[object, ...]] = {}
        for name, processes in self.species.items():
            if name != species:
                new_species[name] = processes
                continue
            replaced = []
            for process in processes:
                if process.name == process_name:
                    replaced.append(process.knockout())
                    found = True
                else:
                    replaced.append(process)
            new_species[name] = tuple(replaced)
        if not found:
            raise KeyError(f"unknown process {species}:{process_name}")
        return Model(self.domain, new_species, self.streams)

    def log_likelihood(
        self,
        data: Mapping[str, Mapping[str, Mapping[tuple[str, int, int], int]]],
        theta: Mapping[str, Mapping[str, object]],
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]],
        *,
        theta_obs: Mapping[str, Mapping[str, object]] | None = None,
    ) -> float:
        fields = self.latent_fields(theta, covariates)
        total = 0.0
        observation_parameters = {} if theta_obs is None else theta_obs
        known_streams = {stream.name for stream in self.streams}
        unknown_streams = set(data) - known_streams
        if unknown_streams:
            raise ValueError(f"data contain unknown streams: {sorted(unknown_streams)}")
        unknown_parameter_streams = set(observation_parameters) - known_streams
        if unknown_parameter_streams:
            raise ValueError(
                f"observation parameters contain unknown streams: {sorted(unknown_parameter_streams)}"
            )
        for stream in self.streams:
            if stream.name not in data:
                raise MissingTargetDataError(
                    f"missing data block for stream {stream.name!r}"
                )
            stream_data = data[stream.name]
            targets = set(self.stream_targets(stream))
            unexpected_species = set(stream_data) - targets
            if unexpected_species:
                raise ValueError(
                    f"data for stream {stream.name!r} contain non-target species: "
                    f"{sorted(unexpected_species)}"
                )
            missing_species = targets - set(stream_data)
            if missing_species:
                raise MissingTargetDataError(
                    f"stream {stream.name!r} is missing target species blocks: "
                    f"{sorted(missing_species)}"
                )
            stream_theta = dict(observation_parameters.get(stream.name, {}))
            required_parameters = set(getattr(stream, "priors", lambda: {})())
            missing_parameters = required_parameters - set(stream_theta)
            if missing_parameters:
                raise KeyError(
                    f"stream {stream.name!r} missing observation parameters: "
                    f"{sorted(missing_parameters)}"
                )
            unexpected_parameters = set(stream_theta) - required_parameters
            if unexpected_parameters:
                raise KeyError(
                    f"stream {stream.name!r} received undeclared observation parameters: "
                    f"{sorted(unexpected_parameters)}"
                )
            for species in self.stream_targets(stream):
                total += float(
                    stream.log_lik(
                        species,
                        fields,
                        stream_data[species],
                        theta_obs=stream_theta,
                        covariates=covariates,
                    )
                )
        return total
