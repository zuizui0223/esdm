# MAP1 — coherent map field programme

Status: **DRAFT — NOT AUTHORIZED FOR CONFIRMATORY OUTCOME**

Date drafted: 2026-09-27

## Independent scientific question

MAP1 does not rescue FIELD1's failed environmental/barrier covariance axes.

Its question is narrower and independent:

> does a response-blind, geography-only coherence prior improve held-out maps beyond
> both an environment-only model and an equally flexible exchangeable residual field?

The target is predictive map continuity. No covariance mechanism is interpreted.

## Why this follows scientifically from, but does not rerun, FIELD1

FIELD1 established one narrow internal flag: a spatial field can add held-out mapping
information. It failed when distance, environmental similarity, and barriers were split
into separately interpreted covariance axes, and its sampling guardrail also failed.

MAP1 removes that entire mechanistic task.

It does **not** estimate:

- spatial range;
- environmental dependence;
- barrier dependence;
- dispersal, movement, migration, or gene flow.

The fixed geography kernel is a design regularizer, not a biological parameter.

## Frozen-shape coherent field

Graph edge lengths are normalized by a response-blind reference distance before fitting.

MAP1 uses:

```text
w_ij = exp(-d_ij / 1)
S = D^(-1/2) W D^(-1/2)
Q0 = I - 0.90 S
```

The numbers `rho=1` and `alpha=0.90` are fixed design constants.

For an orthonormal zero-sum basis `H`:

```text
Q_c = H^T Q0 H
Q_c = L L^T
a = L^-T z,        z ~ Normal(0, I)
c = sqrt((m-1) / tr(Q_c^-1))
u_coherent = sigma * c * H a
sigma ~ HalfNormal(0.75)
```

Only `sigma` and the whitened latent map are inferred.

## Flexibility control

MAP1 includes an equally parameterized exchangeable field:

```text
u_exchangeable = sigma * H z
```

It has the same amplitude prior and the same number of latent innovations but contains no
geographic borrowing. The fixed constant `c` makes
`E[||u||^2 | sigma=1] = m-1` for BC, exactly matching BX, so `sigma` has the same
zero-sum RMS-amplitude meaning in both models. The only intended difference is the
response-blind correlation structure.

This makes the central contrast:

```text
coherent spatial borrowing
vs
generic latent flexibility
```

rather than spatial model versus a much smaller model.

## Finite model family

| ID | residual field |
| --- | --- |
| B0 | none |
| BX | zero-sum exchangeable |
| BC | fixed geography-coherent |

All models share the same environmental mean and observation process.

## Known-truth worlds

### N0 — no residual field

Truth: B0.

Required null comparisons:

- BC - B0 on H1
- BX - B0 on H1
- BC - BX on H1

### N1 — unstructured residual heterogeneity

Truth: BX.

Required positive comparison:

- BX - B0 on H1

Required null comparison:

- BC - BX on H1

The positive comparison makes N1 a valid detectability control: generic latent
heterogeneity must be learnable before the null BC-BX comparison can count. The null
comparison then prevents generic latent variation from being relabelled as spatial
coherence.

### P1 — coherent residual field

Truth: BC.

Required positive comparisons:

- BC - B0 on H1
- BC - BX on H1

Every replicate draws a fresh latent realization before Poisson observations are drawn.

## Held-out geometry

The initial response-free fixture is an irregular 5 x 4 graph. H1 withholds the two
central nodes `m2r1` and `m2r2`; the training domain surrounds the block on multiple
sides.

The primary estimand is mean held-out Poisson log predictive density on H1.

## Claim boundary

A future frozen gate may authorize only:

`COHERENT_MAP_SUPPORTED`

meaning the fixed geography-coherent field adds held-out map information beyond both B0
and BX while respecting the N0/N1 negative controls and a numerical sampling guardrail.

MAP1 cannot support:

- a dispersal mechanism;
- a migration rate;
- environmental isolation;
- barrier effects;
- an estimated spatial range;
- causal connectivity.

## Prior-art boundary

Structured spatial random effects and Gaussian/GMRF fields are established spatial
statistics. MAP1 does not claim their invention.

The prospective contribution is the eSDM validation contract: compare a fixed
geography-coherent field directly against an equally flexible exchangeable latent field,
with fresh latent realizations, explicit held-out geometry, negative controls, and
interpretation-bounded claims.

## Current authorization

Allowed now:

- implementation;
- deterministic tests;
- tiny compilation/numerical smoke;
- response-free design diagnostics.

Not yet allowed:

- confirmatory N0/N1/P1 execution;
- empirical response opening;
- post-outcome threshold setting.

Numerical gate thresholds and the confirmatory MCMC profile must be frozen in a later
commit before any confirmatory outcome.
