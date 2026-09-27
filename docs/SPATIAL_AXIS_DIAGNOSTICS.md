# Spatial covariance-axis diagnostics

These utilities are prospective design diagnostics for spatial-dependence models.

They exist because exact edge-covariate rank can be full while two covariance parameters
still perturb the normalized precision matrix in almost the same direction.

## API

```python
from esdm.field import (
    edge_axis_correlation,
    precision_sensitivity_diagnostics,
)
```

### Edge-axis correlation

`edge_axis_correlation(...)` measures Pearson correlation among frozen edge covariates
(distance, environmental dissimilarity, barrier exposure), optionally on a training-only
set of graph nodes.

Large absolute correlation is a warning about practical separation. It is not itself a
claim gate.

### Precision-sensitivity geometry

`precision_sensitivity_diagnostics(...)` finite-differences the zero-sum projected
precision with respect to the actual inference coordinates:

- `log_rho`
- `gamma`
- `beta`
- optionally `log_sigma`

It reports derivative norms and pairwise cosine similarity. Cosine near +1 or -1 means
two axes alter the precision in nearly the same/opposite direction.

It also treats the flattened, unit-normalized precision derivatives as columns of a
local sensitivity Jacobian. The returned diagnostics include:

- the normalized Gram matrix of those columns;
- its eigenvalues;
- the scale-free condition number of the normalized Jacobian,
  `sqrt(lambda_max / lambda_min)`.

This catches multi-axis ill-conditioning that is not obvious from any one pairwise
correlation. A value near 1 means locally orthogonal sensitivity directions; large values
mean the active covariance axes are jointly hard to separate. Exact local dependence
returns an infinite condition number.

This is intentionally descriptive. The package does not impose a universal cosine or
condition-number threshold because acceptable conditioning depends on graph geometry,
observation design, sample size, and inferential purpose.

## FIELD1 provenance

FIELD1 Phase-A was already frozen as FAIL before these generic helpers were added. Its
post-mortem showed that distance and environmental dissimilarity were full-rank but
practically near-collinear. These helpers carry that lesson forward; they do not reopen
or reinterpret FIELD1.

See `docs/field/FIELD1_POSTMORTEM.md`.


## Interpretation boundary

The normalized condition number is a **response-free local geometry diagnostic**, not a
posterior-identification result. It answers whether the declared covariance axes move the
projected precision in distinct directions at a chosen parameter point.

It does not by itself establish:

- that the data contain enough information to estimate those axes;
- that NUTS or another inference algorithm will be numerically stable;
- that a covariance axis has an ecological mechanism interpretation;
- that predictive gain will follow from a well-conditioned design.

Use it before outcome opening to reject obviously poor covariance decompositions or to
decide that only a single residual spatial field is interpretable.
