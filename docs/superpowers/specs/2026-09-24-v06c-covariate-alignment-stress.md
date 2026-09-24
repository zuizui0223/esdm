# v0.6c Covariate-Alignment Identification Stress

Status: prospective deterministic stress, pre-outcome.

Base: v0.6b clarified accessibility interpretation at
`0eba331481bb0cd116a49fbd6ebeec3c646aeb34`.

## Question

v0.6b showed that joint occurrence alone can create local structural identification when
suitability and accessibility are assigned distinct covariates and link-function shapes,
but 3/4 targets were practically weak.

In fragmented landscapes and island systems, habitat gradients and isolation/accessibility
gradients can themselves be correlated.

v0.6c asks:

> Does increasing habitat-distance alignment make the joint-only decomposition more
> fragile, and does a process-specific AccessibilityCount endpoint preserve practical
> identification?

## Frozen geometry construction

Use the first 24 v0.6a training rows.

1. standardize the frozen habitat vector;
2. standardize the frozen distance vector;
3. residualize distance against habitat and standardize the residual;
4. construct new standardized distance vectors with target alignment

`distance_rho = rho * habitat + sqrt(1-rho^2) * orthogonal_residual`.

Frozen alignment levels:

- 0.00;
- 0.50;
- 0.90;
- 0.99.

The empirical correlation is recorded for every row.

## Frozen ecological truth

Exactly v0.6a:

- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility intercept = 0.40;
- distance/accessibility slope = -1.10.

## Frozen observation comparison

For each alignment level compare:

### Joint-only

- AccessiblePresenceOnly only;
- effort = 8.0 in all 24 contexts.

### Direct-calibrated

- the same AccessiblePresenceOnly stream;
- plus AccessibilityCount;
- accessibility effort = 20.0 in all 24 contexts.

## Frozen diagnostics

Audit the same four targets under both designs using:

- exact JAX local sensitivity;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

## Frozen primary requirements

This stress is considered protected only if:

1. the direct-calibrated design has all four targets structurally and practically
   identified at every alignment level;
2. at rho=0.99, both accessibility targets remain practically weak in the joint-only
   design.

No requirement is imposed on monotonicity of every numerical diagnostic.

## Interpretation

If both requirements hold:

> Direct accessibility observations protect practical decomposition even when habitat and
> accessibility predictors become nearly aligned, whereas joint-only accessibility
> inference remains assumption-sensitive and weak.

If direct calibration loses practical identification at any frozen alignment:

> The current static accessibility design is itself vulnerable to habitat-accessibility
> predictor alignment and must not be promoted as robust to fragmentation geometry.

If joint-only accessibility becomes practically strong at rho=0.99:

> Covariate alignment alone is not the relevant fragility mechanism under the declared
> nonlinear link; a different assumption stress is required.

## Boundary

This is an identification stress, not evidence that real island or fragmented-landscape
covariates have these correlations. It does not establish dispersal kernels,
connectivity, colonization dynamics, or causal isolation effects.
