"""Composition of ecological processes and observation streams."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from esdm.domain import Grid


class DesignUninformedError(ValueError):
    """Raised when a declared process has no observation path."""


class CyclicProcessDependencyError(ValueError):
    """Raised when latent-species dependencies are cyclic."""


@dataclass(frozen=True, slots=True)
class DesignReport:
    informed_processes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class LatentFields:
    log_intensity: Mapping[str, Mapping[tuple[str, int, int], object]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "log_intensity",
            MappingProxyType(
                {
                    species: MappingProxyType(dict(values))
                    for species, values in self.log_intensity.items()
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
        streams = tuple(self.streams)
        if not streams:
            raise ValueError("at least one observation stream is required")
        stream_names = [str(stream.name) for stream in streams]
        if len(set(stream_names)) != len(stream_names):
            raise ValueError("stream names must be unique")
        object.__setattr__(self, "species", MappingProxyType(species))
        object.__setattr__(self, "streams", streams)
        self._check_acyclic()

    def _check_acyclic(self) -> None:
        graph: dict[str, set[str]] = {species: set() for species in self.species}
        for target, processes in self.species.items():
            for process in processes:
                for source in getattr(process, "latent_species_dependencies", frozenset()):
                    if source not in graph:
                        raise ValueError(f"unknown latent species dependency {source!r}")
                    graph[source].add(target)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise CyclicProcessDependencyError("cyclic latent-species dependency")
            if node in visited:
                return
            visiting.add(node)
            for child in graph[node]:
                visit(child)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

    def check_design(self) -> DesignReport:
        informed: list[tuple[str, str]] = []
        for species, processes in self.species.items():
            for process in processes:
                has_path = any(
                    process.name in getattr(stream, "informs", frozenset())
                    and process.output_channel in getattr(stream, "consumes", frozenset())
                    for stream in self.streams
                )
                if not has_path:
                    raise DesignUninformedError(
                        f"process {species}:{process.name} has no process->channel->stream path"
                    )
                informed.append((species, process.name))
        return DesignReport(tuple(informed))

    def latent_fields(
        self,
        theta: Mapping[str, Mapping[str, object]],
        covariates: Mapping[tuple[str, int, int], Mapping[str, object]],
    ) -> LatentFields:
        """Construct latent ecological fields using the declared process graph.

        No scalar coercion occurs here.  This is intentional: the exact same process
        graph is used by ordinary simulation/likelihood code and by JAX/NumPyro.
        """

        missing_contexts = set(self.domain.keys) - set(covariates)
        if missing_contexts:
            raise ValueError("covariates are missing domain contexts")
        fields: dict[str, dict[tuple[str, int, int], object]] = {}
        for species, processes in self.species.items():
            if species not in theta:
                raise KeyError(f"missing parameter block for species {species!r}")
            block: dict[tuple[str, int, int], object] = {}
            for ctx in self.domain.contexts():
                context_covariates = covariates[ctx.key]
                total: object = 0.0
                for process in processes:
                    total = total + process.log_intensity(
                        ctx,
                        theta[species],
                        context_covariates,
                        latent_fields=None,
                    )
                block[ctx.key] = total
            fields[species] = block
        return LatentFields(fields)

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
    ) -> float:
        fields = self.latent_fields(theta, covariates)
        total = 0.0
        for stream in self.streams:
            stream_data = data.get(stream.name, {})
            for species in self.species:
                total += float(stream.log_lik(species, fields, stream_data.get(species, {})))
        return total
