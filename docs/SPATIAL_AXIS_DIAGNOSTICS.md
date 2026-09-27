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

This is intentionally descriptive. The package does not impose a universal cosine
threshold because acceptable conditioning depends on graph geometry, observation design,
sample size, and inferential purpose.

## FIELD1 provenance

FIELD1 Phase-A was already frozen as FAIL before these generic helpers were added. Its
post-mortem showed that distance and environmental dissimilarity were full-rank but
practically near-collinear. These helpers carry that lesson forward; they do not reopen
or reinterpret FIELD1.

See `docs/field/FIELD1_POSTMORTEM.md`.
