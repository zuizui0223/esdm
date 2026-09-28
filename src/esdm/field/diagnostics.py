"""Response-free diagnostics for practical separation of spatial-dependence axes.

These helpers are descriptive design diagnostics. They do not assign claim status or
authorize model promotion. In particular, exact matrix rank can be full even when two
dependence axes perturb the normalized precision in nearly the same direction.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType

from .graph import FrozenSpatialGraph
from .precision import dense_precision_python, zero_sum_basis_python


_EDGE_AXES = {
    "distance": "distance",
    "environment": "environmental_dissimilarity",
    "barrier": "barrier_exposure",
}


@dataclass(frozen=True, slots=True)
class PrecisionSensitivityDiagnostics:
    """Scale-aware and scale-free geometry of projected-precision derivatives."""

    derivative_norms: object
    cosine: object
    axes: tuple[str, ...] = ()
    normalized_gram: object = ()
    normalized_gram_eigenvalues: tuple[float, ...] = ()
    normalized_condition_number: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "derivative_norms",
            MappingProxyType(
                {str(key): float(value) for key, value in dict(self.derivative_norms).items()}
            ),
        )
        clean_cosine = MappingProxyType(
            {
                tuple(str(part) for part in key): float(value)
                for key, value in dict(self.cosine).items()
            }
        )
        axes = tuple(str(axis) for axis in self.axes)
        gram = tuple(
            tuple(float(value) for value in row)
            for row in self.normalized_gram
        )
        eigenvalues = tuple(
            float(value) for value in self.normalized_gram_eigenvalues
        )
        object.__setattr__(self, "cosine", clean_cosine)
        object.__setattr__(self, "axes", axes)
        object.__setattr__(self, "normalized_gram", gram)
        object.__setattr__(
            self,
            "normalized_gram_eigenvalues",
            eigenvalues,
        )
        object.__setattr__(
            self,
            "normalized_condition_number",
            float(self.normalized_condition_number),
        )




@dataclass(frozen=True, slots=True)
class PrecisionSensitivitySweep:
    """Sensitivity diagnostics across predeclared parameter points."""

    points: tuple[object, ...]
    diagnostics: tuple[PrecisionSensitivityDiagnostics, ...]
    worst_point_index: int
    max_condition_number: float
    min_gram_eigenvalue: float

    def __post_init__(self) -> None:
        clean_points = tuple(
            MappingProxyType(
                {str(key): float(value) for key, value in dict(point).items()}
            )
            for point in self.points
        )
        diagnostics = tuple(self.diagnostics)
        if not clean_points or len(clean_points) != len(diagnostics):
            raise ValueError(
                "precision sensitivity sweep points/diagnostics must be non-empty and aligned"
            )
        index = int(self.worst_point_index)
        if index < 0 or index >= len(clean_points):
            raise ValueError("precision sensitivity sweep worst_point_index is invalid")
        object.__setattr__(self, "points", clean_points)
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "worst_point_index", index)
        object.__setattr__(
            self,
            "max_condition_number",
            float(self.max_condition_number),
        )
        object.__setattr__(
            self,
            "min_gram_eigenvalue",
            float(self.min_gram_eigenvalue),
        )


def _eligible_edges(graph: FrozenSpatialGraph, spaces=None):
    if spaces is None:
        return tuple(graph.edges)
    eligible = {str(space) for space in spaces}
    unknown = eligible - set(graph.nodes)
    if unknown:
        raise ValueError(
            f"unknown spatial-axis diagnostic spaces: {sorted(unknown)}"
        )
    return tuple(
        edge
        for edge in graph.edges
        if edge.left in eligible and edge.right in eligible
    )


def edge_axis_correlation(
    graph: FrozenSpatialGraph,
    axis_a: str,
    axis_b: str,
    *,
    spaces=None,
) -> float:
    """Pearson correlation of two frozen edge covariate axes.

    A high absolute value warns that full rank may still correspond to weak practical
    separation. Constant axes fail closed because correlation is undefined.
    """

    a_name = str(axis_a)
    b_name = str(axis_b)
    if a_name not in _EDGE_AXES or b_name not in _EDGE_AXES:
        raise KeyError(
            f"edge axes must be chosen from {sorted(_EDGE_AXES)!r}"
        )
    edges = _eligible_edges(graph, spaces=spaces)
    if len(edges) < 2:
        raise ValueError("edge-axis correlation requires at least two eligible edges")

    a = tuple(float(getattr(edge, _EDGE_AXES[a_name])) for edge in edges)
    b = tuple(float(getattr(edge, _EDGE_AXES[b_name])) for edge in edges)
    mean_a = math.fsum(a) / len(a)
    mean_b = math.fsum(b) / len(b)
    da = tuple(value - mean_a for value in a)
    db = tuple(value - mean_b for value in b)
    ss_a = math.fsum(value * value for value in da)
    ss_b = math.fsum(value * value for value in db)
    if ss_a <= 0.0 or ss_b <= 0.0:
        raise ValueError("edge-axis correlation is undefined for a constant axis")
    covariance = math.fsum(x * y for x, y in zip(da, db, strict=True))
    return covariance / math.sqrt(ss_a * ss_b)


def _project_precision(precision, basis):
    n = len(precision)
    k = len(basis[0])
    return tuple(
        tuple(
            math.fsum(
                basis[i][a] * precision[i][j] * basis[j][b]
                for i in range(n)
                for j in range(n)
            )
            for b in range(k)
        )
        for a in range(k)
    )


def _projected_precision(
    graph,
    *,
    log_rho,
    gamma,
    beta,
    log_sigma,
    alpha,
):
    precision = dense_precision_python(
        graph,
        rho=math.exp(float(log_rho)),
        gamma=float(gamma),
        beta=float(beta),
        sigma=math.exp(float(log_sigma)),
        alpha=float(alpha),
    )
    basis = zero_sum_basis_python(graph.node_count)
    return _project_precision(precision, basis)


def _matrix_difference(a, b, denominator):
    return tuple(
        tuple(
            (float(a[i][j]) - float(b[i][j])) / float(denominator)
            for j in range(len(a[i]))
        )
        for i in range(len(a))
    )


def _matrix_norm(matrix):
    return math.sqrt(
        math.fsum(float(value) * float(value) for row in matrix for value in row)
    )


def _matrix_cosine(a, b):
    norm_a = _matrix_norm(a)
    norm_b = _matrix_norm(b)
    if norm_a <= 0.0 or norm_b <= 0.0:
        raise ValueError("precision sensitivity derivative has zero norm")
    inner = math.fsum(
        float(x) * float(y)
        for row_a, row_b in zip(a, b, strict=True)
        for x, y in zip(row_a, row_b, strict=True)
    )
    value = inner / (norm_a * norm_b)
    # Roundoff can cross the mathematical cosine boundary by a few ulps.
    return max(-1.0, min(1.0, value))




def _symmetric_eigenvalues_jacobi(matrix, *, tolerance=1e-12, max_sweeps=100):
    """Eigenvalues of a small real symmetric matrix without a NumPy dependency."""

    work = [list(map(float, row)) for row in matrix]
    n = len(work)
    if n == 0 or any(len(row) != n for row in work):
        raise ValueError("symmetric eigensolver requires a non-empty square matrix")
    if n == 1:
        return (work[0][0],)

    for _sweep in range(int(max_sweeps)):
        p = q = 0
        largest = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                value = abs(work[i][j])
                if value > largest:
                    largest = value
                    p, q = i, j
        if largest <= float(tolerance):
            break

        app = work[p][p]
        aqq = work[q][q]
        apq = work[p][q]
        angle = 0.5 * math.atan2(2.0 * apq, aqq - app)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        for k in range(n):
            if k in (p, q):
                continue
            aik = work[p][k]
            aqk = work[q][k]
            work[p][k] = work[k][p] = cos_a * aik - sin_a * aqk
            work[q][k] = work[k][q] = sin_a * aik + cos_a * aqk

        work[p][p] = (
            cos_a * cos_a * app
            - 2.0 * sin_a * cos_a * apq
            + sin_a * sin_a * aqq
        )
        work[q][q] = (
            sin_a * sin_a * app
            + 2.0 * sin_a * cos_a * apq
            + cos_a * cos_a * aqq
        )
        work[p][q] = work[q][p] = 0.0
    else:
        raise RuntimeError("symmetric eigensolver did not converge")

    return tuple(sorted(work[index][index] for index in range(n)))


def _normalized_sensitivity_gram(requested, derivatives):
    rows = []
    for left in requested:
        row = []
        for right in requested:
            if left == right:
                row.append(1.0)
            else:
                row.append(_matrix_cosine(derivatives[left], derivatives[right]))
        rows.append(tuple(row))
    gram = tuple(rows)
    eigenvalues = _symmetric_eigenvalues_jacobi(gram)

    # The Gram matrix is positive semidefinite mathematically. Clip tiny negative
    # roundoff before constructing the scale-free Jacobian condition number.
    clipped = tuple(max(0.0, value) for value in eigenvalues)
    minimum = min(clipped)
    maximum = max(clipped)
    if minimum <= 1e-12:
        condition = math.inf
    else:
        condition = math.sqrt(maximum / minimum)
    return gram, clipped, condition


def precision_sensitivity_diagnostics(
    graph: FrozenSpatialGraph,
    *,
    log_rho: float,
    gamma: float,
    beta: float,
    log_sigma: float = 0.0,
    alpha: float = 0.95,
    axes=("log_rho", "gamma", "beta"),
    step: float = 1e-5,
) -> PrecisionSensitivityDiagnostics:
    """Finite-difference sensitivity geometry of the zero-sum projected precision.

    Derivatives are taken with respect to the actual FIELD1 inference coordinates:
    `log_rho`, `gamma`, `beta`, and optionally `log_sigma`.
    Pairwise cosine near +1 or -1 means the axes perturb the projected precision in
    nearly the same/opposite direction even when an edge-covariate rank check passes.
    """

    allowed = ("log_rho", "gamma", "beta", "log_sigma")
    requested = tuple(str(axis) for axis in axes)
    if not requested or len(set(requested)) != len(requested):
        raise ValueError("precision sensitivity axes must be non-empty and unique")
    unknown = set(requested) - set(allowed)
    if unknown:
        raise KeyError(f"unknown precision sensitivity axes: {sorted(unknown)}")
    h = float(step)
    if not math.isfinite(h) or h <= 0.0:
        raise ValueError("precision sensitivity step must be finite and positive")

    point = {
        "log_rho": float(log_rho),
        "gamma": float(gamma),
        "beta": float(beta),
        "log_sigma": float(log_sigma),
    }
    if point["gamma"] < 0.0 or point["beta"] < 0.0:
        raise ValueError("gamma and beta diagnostic points must be non-negative")

    derivatives = {}
    for axis in requested:
        plus = dict(point)
        minus = dict(point)
        plus[axis] += h
        minus[axis] -= h
        # At a non-negative boundary use a forward difference instead of stepping
        # outside the declared parameter support.
        if axis in {"gamma", "beta"} and minus[axis] < 0.0:
            base = _projected_precision(
                graph,
                alpha=alpha,
                **point,
            )
            upper = _projected_precision(
                graph,
                alpha=alpha,
                **plus,
            )
            derivative = _matrix_difference(upper, base, h)
        else:
            upper = _projected_precision(
                graph,
                alpha=alpha,
                **plus,
            )
            lower = _projected_precision(
                graph,
                alpha=alpha,
                **minus,
            )
            derivative = _matrix_difference(upper, lower, 2.0 * h)
        derivatives[axis] = derivative

    norms = {axis: _matrix_norm(matrix) for axis, matrix in derivatives.items()}
    cosines = {}
    for i, left in enumerate(requested):
        for right in requested[i + 1 :]:
            cosines[(left, right)] = _matrix_cosine(
                derivatives[left],
                derivatives[right],
            )
    gram, gram_eigenvalues, condition = _normalized_sensitivity_gram(
        requested,
        derivatives,
    )
    return PrecisionSensitivityDiagnostics(
        derivative_norms=norms,
        cosine=cosines,
        axes=requested,
        normalized_gram=gram,
        normalized_gram_eigenvalues=gram_eigenvalues,
        normalized_condition_number=condition,
    )


def precision_sensitivity_sweep(
    graph: FrozenSpatialGraph,
    points,
    *,
    alpha: float = 0.95,
    axes=("log_rho", "gamma", "beta"),
    step: float = 1e-5,
) -> PrecisionSensitivitySweep:
    """Evaluate local sensitivity conditioning over predeclared parameter points."""

    clean_points = []
    diagnostics = []
    required = {"log_rho", "gamma", "beta"}
    allowed = required | {"log_sigma"}

    for raw in points:
        point = {str(key): float(value) for key, value in dict(raw).items()}
        missing = required - set(point)
        extra = set(point) - allowed
        if missing:
            raise ValueError(
                f"precision sensitivity sweep point missing keys: {sorted(missing)}"
            )
        if extra:
            raise KeyError(
                f"precision sensitivity sweep point has unknown keys: {sorted(extra)}"
            )
        point.setdefault("log_sigma", 0.0)
        clean_points.append(point)
        diagnostics.append(
            precision_sensitivity_diagnostics(
                graph,
                log_rho=point["log_rho"],
                gamma=point["gamma"],
                beta=point["beta"],
                log_sigma=point["log_sigma"],
                alpha=alpha,
                axes=axes,
                step=step,
            )
        )

    if not diagnostics:
        raise ValueError("precision sensitivity sweep requires at least one point")

    conditions = tuple(
        diagnostic.normalized_condition_number
        for diagnostic in diagnostics
    )
    worst_index = max(
        range(len(conditions)),
        key=lambda index: conditions[index],
    )
    minimum_eigenvalue = min(
        min(diagnostic.normalized_gram_eigenvalues)
        for diagnostic in diagnostics
    )
    return PrecisionSensitivitySweep(
        points=tuple(clean_points),
        diagnostics=tuple(diagnostics),
        worst_point_index=worst_index,
        max_condition_number=conditions[worst_index],
        min_gram_eigenvalue=minimum_eigenvalue,
    )
