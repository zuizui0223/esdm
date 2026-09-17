"""JAX trace-size diagnostics for the array-first generative path."""

from __future__ import annotations


def array_trace_equation_count(model, covariates, theta, theta_obs) -> int:
    """Return the JAXPR equation count for all declared expected-rate vectors.

    The diagnostic treats ecological and observation parameters as traced PyTree
    inputs while covariates remain fixed design constants. A vectorized model should
    therefore have a graph size governed by process terms, not by context count.
    """

    try:
        import jax
        import jax.numpy as jnp
    except ImportError as exc:  # pragma: no cover - exercised only without inference extra
        raise RuntimeError("JAX is required for array trace diagnostics") from exc

    def rate_vector(ecological_parameters, observation_parameters):
        fields = model.latent_field_arrays(
            ecological_parameters,
            covariates,
            array_module=jnp,
        )
        vectors = []
        for stream in model.streams:
            stream_theta = observation_parameters.get(stream.name, {})
            for species in model.stream_targets(stream):
                vectors.append(
                    stream.expected_rate_array(
                        species,
                        fields,
                        theta_obs=stream_theta,
                        covariates=covariates,
                        array_module=jnp,
                    ).values
                )
        if not vectors:
            raise ValueError("model has no targeted observation-rate vectors")
        if len(vectors) == 1:
            return vectors[0]
        return jnp.concatenate(vectors, axis=0)

    closed = jax.make_jaxpr(rate_vector)(theta, theta_obs)
    return int(len(closed.jaxpr.eqns))
