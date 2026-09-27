"""Dense FIELD1 graph precision and whitened-field transforms."""

from __future__ import annotations

import math

from .graph import FrozenSpatialGraph


def _validate_positive(name: str, value: float) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return numeric


def _validate_nonnegative(name: str, value: float) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return numeric


def dense_precision_python(
    graph: FrozenSpatialGraph,
    *,
    rho: float,
    gamma: float,
    beta: float,
    sigma: float,
    alpha: float = 0.95,
):
    """Return the proper dense precision Q = sigma^-2 (I - alpha S)."""

    rho = _validate_positive("rho", rho)
    gamma = _validate_nonnegative("gamma", gamma)
    beta = _validate_nonnegative("beta", beta)
    sigma = _validate_positive("sigma", sigma)
    alpha = float(alpha)
    if not math.isfinite(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between zero and one")

    n = graph.node_count
    edge_logs = tuple(
        (
            left,
            right,
            -edge.distance / rho
            -gamma * edge.environmental_dissimilarity
            -beta * edge.barrier_exposure,
        )
        for left, right, edge in graph.edge_indices()
    )
    log_shift = max(value for _left, _right, value in edge_logs)
    weights = [[0.0 for _ in range(n)] for _ in range(n)]
    for left, right, log_weight in edge_logs:
        weight = math.exp(log_weight - log_shift)
        weights[left][right] = weight
        weights[right][left] = weight

    degree = [math.fsum(row) for row in weights]
    if any(value <= 0.0 for value in degree):
        raise ValueError("FIELD1 precision requires positive graph degree")

    inv_sqrt = [1.0 / math.sqrt(value) for value in degree]
    inv_sigma2 = 1.0 / (sigma * sigma)
    precision = []
    for i in range(n):
        row = []
        for j in range(n):
            normalized = inv_sqrt[i] * weights[i][j] * inv_sqrt[j]
            value = (1.0 if i == j else 0.0) - alpha * normalized
            row.append(inv_sigma2 * value)
        precision.append(tuple(row))
    return tuple(precision)


def dense_precision_array(
    graph: FrozenSpatialGraph,
    *,
    rho,
    gamma,
    beta,
    sigma,
    alpha: float,
    array_module,
):
    """JAX/NumPy-compatible dense FIELD1 precision construction."""

    zero = array_module.asarray(0.0)
    edge_logs = [
        (
            left,
            right,
            -edge.distance / rho
            -gamma * edge.environmental_dissimilarity
            -beta * edge.barrier_exposure,
        )
        for left, right, edge in graph.edge_indices()
    ]
    log_shift = array_module.max(
        array_module.stack([value for _left, _right, value in edge_logs])
    )
    by_pair = {}
    for left, right, log_weight in edge_logs:
        weight = array_module.exp(log_weight - log_shift)
        by_pair[(left, right)] = weight
        by_pair[(right, left)] = weight

    rows = []
    for i in range(graph.node_count):
        rows.append(
            array_module.stack(
                [
                    by_pair.get((i, j), zero)
                    for j in range(graph.node_count)
                ]
            )
        )
    weights = array_module.stack(rows)
    degree = array_module.sum(weights, axis=1)
    inv_sqrt = 1.0 / array_module.sqrt(degree)
    normalized = inv_sqrt[:, None] * weights * inv_sqrt[None, :]
    identity = array_module.eye(graph.node_count)
    return (identity - float(alpha) * normalized) / (sigma * sigma)


def _cholesky_python(matrix):
    n = len(matrix)
    lower = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            subtotal = math.fsum(
                lower[i][k] * lower[j][k] for k in range(j)
            )
            if i == j:
                diagonal = float(matrix[i][i]) - subtotal
                if diagonal <= 0.0:
                    raise ValueError("FIELD1 precision is not positive definite")
                lower[i][j] = math.sqrt(diagonal)
            else:
                lower[i][j] = (
                    float(matrix[i][j]) - subtotal
                ) / lower[j][j]
    return lower


def zero_sum_basis_python(node_count: int):
    """Return an orthonormal Helmert basis for the zero-sum node subspace."""

    n = int(node_count)
    if n < 2:
        raise ValueError("zero-sum FIELD1 basis requires at least two nodes")
    rows = [[0.0 for _ in range(n - 1)] for _ in range(n)]
    for column in range(n - 1):
        scale = math.sqrt((column + 1) * (column + 2))
        positive = 1.0 / scale
        for row in range(column + 1):
            rows[row][column] = positive
        rows[column + 1][column] = -(column + 1) / scale
    return tuple(tuple(row) for row in rows)


def zero_sum_basis_array(node_count: int, *, array_module):
    return array_module.asarray(zero_sum_basis_python(node_count))


def _project_precision_python(precision, basis):
    n = len(precision)
    k = len(basis[0])
    result = []
    for a in range(k):
        row = []
        for b in range(k):
            value = math.fsum(
                basis[i][a] * precision[i][j] * basis[j][b]
                for i in range(n)
                for j in range(n)
            )
            row.append(value)
        result.append(tuple(row))
    return tuple(result)


def whitened_field_python(
    graph: FrozenSpatialGraph,
    innovations,
    *,
    rho: float,
    gamma: float,
    beta: float,
    sigma: float,
    alpha: float = 0.95,
):
    """Sample a proper graph-GMRF directly on the zero-sum subspace."""

    z = tuple(float(value) for value in innovations)
    expected = graph.node_count - 1
    if len(z) != expected:
        raise ValueError(
            f"FIELD1 zero-sum innovation count must be {expected}"
        )
    precision = dense_precision_python(
        graph,
        rho=rho,
        gamma=gamma,
        beta=beta,
        sigma=sigma,
        alpha=alpha,
    )
    basis = zero_sum_basis_python(graph.node_count)
    projected = _project_precision_python(precision, basis)
    lower = _cholesky_python(projected)

    coefficients = [0.0 for _ in z]
    for i in range(len(z) - 1, -1, -1):
        subtotal = math.fsum(
            lower[j][i] * coefficients[j]
            for j in range(i + 1, len(z))
        )
        coefficients[i] = (z[i] - subtotal) / lower[i][i]

    return tuple(
        math.fsum(
            basis[node][column] * coefficients[column]
            for column in range(expected)
        )
        for node in range(graph.node_count)
    )


def whitened_field_array(
    graph: FrozenSpatialGraph,
    innovations,
    *,
    rho,
    gamma,
    beta,
    sigma,
    alpha: float,
    array_module,
):
    """Differentiable zero-sum dense whitened FIELD1 transform."""

    precision = dense_precision_array(
        graph,
        rho=rho,
        gamma=gamma,
        beta=beta,
        sigma=sigma,
        alpha=alpha,
        array_module=array_module,
    )
    basis = zero_sum_basis_array(
        graph.node_count,
        array_module=array_module,
    )
    projected = (
        array_module.swapaxes(basis, -1, -2)
        @ precision
        @ basis
    )
    lower = array_module.linalg.cholesky(projected)
    coefficients = array_module.linalg.solve(
        array_module.swapaxes(lower, -1, -2),
        innovations,
    )
    return basis @ coefficients
