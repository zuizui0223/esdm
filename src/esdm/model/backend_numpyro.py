"""Optional NumPyro backend for the process-based generative model.

The backend translates backend-neutral prior declarations into NumPyro sample sites,
but delegates ecological latent-field construction and observation-rate construction to
the existing :mod:`esdm` process and stream objects.  It therefore does not maintain a
second ecological model implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import importlib.util
import sys


class NumPyroUnavailableError(RuntimeError):
    """Raised when the optional inference backend is requested but unavailable."""


def numpyro_available() -> bool:
    return sys.version_info >= (3, 11) and importlib.util.find_spec("numpyro") is not None


def _imports():
    if not numpyro_available():
        raise NumPyroUnavailableError(
            "NumPyro inference requires the optional 'inference' extra and Python >= 3.11"
        )
    import jax.numpy as jnp
    from jax import random
    import numpyro
    import numpyro.distributions as dist
    from numpyro.infer import MCMC, NUTS

    return jnp, random, numpyro, dist, MCMC, NUTS


@dataclass(frozen=True, slots=True)
class NumPyroFit:
    samples: Mapping[str, object]
    num_divergences: int
    num_warmup: int
    num_samples: int
    num_chains: int


def _parameter_layout(model):
    """Return fully qualified sample sites and backend-neutral prior specs."""

    layout: list[tuple[str, str, str, object]] = []
    for species, processes in model.species.items():
        seen_parameters: set[str] = set()
        for process in processes:
            for parameter, prior in process.priors().items():
                if parameter in seen_parameters:
                    raise ValueError(
                        f"duplicate parameter name within species {species!r}: {parameter!r}"
                    )
                seen_parameters.add(parameter)
                site = f"{species}.{process.name}.{parameter}"
                layout.append((site, species, parameter, prior))
    return tuple(layout)


def _numpyro_distribution(prior, dist):
    name = str(prior.distribution)
    parameters = dict(prior.parameters)
    if name == "Normal":
        return dist.Normal(float(parameters["loc"]), float(parameters["scale"]))
    raise NotImplementedError(f"unsupported PriorSpec distribution: {name}")


def _validate_data(model, data) -> None:
    keys = set(model.domain.keys)
    stream_names = {stream.name for stream in model.streams}
    unknown_streams = set(data) - stream_names
    if unknown_streams:
        raise ValueError(f"data contain unknown streams: {sorted(unknown_streams)}")
    for stream_name, by_species in data.items():
        unknown_species = set(by_species) - set(model.species)
        if unknown_species:
            raise ValueError(
                f"data for stream {stream_name!r} contain unknown species: {sorted(unknown_species)}"
            )
        for species, counts in by_species.items():
            unknown_keys = set(counts) - keys
            if unknown_keys:
                raise ValueError(
                    f"data for {stream_name}:{species} contain contexts outside the model domain"
                )
            if any(int(value) < 0 for value in counts.values()):
                raise ValueError("presence-only counts must be non-negative")


def make_numpyro_model(model, data, covariates):
    """Build a NumPyro callable around the existing generative graph."""

    jnp, _random, numpyro, dist, _MCMC, _NUTS = _imports()
    model.check_design()
    layout = _parameter_layout(model)
    _validate_data(model, data)
    ordered_keys = tuple(model.domain.keys)

    def program():
        theta: dict[str, dict[str, object]] = {species: {} for species in model.species}
        for site, species, parameter, prior in layout:
            theta[species][parameter] = numpyro.sample(
                site, _numpyro_distribution(prior, dist)
            )

        fields = model.latent_fields(theta, covariates)
        for stream in model.streams:
            for species in model.species:
                rate_map = stream.expected_rates(species, fields, exp_fn=jnp.exp)
                rates = jnp.stack([jnp.asarray(rate_map[key]) for key in ordered_keys])
                counts_map = data.get(stream.name, {}).get(species, {})
                counts = jnp.asarray(
                    [int(counts_map.get(key, 0)) for key in ordered_keys],
                    dtype=jnp.int32,
                )
                numpyro.sample(
                    f"obs.{stream.name}.{species}",
                    dist.Poisson(rates).to_event(1),
                    obs=counts,
                )

    return program


def fit_numpyro(
    model,
    data,
    covariates,
    *,
    rng_seed: int = 0,
    num_warmup: int = 500,
    num_samples: int = 500,
    num_chains: int = 1,
    progress_bar: bool = True,
    target_accept_prob: float = 0.8,
) -> NumPyroFit:
    """Fit the declared v0.3 generative graph with NUTS/MCMC."""

    _jnp, random, _numpyro, _dist, MCMC, NUTS = _imports()
    if num_warmup < 1 or num_samples < 1 or num_chains < 1:
        raise ValueError("num_warmup, num_samples, and num_chains must be positive")
    program = make_numpyro_model(model, data, covariates)
    kernel = NUTS(program, target_accept_prob=float(target_accept_prob))
    mcmc = MCMC(
        kernel,
        num_warmup=int(num_warmup),
        num_samples=int(num_samples),
        num_chains=int(num_chains),
        progress_bar=bool(progress_bar),
    )
    mcmc.run(random.PRNGKey(int(rng_seed)))
    samples = mcmc.get_samples(group_by_chain=False)
    extra = mcmc.get_extra_fields(group_by_chain=False)
    diverging = extra.get("diverging")
    num_divergences = 0 if diverging is None else int(diverging.sum())
    return NumPyroFit(
        samples=samples,
        num_divergences=num_divergences,
        num_warmup=int(num_warmup),
        num_samples=int(num_samples),
        num_chains=int(num_chains),
    )


def _draw_count(layout, samples) -> int:
    lengths = []
    for site, _species, _parameter, _prior in layout:
        if site not in samples:
            raise KeyError(f"posterior samples missing site {site!r}")
        lengths.append(len(samples[site]))
    if not lengths:
        return 1
    if len(set(lengths)) != 1:
        raise ValueError("posterior sample arrays must have equal draw counts")
    return lengths[0]


def posterior_record_rates(model, samples, covariates):
    """Derive record-rate draws using the existing process/stream graph.

    Returns a mapping keyed by ``(stream_name, species)``.  Each value is a tuple of
    posterior draws; every draw is a tuple ordered exactly like ``model.domain.keys``.
    """

    layout = _parameter_layout(model)
    n_draws = _draw_count(layout, samples)
    output: dict[tuple[str, str], list[tuple[float, ...]]] = {
        (stream.name, species): []
        for stream in model.streams
        for species in model.species
    }

    for draw in range(n_draws):
        theta: dict[str, dict[str, float]] = {species: {} for species in model.species}
        for site, species, parameter, _prior in layout:
            theta[species][parameter] = float(samples[site][draw])
        fields = model.latent_fields(theta, covariates)
        for stream in model.streams:
            for species in model.species:
                rate_map = stream.expected_rates(species, fields)
                output[(stream.name, species)].append(
                    tuple(float(rate_map[key]) for key in model.domain.keys)
                )

    return {key: tuple(draws) for key, draws in output.items()}
