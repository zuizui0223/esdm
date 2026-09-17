"""Optional NumPyro backend for the process-based generative model.

The backend translates backend-neutral ecological and observation-process priors into
NumPyro sample sites, but delegates latent-field construction and observation-rate
construction to the existing :mod:`esdm` objects. It therefore does not maintain a
second ecological or observation model implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
import importlib.util
import math
import random as py_random
import sys

from .compose import MissingTargetDataError


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
    samples_by_chain: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "samples", MappingProxyType(dict(self.samples)))
        if self.samples_by_chain is not None:
            object.__setattr__(
                self,
                "samples_by_chain",
                MappingProxyType(dict(self.samples_by_chain)),
            )


@dataclass(frozen=True, slots=True)
class NumPyroSBCResult:
    ranks: Mapping[str, tuple[int, ...]]
    posterior_draw_count: int
    replicates: int
    divergences_by_replicate: tuple[int, ...]
    draw_counts_by_site: Mapping[str, tuple[int, ...]] | None = None
    effective_sample_sizes_by_site: Mapping[str, tuple[float, ...]] | None = None
    num_chains: int = 1

    def __post_init__(self) -> None:
        clean_ranks = {site: tuple(values) for site, values in self.ranks.items()}
        object.__setattr__(self, "ranks", MappingProxyType(clean_ranks))
        if self.draw_counts_by_site is None:
            counts = {
                site: tuple(int(self.posterior_draw_count) for _ in values)
                for site, values in clean_ranks.items()
            }
        else:
            counts = {
                site: tuple(int(value) for value in values)
                for site, values in self.draw_counts_by_site.items()
            }
        if self.effective_sample_sizes_by_site is None:
            ess = {
                site: tuple(float(value) for value in counts[site])
                for site in clean_ranks
            }
        else:
            ess = {
                site: tuple(float(value) for value in values)
                for site, values in self.effective_sample_sizes_by_site.items()
            }
        if set(counts) != set(clean_ranks) or set(ess) != set(clean_ranks):
            raise ValueError("SBC rank, draw-count, and ESS sites must match")
        for site in clean_ranks:
            if not (
                len(clean_ranks[site]) == len(counts[site]) == len(ess[site]) == self.replicates
            ):
                raise ValueError("SBC per-site vectors must match replicate count")
        object.__setattr__(self, "draw_counts_by_site", MappingProxyType(counts))
        object.__setattr__(self, "effective_sample_sizes_by_site", MappingProxyType(ess))


def _parameter_layout(model):
    """Return fully qualified ecological sample sites and prior specs."""

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


def _observation_parameter_layout(model):
    """Return fully qualified observation-process sample sites and prior specs."""

    layout: list[tuple[str, str, str, object]] = []
    for stream in model.streams:
        priors = dict(getattr(stream, "priors", lambda: {})())
        for parameter, prior in priors.items():
            site = f"stream.{stream.name}.{parameter}"
            layout.append((site, stream.name, parameter, prior))
    return tuple(layout)


def _all_sample_sites(model) -> tuple[str, ...]:
    return tuple(site for site, *_ in _parameter_layout(model)) + tuple(
        site for site, *_ in _observation_parameter_layout(model)
    )


def _numpyro_distribution(prior, dist):
    name = str(prior.distribution)
    parameters = dict(prior.parameters)
    if name == "Normal":
        return dist.Normal(float(parameters["loc"]), float(parameters["scale"]))
    raise NotImplementedError(f"unsupported PriorSpec distribution: {name}")


def _sample_prior_value(prior, rng: py_random.Random) -> float:
    name = str(prior.distribution)
    parameters = dict(prior.parameters)
    if name == "Normal":
        return rng.gauss(float(parameters["loc"]), float(parameters["scale"]))
    raise NotImplementedError(f"unsupported PriorSpec distribution: {name}")


def _sample_prior_state(model, rng: py_random.Random):
    theta: dict[str, dict[str, float]] = {species: {} for species in model.species}
    theta_obs: dict[str, dict[str, float]] = {stream.name: {} for stream in model.streams}
    truth_by_site: dict[str, float] = {}
    for site, species, parameter, prior in _parameter_layout(model):
        value = _sample_prior_value(prior, rng)
        theta[species][parameter] = value
        truth_by_site[site] = value
    for site, stream_name, parameter, prior in _observation_parameter_layout(model):
        value = _sample_prior_value(prior, rng)
        theta_obs[stream_name][parameter] = value
        truth_by_site[site] = value
    return theta, theta_obs, truth_by_site


def _sample_prior_theta(model, rng: py_random.Random):
    """Compatibility helper returning only ecological prior draws."""

    theta, _theta_obs, truth_by_site = _sample_prior_state(model, rng)
    ecological_sites = {site for site, *_ in _parameter_layout(model)}
    return theta, {site: value for site, value in truth_by_site.items() if site in ecological_sites}


def _validate_data(model, data) -> None:
    keys = set(model.domain.keys)
    stream_names = {stream.name for stream in model.streams}
    unknown_streams = set(data) - stream_names
    if unknown_streams:
        raise ValueError(f"data contain unknown streams: {sorted(unknown_streams)}")

    for stream in model.streams:
        if stream.name not in data:
            raise MissingTargetDataError(
                f"missing data block for stream {stream.name!r}"
            )
        by_species = data[stream.name]
        targets = set(model.stream_targets(stream))
        unexpected_species = set(by_species) - targets
        if unexpected_species:
            raise ValueError(
                f"data for stream {stream.name!r} contain non-target species: "
                f"{sorted(unexpected_species)}"
            )
        missing_species = targets - set(by_species)
        if missing_species:
            raise MissingTargetDataError(
                f"stream {stream.name!r} is missing target species blocks: "
                f"{sorted(missing_species)}"
            )
        for species, counts in by_species.items():
            unknown_keys = set(counts) - keys
            if unknown_keys:
                raise ValueError(
                    f"data for {stream.name}:{species} contain contexts outside the model domain"
                )
            if any(int(value) < 0 for value in counts.values()):
                raise ValueError("presence-only counts must be non-negative")


def make_numpyro_model(model, data, covariates):
    """Build a NumPyro callable around the existing generative graph.

    Statically known zero-exposure cells are omitted from the Poisson observation vector.
    They represent no observation opportunity, not a rate-zero likelihood constraint at a
    non-differentiable boundary. Positive counts in such cells fail closed.
    """

    jnp, _random, numpyro, dist, _MCMC, _NUTS = _imports()
    model.check_design()
    ecological_layout = _parameter_layout(model)
    observation_layout = _observation_parameter_layout(model)
    _validate_data(model, data)
    ordered_keys = tuple(model.domain.keys)

    active_indices: dict[tuple[str, str], tuple[int, ...]] = {}
    active_counts: dict[tuple[str, str], tuple[int, ...]] = {}
    for stream in model.streams:
        mask = tuple(stream.structural_exposure_mask(ordered_keys))
        if len(mask) != len(ordered_keys):
            raise ValueError(
                f"stream {stream.name!r} structural exposure mask has wrong length"
            )
        for species in model.stream_targets(stream):
            counts_map = data[stream.name][species]
            impossible = [
                key
                for key, exposed in zip(ordered_keys, mask, strict=True)
                if not exposed and int(counts_map.get(key, 0)) > 0
            ]
            if impossible:
                raise ValueError(
                    f"positive count in zero-exposure context for {stream.name}:{species}: "
                    f"{impossible[0]!r}"
                )
            indices = tuple(index for index, exposed in enumerate(mask) if exposed)
            if not indices:
                raise ValueError(
                    f"stream {stream.name!r} has no structurally exposed contexts"
                )
            active_indices[(stream.name, species)] = indices
            active_counts[(stream.name, species)] = tuple(
                int(counts_map.get(ordered_keys[index], 0)) for index in indices
            )

    def program():
        theta: dict[str, dict[str, object]] = {species: {} for species in model.species}
        theta_obs: dict[str, dict[str, object]] = {
            stream.name: {} for stream in model.streams
        }
        for site, species, parameter, prior in ecological_layout:
            theta[species][parameter] = numpyro.sample(
                site, _numpyro_distribution(prior, dist)
            )
        for site, stream_name, parameter, prior in observation_layout:
            theta_obs[stream_name][parameter] = numpyro.sample(
                site, _numpyro_distribution(prior, dist)
            )

        fields = model.latent_field_arrays(
            theta,
            covariates,
            array_module=jnp,
        )
        for stream in model.streams:
            stream_theta = theta_obs[stream.name]
            for species in model.stream_targets(stream):
                rate_array = stream.expected_rate_array(
                    species,
                    fields,
                    theta_obs=stream_theta,
                    covariates=covariates,
                    array_module=jnp,
                )
                if rate_array.keys != ordered_keys:
                    raise RuntimeError("array rate order does not match model domain")
                indices = active_indices[(stream.name, species)]
                index_array = jnp.asarray(indices, dtype=jnp.int32)
                rates = rate_array.values[index_array]
                counts = jnp.asarray(
                    active_counts[(stream.name, species)],
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
    """Fit the declared generative graph with NUTS/MCMC."""

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
        chain_method="sequential",
        progress_bar=bool(progress_bar),
    )
    mcmc.run(random.PRNGKey(int(rng_seed)))
    samples = mcmc.get_samples(group_by_chain=False)
    samples_by_chain = mcmc.get_samples(group_by_chain=True)
    extra = mcmc.get_extra_fields(group_by_chain=False)
    diverging = extra.get("diverging")
    num_divergences = 0 if diverging is None else int(diverging.sum())
    return NumPyroFit(
        samples=samples,
        samples_by_chain=samples_by_chain,
        num_divergences=num_divergences,
        num_warmup=int(num_warmup),
        num_samples=int(num_samples),
        num_chains=int(num_chains),
    )


def _effective_sample_size(chain_values) -> float:
    """Return scalar ESS from NumPyro's chain-aware diagnostic."""

    if not numpyro_available():
        raise NumPyroUnavailableError("NumPyro is required to estimate effective sample size")
    import jax.numpy as jnp
    from numpyro.diagnostics import effective_sample_size

    array = jnp.asarray(chain_values)
    if array.ndim != 2:
        raise ValueError("ESS thinning currently requires scalar parameters with chain x draw arrays")
    value = float(effective_sample_size(array))
    total = int(array.shape[0] * array.shape[1])
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("effective sample size must be finite and positive")
    return min(float(total), value)


def run_numpyro_sbc(
    model,
    covariates,
    *,
    replicates: int,
    rng_seed: int = 0,
    num_warmup: int = 200,
    num_samples: int = 200,
    num_chains: int = 1,
    ess_thinning: bool = False,
    progress_bar: bool = False,
    target_accept_prob: float = 0.8,
) -> NumPyroSBCResult:
    """Run prior-draw -> in-model simulate -> joint fit -> rank cycles.

    When ``ess_thinning`` is enabled, ranks are computed from draws thinned using a
    chain-aware ESS estimate. The retained finite support is recorded for every
    parameter and replicate so downstream ECDF tests can use the exact discrete null.
    """

    from esdm.identify import ess_thin_draws
    from esdm.simulate.in_model import simulate_presence_only

    n_rep = int(replicates)
    n_chains = int(num_chains)
    if n_rep < 1:
        raise ValueError("replicates must be positive")
    if n_chains < 1:
        raise ValueError("num_chains must be positive")
    rng = py_random.Random(int(rng_seed))
    sites = _all_sample_sites(model)
    ranks: dict[str, list[int]] = {site: [] for site in sites}
    draw_counts: dict[str, list[int]] = {site: [] for site in sites}
    ess_values: dict[str, list[float]] = {site: [] for site in sites}
    divergences: list[int] = []

    for _ in range(n_rep):
        theta, theta_obs, truth_by_site = _sample_prior_state(model, rng)
        generated = simulate_presence_only(
            model,
            theta,
            covariates,
            theta_obs=theta_obs,
            seed=rng.randrange(0, 2**31 - 1),
        )
        fit = fit_numpyro(
            model,
            generated.counts,
            covariates,
            rng_seed=rng.randrange(0, 2**31 - 1),
            num_warmup=num_warmup,
            num_samples=num_samples,
            num_chains=n_chains,
            progress_bar=progress_bar,
            target_accept_prob=target_accept_prob,
        )
        divergences.append(fit.num_divergences)
        for site in sites:
            truth = truth_by_site[site]
            raw_draws = tuple(float(draw) for draw in fit.samples[site])
            if ess_thinning:
                if fit.samples_by_chain is None:
                    raise RuntimeError("chain-structured samples are required for ESS thinning")
                ess = _effective_sample_size(fit.samples_by_chain[site])
                thinned = ess_thin_draws(raw_draws, effective_sample_size=ess)
                rank_draws = thinned.draws
                retained = thinned.draw_count
            else:
                ess = float(len(raw_draws))
                rank_draws = raw_draws
                retained = len(raw_draws)
            ranks[site].append(sum(float(draw) < truth for draw in rank_draws))
            draw_counts[site].append(retained)
            ess_values[site].append(ess)

    return NumPyroSBCResult(
        ranks={site: tuple(values) for site, values in ranks.items()},
        posterior_draw_count=int(num_samples) * n_chains,
        replicates=n_rep,
        divergences_by_replicate=tuple(divergences),
        draw_counts_by_site={site: tuple(values) for site, values in draw_counts.items()},
        effective_sample_sizes_by_site={
            site: tuple(values) for site, values in ess_values.items()
        },
        num_chains=n_chains,
    )


def _draw_count(site_names, samples) -> int:
    lengths = []
    for site in site_names:
        if site not in samples:
            raise KeyError(f"posterior samples missing site {site!r}")
        lengths.append(len(samples[site]))
    if not lengths:
        return 1
    if len(set(lengths)) != 1:
        raise ValueError("posterior sample arrays must have equal draw counts")
    return lengths[0]


def posterior_record_rates(model, samples, covariates):
    """Derive record-rate draws using the existing process/stream graph."""

    ecological_layout = _parameter_layout(model)
    observation_layout = _observation_parameter_layout(model)
    n_draws = _draw_count(_all_sample_sites(model), samples)
    output: dict[tuple[str, str], list[tuple[float, ...]]] = {
        (stream.name, species): []
        for stream in model.streams
        for species in model.stream_targets(stream)
    }

    for draw in range(n_draws):
        theta: dict[str, dict[str, float]] = {species: {} for species in model.species}
        theta_obs: dict[str, dict[str, float]] = {
            stream.name: {} for stream in model.streams
        }
        for site, species, parameter, _prior in ecological_layout:
            theta[species][parameter] = float(samples[site][draw])
        for site, stream_name, parameter, _prior in observation_layout:
            theta_obs[stream_name][parameter] = float(samples[site][draw])
        fields = model.latent_fields(theta, covariates)
        for stream in model.streams:
            for species in model.stream_targets(stream):
                rate_map = stream.expected_rates(
                    species,
                    fields,
                    theta_obs=theta_obs[stream.name],
                    covariates=covariates,
                )
                output[(stream.name, species)].append(
                    tuple(float(rate_map[key]) for key in model.domain.keys)
                )

    return {key: tuple(draws) for key, draws in output.items()}
