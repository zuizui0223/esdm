# v0.6c Covariate-Alignment Stress Gate

Status: **FROZEN BEFORE v0.6c AUDIT OUTCOME**

Design commit:
`6c5641944a0a3cd112b718bc5d949607b5b52e37`.

## Frozen alignment levels

Exactly:

- rho = 0.00;
- rho = 0.50;
- rho = 0.90;
- rho = 0.99.

Distance is constructed from standardized habitat plus its orthogonalized frozen
v0.6a distance residual. No covariate row may be changed after this gate.

## Frozen truth

- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility intercept = 0.40;
- accessibility distance slope = -1.10.

## Frozen designs

At each rho:

### Joint-only
- AccessiblePresenceOnly only;
- effort = 8.0 in all 24 contexts.

### Direct-calibrated
- identical AccessiblePresenceOnly;
- AccessibilityCount added;
- direct accessibility effort = 20.0 in all 24 contexts.

## Frozen diagnostics

For all four parameters, under both designs:

- exact JAX local sensitivity;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

## Frozen primary checks

PASS only if both hold:

1. Direct-calibrated has all four targets structurally Identified and practically non-weak
   at all four rho levels.
2. At rho = 0.99, both joint-only accessibility targets
   (`access_intercept`, `beta_distance`) are practically weak.

No monotonicity requirement is imposed.

## Interpretation

PASS:

> A process-specific accessibility endpoint protects practical suitability/accessibility
> decomposition across the frozen habitat-distance alignment stress, while joint-only
> accessibility remains practically weak near alignment.

FAIL of check 1:

> The static accessibility decomposition is vulnerable even with direct accessibility
> calibration under at least one frozen alignment geometry.

FAIL of check 2 with check 1 passing:

> Predictor alignment alone does not explain joint-only practical weakness under the
> declared nonlinear model; another assumption stress is needed.

## Boundary

This does not claim that empirical island or fragmented-landscape habitat and isolation
covariates have any particular correlation. It is a deterministic design stress only.
