# v0.7a dynamic occupancy identification gate

Status: **FROZEN DESIGN — NO PROMOTION RESULT**

Date frozen: 2026-09-25

## Question

Can repeated occurrence counts identify initial occupancy, colonization, and extinction
separately from the ecological intensity scale, and does a direct marginal-occupancy
calibration restore the missing information?

## Exact refusal hypothesis

The refusal model has one species, constant ecological log intensity `alpha`, and
intercept-only dynamic occupancy:

```text
psi_t = gamma + (1 - gamma - epsilon) psi_(t-1)
lambda_t = exp(alpha) psi_t effort
```

Write

```text
r = 1 - gamma - epsilon
q = gamma / (gamma + epsilon)
psi_t = q + (psi_0 - q) r^t
```

Then the joint occurrence trajectory is

```text
lambda_t / effort
  = exp(alpha) q
    + exp(alpha) (psi_0 - q) r^t
  = B + C r^t
```

The occurrence trajectory therefore exposes only three composite quantities
`(B, C, r)` while the model has four free parameters
`(alpha, psi_0, gamma, epsilon)`.

**Frozen refusal criterion:** every one of the four free parameters must be classified
`NotIdentified` by the exact JAX local-rank diagnostic in the joint-only design.

This is not a small-sample prediction. Increasing the number of occurrence time points or
records cannot create the missing occupancy scale under this frozen intercept-only model.

## Positive design

The positive model is identical except for one independent observation stream:

`OccupancyCount`

```text
lambda_occupancy = psi_t × effort × detection
```

The direct stream has exposure only in the first four of twelve declared time points.
Joint occurrence effort is 500 at all twelve time points; direct occupancy effort is 500
at those first four points and exactly zero later.

Truth is fixed before the qualification run:

```text
alpha       = 0.30
psi_0       = 0.20
gamma       = 0.35
epsilon     = 0.15
```

The fitted parameters are their declared log/logit-scale representations.

## Frozen positive criteria

For all four targets:

1. exact JAX structural status is `Identified`;
2. practical diagnostic is not weak;
3. Fisher-like target SD proxy is <= 0.25.

Shared numerical settings:

```text
structural rtol = 1e-8
structural atol = 1e-10
relative singular-value threshold = 1e-3
condition-number threshold = 1e3
target-SD threshold = 0.25
Fisher ridge = 1e-10
```

## Interpretation boundary

Passing this gate would establish only that a direct occupancy scale can make the frozen
marginal dynamic decomposition structurally and practically estimable.

It would not establish:

- realized binary occupancy histories;
- direct observation of colonization or extinction events;
- movement or dispersal pathways;
- connectivity or source-sink dynamics;
- empirical validity in a biological system.

A recovery/MCMC gate, if added, must be frozen separately after this qualification design
is mechanically resolved.
