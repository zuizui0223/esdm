"""Structural-identification diagnostics from observation-rate sensitivities.

JAX-backed diagnostics use exact automatic differentiation and relative SVD rank.
The legacy finite-difference path remains only as a compatibility fallback when JAX
is unavailable; v0.3.2 hardening gates require the JAX path explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import math
from typing import Sequence

from .contraction import IdentificationResult, IdentificationStatus


@dataclass(frozen=True, slots=True)
class DesignJacobianDiagnostic:
    site_names: tuple[str, ...]
    target: str
    target_index: int
    observation_dimension: int
    jacobian: tuple[tuple[float, ...], ...]
    expected_rates: tuple[float, ...]
    singular_values: tuple[float, ...]
    full_rank: int
    reduced_rank: int
    target_max_abs_sensitivity: float
    rtol: float
    atol: float


def _parameter_sites(model):
    sites: list[tuple[str, str, str, str]] = []
    for species, processes in model.species.items():
        for process in processes:
            for parameter in process.priors():
                sites.append(
                    (f"{species}.{process.name}.{parameter}", "ecological", species, parameter)
                )
    for stream in model.streams:
        for parameter in getattr(stream, "priors", lambda: {})():
            sites.append(
                (f"stream.{stream.name}.{parameter}", "observation", stream.name, parameter)
            )
    return tuple(sites)


def _copy_nested(values):
    return {key: dict(block) for key, block in values.items()}


def _log_rate_vector(model, covariates, theta, theta_obs):
    """Return exposed scalar log rates through the generic observation-block API."""

    fields = model.latent_fields(theta, covariates)
    ordered_keys = tuple(model.domain.keys)
    values: list[float] = []
    for stream in model.streams:
        stream_theta = dict(theta_obs.get(stream.name, {}))
        for species in model.stream_targets(stream):
            blocks = stream.observation_blocks(
                species,
                fields,
                theta_obs=stream_theta,
                covariates=covariates,
            )
            for block in blocks:
                if tuple(block.keys) != ordered_keys:
                    raise RuntimeError(
                        "observation block order does not match model domain"
                    )
                for exposed, raw_rate in zip(
                    block.structural_exposure_mask,
                    block.rates,
                    strict=True,
                ):
                    if not exposed:
                        continue
                    rate = float(raw_rate)
                    if not math.isfinite(rate) or rate <= 0.0:
                        raise ValueError(
                            "structural identification requires finite positive "
                            "rates in exposed contexts"
                        )
                    values.append(math.log(rate))
    if not values:
        raise ValueError(
            "structural identification requires at least one exposed observation"
        )
    return tuple(values)


def _matrix_rank(matrix, *, tolerance: float) -> int:
    """Legacy absolute-tolerance rank used only by finite-difference fallback."""

    if not matrix:
        return 0
    rows = [list(map(float, row)) for row in matrix]
    n_rows = len(rows)
    n_cols = len(rows[0]) if rows else 0
    if any(len(row) != n_cols for row in rows):
        raise ValueError("matrix rows must have equal length")
    rank = 0
    pivot_col = 0
    while rank < n_rows and pivot_col < n_cols:
        pivot = max(range(rank, n_rows), key=lambda i: abs(rows[i][pivot_col]))
        if abs(rows[pivot][pivot_col]) <= tolerance:
            pivot_col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        pivot_value = rows[rank][pivot_col]
        rows[rank] = [value / pivot_value for value in rows[rank]]
        for i in range(n_rows):
            if i == rank:
                continue
            factor = rows[i][pivot_col]
            if abs(factor) <= tolerance:
                continue
            rows[i] = [rows[i][j] - factor * rows[rank][j] for j in range(n_cols)]
        rank += 1
        pivot_col += 1
    return rank


def _legacy_identify(
    model,
    covariates,
    *,
    theta,
    theta_obs,
    target: str,
    step: float,
    tolerance: float,
) -> IdentificationResult:
    sites = _parameter_sites(model)
    site_names = tuple(site for site, *_ in sites)
    delta = float(step)
    tol = float(tolerance)
    if not math.isfinite(delta) or delta <= 0.0:
        raise ValueError("step must be finite and positive")
    if not math.isfinite(tol) or tol <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    obs = {} if theta_obs is None else _copy_nested(theta_obs)
    base_theta = _copy_nested(theta)
    base = _log_rate_vector(model, covariates, base_theta, obs)
    columns: list[tuple[float, ...]] = []
    for _site, kind, block_name, parameter in sites:
        perturbed_theta = _copy_nested(base_theta)
        perturbed_obs = _copy_nested(obs)
        if kind == "ecological":
            if block_name not in perturbed_theta or parameter not in perturbed_theta[block_name]:
                raise KeyError(f"missing nominal ecological parameter {block_name}:{parameter}")
            perturbed_theta[block_name][parameter] += delta
        else:
            if block_name not in perturbed_obs or parameter not in perturbed_obs[block_name]:
                raise KeyError(f"missing nominal observation parameter {block_name}:{parameter}")
            perturbed_obs[block_name][parameter] += delta
        shifted = _log_rate_vector(model, covariates, perturbed_theta, perturbed_obs)
        columns.append(tuple((shifted[i] - base[i]) / delta for i in range(len(base))))

    target_index = site_names.index(target)
    target_column = columns[target_index]
    if max(abs(value) for value in target_column) <= tol:
        return IdentificationResult(
            status=IdentificationStatus.DESIGN_UNINFORMED,
            target=target,
            evidence=(
                "target has zero local sensitivity in all declared observations",
                "jacobian_backend=finite_difference_legacy",
            ),
        )
    full_matrix = [[columns[j][i] for j in range(len(columns))] for i in range(len(base))]
    reduced_matrix = [
        [columns[j][i] for j in range(len(columns)) if j != target_index]
        for i in range(len(base))
    ]
    full_rank = _matrix_rank(full_matrix, tolerance=tol)
    reduced_rank = _matrix_rank(reduced_matrix, tolerance=tol)
    status = IdentificationStatus.IDENTIFIED if full_rank > reduced_rank else IdentificationStatus.NOT_IDENTIFIED
    return IdentificationResult(
        status=status,
        target=target,
        evidence=(
            f"local_sensitivity_rank_full={full_rank}",
            f"local_sensitivity_rank_without_target={reduced_rank}",
            f"free_parameter_count={len(columns)}",
            f"observation_dimension={len(base)}",
            "jacobian_backend=finite_difference_legacy",
        ),
    )


def _jax_available() -> bool:
    return importlib.util.find_spec("jax") is not None


def _validate_relative_tolerances(*, rtol: float, atol: float) -> tuple[float, float]:
    relative = float(rtol)
    absolute = float(atol)
    if not math.isfinite(relative) or relative <= 0.0:
        raise ValueError("rtol must be finite and positive")
    if not math.isfinite(absolute) or absolute <= 0.0:
        raise ValueError("atol must be finite and positive")
    return relative, absolute


def _relative_svd_rank(matrix, *, rtol: float, atol: float):
    import jax.numpy as jnp

    array = jnp.asarray(matrix)
    if array.ndim != 2:
        raise ValueError("Jacobian matrix must be two-dimensional")
    if int(array.shape[1]) == 0:
        return 0, tuple(), float(atol)
    singular = tuple(float(value) for value in jnp.linalg.svd(array, compute_uv=False))
    if not singular:
        return 0, tuple(), float(atol)
    cutoff = max(float(atol), float(rtol) * singular[0])
    return sum(value > cutoff for value in singular), singular, cutoff


def design_jacobian_diagnostic(
    model,
    covariates,
    *,
    theta,
    theta_obs=None,
    target: str,
    rtol: float = 1e-8,
    atol: float = 1e-10,
) -> DesignJacobianDiagnostic:
    """Compute an exact local log-rate Jacobian with ``jax.jacfwd``.

    Statically unexposed cells are excluded using each observation block's structural
    exposure mask. Parameter-dependent zero rates are not used to redefine the design.
    Negative, non-finite, or non-positive exposed rates remain errors.
    """

    if not _jax_available():
        raise RuntimeError("JAX is required for exact structural-identification diagnostics")
    relative, absolute = _validate_relative_tolerances(rtol=rtol, atol=atol)
    model.check_design()
    sites = _parameter_sites(model)
    site_names = tuple(site for site, *_ in sites)
    target_name = str(target)
    if target_name not in site_names:
        raise KeyError(f"target is not a declared free parameter: {target_name}")

    import jax
    import jax.numpy as jnp

    jax.config.update("jax_enable_x64", True)

    obs_template = {} if theta_obs is None else _copy_nested(theta_obs)
    theta_template = _copy_nested(theta)
    values = []
    for _site, kind, block_name, parameter in sites:
        source = theta_template if kind == "ecological" else obs_template
        if block_name not in source or parameter not in source[block_name]:
            raise KeyError(f"missing nominal {kind} parameter {block_name}:{parameter}")
        values.append(source[block_name][parameter])
    nominal = jnp.asarray(values, dtype=jnp.float64)

    def unpack(vector):
        ecological = _copy_nested(theta_template)
        observation = _copy_nested(obs_template)
        for index, (_site, kind, block_name, parameter) in enumerate(sites):
            target_block = ecological if kind == "ecological" else observation
            target_block[block_name][parameter] = vector[index]
        return ecological, observation

    ordered_keys = tuple(model.domain.keys)

    def rate_blocks(vector):
        ecological, observation = unpack(vector)
        fields = model.latent_field_arrays(
            ecological,
            covariates,
            array_module=jnp,
        )
        blocks = []
        for stream in model.streams:
            stream_theta = observation.get(stream.name, {})
            for species in model.stream_targets(stream):
                blocks.extend(
                    stream.observation_blocks(
                        species,
                        fields,
                        theta_obs=stream_theta,
                        covariates=covariates,
                        array_module=jnp,
                    )
                )
        if not blocks:
            raise ValueError(
                "structural identification requires at least one observation block"
            )
        return tuple(blocks)

    nominal_blocks = rate_blocks(nominal)
    block_names = tuple(block.name for block in nominal_blocks)
    active_indices_list: list[int] = []
    offset = 0
    for block in nominal_blocks:
        if tuple(block.keys) != ordered_keys:
            raise RuntimeError(
                "observation block order does not match model domain"
            )
        mask = tuple(bool(value) for value in block.structural_exposure_mask)
        if len(mask) != len(ordered_keys):
            raise ValueError(
                "observation block structural exposure mask has wrong length"
            )
        active_indices_list.extend(
            offset + index
            for index, exposed in enumerate(mask)
            if exposed
        )
        offset += len(ordered_keys)
    active_indices = tuple(active_indices_list)
    if not active_indices:
        raise ValueError(
            "structural identification requires at least one exposed observation"
        )
    active_index_array = jnp.asarray(active_indices, dtype=jnp.int32)

    def rate_vector(vector):
        blocks = rate_blocks(vector)
        if tuple(block.name for block in blocks) != block_names:
            raise RuntimeError(
                "observation block structure changed across parameter values"
            )
        vectors = []
        for block in blocks:
            if tuple(block.keys) != ordered_keys:
                raise RuntimeError(
                    "observation block order does not match model domain"
                )
            vectors.append(jnp.asarray(block.rates))
        return (
            vectors[0]
            if len(vectors) == 1
            else jnp.concatenate(vectors, axis=0)
        )

    nominal_rates_array = rate_vector(nominal)
    nominal_rates = tuple(float(value) for value in nominal_rates_array)
    if any((not math.isfinite(value) or value < 0.0) for value in nominal_rates):
        raise ValueError(
            "structural identification requires finite non-negative expected rates"
        )
    if any(nominal_rates[index] <= 0.0 for index in active_indices):
        raise ValueError(
            "structural identification requires positive rates in exposed contexts"
        )

    def active_rate_vector(vector):
        return rate_vector(vector)[active_index_array]

    expected_rates = tuple(nominal_rates[index] for index in active_indices)
    jacobian_array = jax.jacfwd(lambda vector: jnp.log(active_rate_vector(vector)))(nominal)
    jacobian = tuple(tuple(float(value) for value in row) for row in jacobian_array)
    target_index = site_names.index(target_name)
    target_max = max(abs(row[target_index]) for row in jacobian) if jacobian else 0.0
    full_rank, singular_values, _cutoff = _relative_svd_rank(
        jacobian_array, rtol=relative, atol=absolute
    )
    reduced = jnp.delete(jacobian_array, target_index, axis=1)
    reduced_rank, _reduced_singular, _reduced_cutoff = _relative_svd_rank(
        reduced, rtol=relative, atol=absolute
    )
    return DesignJacobianDiagnostic(
        site_names=site_names,
        target=target_name,
        target_index=target_index,
        observation_dimension=len(expected_rates),
        jacobian=jacobian,
        expected_rates=expected_rates,
        singular_values=singular_values,
        full_rank=full_rank,
        reduced_rank=reduced_rank,
        target_max_abs_sensitivity=target_max,
        rtol=relative,
        atol=absolute,
    )


def _status_from_diagnostic(diagnostic: DesignJacobianDiagnostic) -> IdentificationStatus:
    if diagnostic.target_max_abs_sensitivity <= diagnostic.atol:
        return IdentificationStatus.DESIGN_UNINFORMED
    if diagnostic.full_rank > diagnostic.reduced_rank:
        return IdentificationStatus.IDENTIFIED
    return IdentificationStatus.NOT_IDENTIFIED


def _result_from_diagnostic(diagnostic: DesignJacobianDiagnostic) -> IdentificationResult:
    status = _status_from_diagnostic(diagnostic)
    evidence = [
        "jacobian_backend=jax.jacfwd",
        f"local_sensitivity_rank_full={diagnostic.full_rank}",
        f"local_sensitivity_rank_without_target={diagnostic.reduced_rank}",
        f"free_parameter_count={len(diagnostic.site_names)}",
        f"observation_dimension={diagnostic.observation_dimension}",
        f"relative_rank_rtol={diagnostic.rtol}",
        f"absolute_rank_atol={diagnostic.atol}",
        "singular_values=" + ",".join(f"{value:.12g}" for value in diagnostic.singular_values),
    ]
    if status is IdentificationStatus.DESIGN_UNINFORMED:
        evidence.insert(1, "target has zero exact local sensitivity in all declared observations")
    return IdentificationResult(status=status, target=diagnostic.target, evidence=tuple(evidence))


def identify_parameter_from_design(
    model,
    covariates,
    *,
    theta,
    theta_obs=None,
    target: str,
    step: float = 1e-5,
    tolerance: float = 1e-7,
    method: str = "auto",
    rtol: float = 1e-8,
    atol: float = 1e-10,
    anchors: Sequence[tuple[object, object]] | None = None,
) -> IdentificationResult:
    """Classify local structural identification for one free parameter.

    ``method='jax'`` uses exact autodiff plus relative SVD rank. ``method='auto'``
    selects that path when JAX is installed and otherwise preserves the frozen v0.3.1
    finite-difference behavior for base Python environments. ``method='finite_difference'``
    is an explicit legacy compatibility path and is not sufficient for v0.3.2 gates.
    """

    model.check_design()
    target_name = str(target)
    site_names = tuple(site for site, *_ in _parameter_sites(model))
    if target_name not in site_names:
        return IdentificationResult(
            status=IdentificationStatus.DESIGN_UNINFORMED,
            target=target_name,
            evidence=("target is not a declared free parameter",),
        )

    if anchors is not None:
        anchor_results = []
        for index, pair in enumerate(anchors):
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError("each identification anchor must be a (theta, theta_obs) pair")
            result = identify_parameter_from_design(
                model,
                covariates,
                theta=pair[0],
                theta_obs=pair[1],
                target=target_name,
                step=step,
                tolerance=tolerance,
                method=method,
                rtol=rtol,
                atol=atol,
                anchors=None,
            )
            anchor_results.append(result)
        if not anchor_results:
            raise ValueError("anchors must contain at least one evaluation point")
        statuses = {result.status for result in anchor_results}
        if IdentificationStatus.DESIGN_UNINFORMED in statuses:
            status = IdentificationStatus.DESIGN_UNINFORMED
        elif IdentificationStatus.NOT_IDENTIFIED in statuses:
            status = IdentificationStatus.NOT_IDENTIFIED
        else:
            status = IdentificationStatus.IDENTIFIED
        evidence = []
        for index, result in enumerate(anchor_results):
            evidence.append(f"anchor[{index}].status={result.status.value}")
            evidence.extend(f"anchor[{index}].{item}" for item in result.evidence)
        return IdentificationResult(status=status, target=target_name, evidence=tuple(evidence))

    normalized_method = str(method).strip().lower()
    if normalized_method not in {"auto", "jax", "finite_difference"}:
        raise ValueError("method must be 'auto', 'jax', or 'finite_difference'")
    use_jax = normalized_method == "jax" or (normalized_method == "auto" and _jax_available())
    if use_jax:
        if not _jax_available():
            raise RuntimeError("JAX is required when method='jax'")
        diagnostic = design_jacobian_diagnostic(
            model,
            covariates,
            theta=theta,
            theta_obs=theta_obs,
            target=target_name,
            rtol=rtol,
            atol=atol,
        )
        return _result_from_diagnostic(diagnostic)

    return _legacy_identify(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target=target_name,
        step=step,
        tolerance=tolerance,
    )
