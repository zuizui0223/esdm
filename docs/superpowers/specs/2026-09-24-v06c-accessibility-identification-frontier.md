# v0.6c Static-Accessibility Identification Frontier

Status: prospective finite audit, pre-outcome.

Base: v0.6b frozen Outcome B at
`d0e82a2a3b1b79c32403ded33a26143bfa473ae3`.

## Question

v0.6b showed that joint occurrence can create local structural rank through model shape
while leaving accessibility practically weak.

v0.6c asks:

> How sensitive is that joint-only separation to the geometry of the declared predictors
> and to the accessibility regime, and how much does a direct accessibility endpoint
> stabilize the same model?

This is an assumption-reliance map, not a search for a passing configuration.

## Frozen finite grid

Three covariate geometries:

1. **distinct**
   - exact v0.6a habitat contrast;
   - exact v0.6a distance contrast.

2. **aligned**
   - habitat is the exact v0.6a habitat contrast;
   - distance is set exactly equal to habitat.
   - Any separation beyond ordinary linear predictor independence therefore comes from
     the declared intensity/accessibility functional forms.

3. **flat_access**
   - habitat retains the exact v0.6a contrast;
   - distance is exactly zero.
   - The accessibility slope has no design variation and should fail closed as
     DesignUninformed.

Three accessibility-intercept truths:

- low-access regime: `-2.0`;
- middle regime: `+0.40`;
- high-access regime: `+2.0`.

All other truths are fixed:

- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility distance slope = -1.10.

This yields exactly **9 frozen cells**.

## Observation contracts

Every cell is diagnosed twice.

### joint-only

Only AccessiblePresenceOnly:

- effort = 8.0 in all 24 contexts.

### direct-calibrated

The identical joint stream plus AccessibilityCount:

- direct accessibility effort = 20.0 in all 24 contexts.

No simulated outcomes or posterior MCMC are used.

## Frozen diagnostics

Exactly the v0.6a/v0.6b thresholds:

- JAX exact log-rate Jacobian;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

Targets are exactly:

- suitability intercept;
- habitat slope;
- accessibility intercept;
- accessibility distance slope.

The v0.6a intercept-only product control is rerun and must remain NotIdentified.

## Frozen output

For every grid cell and observation design, report:

- structural status for all four targets;
- practical weak/pass status;
- target SD proxy;
- singular-value ratio;
- condition number.

No cell is selected as a winner.

The key comparison is the full finite pattern:

- where joint-only rank is created by functional form;
- where practical information remains weak;
- where the design is truly uninformed;
- where direct accessibility observations improve or fail to improve the decomposition.

## Interpretation boundary

v0.6c is deterministic design analysis.

It does not establish parameter recovery, empirical accessibility, movement kernels,
connectivity, or causal movement limitation.

No grid cell, truth, threshold, or observation effort may be added or altered in response
to the outcome.
