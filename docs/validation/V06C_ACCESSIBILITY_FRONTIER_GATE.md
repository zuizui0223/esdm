# v0.6c Accessibility Identification Frontier Gate

Status: **FROZEN BEFORE v0.6c FRONTIER OUTCOME**

Design commit:
`d725265751d7085d05d8d82bc83e32f810ef6f0a`.

## Frozen finite grid

Exactly 9 cells:

Geometry:
- distinct;
- aligned;
- flat_access.

Accessibility intercept:
- -2.0;
- +0.40;
- +2.0.

No geometry or intercept value may be added, removed, or altered after this freeze.

## Frozen ecological parameters

All cells:

- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility distance slope = -1.10.

Only accessibility intercept varies over the frozen three values.

## Frozen observation comparison

Each cell has exactly two designs.

### joint-only

- AccessiblePresenceOnly only;
- effort = 8.0 in all 24 contexts.

### direct-calibrated

- same AccessiblePresenceOnly;
- AccessibilityCount added;
- direct accessibility effort = 20.0 in all 24 contexts.

## Frozen targets

Exactly four:

- sp.suitability.suitability_intercept;
- sp.suitability.beta_habitat;
- sp.accessibility.access_intercept;
- sp.accessibility.beta_distance.

## Frozen diagnostics

- exact JAX log-rate Jacobian;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

## Hard invariant

The exact v0.6a intercept-only joint-product control is rerun.

Both:

- suitability intercept;
- accessibility intercept

must remain exact-JAX NotIdentified.

If that control fails, v0.6c is invalid.

## Output contract

For every one of the 9 cells and both observation designs, record all four targets'
structural and practical diagnostics.

The frontier is descriptive.

There is no pass target for the number of identified or practical cells.

No best geometry/regime is selected.

## Interpretation contract

The output may support statements about:

- functional-form/covariate dependence of structural rank;
- practical weakness despite structural rank;
- design-uninformed cases;
- stabilization from direct accessibility information.

It may not support:

- empirical accessibility;
- movement or dispersal kernels;
- causal movement limitation;
- selecting a favorable cell as if it were prospectively primary.

No threshold, effort, geometry, truth, or target may be changed after this freeze in
response to the outcome.
