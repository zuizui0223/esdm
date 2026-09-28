# AMAP1 — adaptive single-field map programme

Status: **DRAFT — NOT AUTHORIZED FOR CONFIRMATORY OUTCOME**

Date drafted: 2026-09-28

## Independent scientific question

AMAP1 does not reopen FIELD1 or MAP1 and does not try to rescue either failed claim.

FIELD1 asked whether distance, environmental similarity, and barriers could be qualified
as separate dependence axes. MAP1 asked whether a fixed geography-coherent field could
be declared predictively coherent rather than exchangeable.

AMAP1 asks a different question:

> Can one continuous residual field adapt its covariance between exchangeable and
> fixed geographic coherence, and thereby produce low-regret held-out maps when the
> true residual structure is absent, exchangeable, or coherent?

The target is robust map prediction under structural uncertainty.

No claim is made about whether geographic coherence is biologically "present".

## One latent field

Let H be the fixed orthonormal zero-sum basis on m graph nodes.

Let C_geo be the response-blind fixed coherent covariance in zero-sum coordinates,
normalized so

```text
tr(C_geo) = m - 1.
```

The exchangeable zero-sum covariance is I.

AMAP1 defines

```text
Sigma_kappa
  = sigma^2 [ (1-kappa) I + kappa C_geo ]

a ~ Normal(0, Sigma_kappa)
u = H a
```

with

```text
sigma ~ HalfNormal(0.75)
kappa ~ Beta(1, 1)
0 <= kappa <= 1
```

and a fixed response-blind geography kernel:

```text
edge weight = exp(-normalized geographic distance)
fixed rho = 1
alpha = 0.90
```

Properties:

- kappa = 0 reproduces the exchangeable zero-sum covariance;
- kappa = 1 reproduces the MAP1 fixed coherent covariance in distribution;
- every kappa has the same total conditional prior energy:
  E[||u||^2 | sigma] = sigma^2 (m-1);
- latent dimension remains m-1 for all kappa;
- the field remains exactly zero-sum and does not replace the ecological intercept.

The coherence weight is a regularization coordinate only. It is not an estimand for a
scientific mechanism claim.

## Why this is not MAP1 rescue

MAP1 failed because its discrete coherent model was not sufficiently specific in null
worlds. AMAP1 does not lower those thresholds, reinterpret those outcomes, or rerun the
same claim.

Differences in estimand:

```text
MAP1:
  "Does fixed coherence pass positive and null model-comparison gates?"

AMAP1:
  "Does one adaptive field stay predictively close to the truth-aligned oracle
   across structural uncertainty?"
```

AMAP1 therefore does not penalize the adaptive field for outperforming the oracle by
chance in a null world. It penalizes only material predictive regret.

MAP1 remains terminal FAIL regardless of AMAP1 outcome.

## Base oracle models

The already-defined map models are used only as known-truth oracle references:

- B0: environment only;
- BX: exchangeable zero-sum residual field;
- BC: fixed geography-coherent residual field;
- BA: AMAP1 adaptive covariance field.

The oracle is declared by the generating truth, never selected from outer-heldout
outcomes.

## New multi-geometry qualification universe

AMAP1 does not reuse MAP1's single frozen fixture as its sole validation universe.

Three response-blind geometry families are required:

### G1 — irregular two-dimensional lattice

A connected irregular lattice with variation in horizontal and vertical edge lengths.
Outer holdout is a central contiguous block.

### G2 — elongated corridor

A long narrow graph with local side branches. Outer holdout is a contiguous interior
segment, leaving observed nodes on both sides.

### G3 — clustered / archipelago-like graph

Two dense local clusters connected by longer sparse bridge edges. Outer holdout is a
contiguous subset of one cluster while the training set retains both local and bridge
edges.

For every geometry:

- graph construction is fixed before outcome;
- edge distances are normalized by the median positive training-independent graph edge
  length;
- the fixed coherent kernel uses the same rho=1 and alpha=0.90;
- environmental mean covariates are generated independently from the residual-field
  innovations;
- heldout nodes are omitted from fitting, not zero-effort padded.

The exact node coordinates, edge list, covariates, and outer holdout for G1-G3 must be
machine-frozen before confirmatory execution.

## Truth classes

Each geometry is crossed with three residual truth classes.

### T0 — no residual field

Truth model: B0.

Oracle reference: B0.

### TX — exchangeable residual field

Truth model: BX.

Oracle reference: BX.

Detectability firewall:

```text
BX - B0 must be positive-qualified.
```

### TC — coherent residual field

Truth model: BC.

Oracle reference: BC.

Detectability firewall:

```text
BC - B0 must be positive-qualified.
```

Every field-positive replicate draws a fresh latent realization before observation
counts.

This gives nine geometry x truth worlds.

## AMAP1 predictive estimand

For each replicate:

```text
regret
  = oracle mean heldout log predictive density
  - BA mean heldout log predictive density
```

Positive regret means the adaptive map is worse than the truth-aligned oracle.

The primary AMAP1 claim is **not** that BA beats the oracle. The target is bounded regret.

Candidate claim:

```text
LOW_REGRET_MAP_SUPPORTED
```

It may be promoted only if BA tracks the appropriate oracle across all three truth
classes and all geometry families.

## Proposed pre-outcome gate shape

Numerical thresholds remain DRAFT until frozen in a separate qualification gate.

The intended structure is:

1. **Oracle detectability**
   - TX: BX-B0 must be positive-qualified.
   - TC: BC-B0 must be positive-qualified.

2. **Adaptive regret**
   - T0: BA relative to B0 must satisfy the frozen low-regret rule.
   - TX: BA relative to BX must satisfy the frozen low-regret rule.
   - TC: BA relative to BC must satisfy the frozen low-regret rule.

3. **Cross-geometry requirement**
   - the same rule must pass separately in G1, G2, and G3;
   - success in one geometry cannot rescue failure in another.

4. **Sampling**
   - a frozen NUTS divergence guardrail applies to the complete programme.

A natural low-regret rule is based on the existing +0.005 per-context materiality scale:

```text
material regret = regret > 0.005
```

but its replicate-frequency and mean-regret thresholds are not authorized until the
full response-free fixture and fit cardinality are frozen.

## Interpretation boundary

If AMAP1 passes, allowed statements are limited to:

- one adaptive residual field can provide robust held-out maps across the declared
  structural uncertainty;
- the map does not require choosing in advance between exchangeable and fixed coherent
  residual covariance;
- the adaptive map has bounded predictive regret relative to the truth-aligned base
  model in the frozen known-truth universe.

Not allowed:

- kappa estimates dispersal;
- kappa is a probability that coherence is real;
- kappa measures connectivity or gene flow;
- a high kappa proves a spatial mechanism;
- the fixed kernel is the true ecological covariance;
- AMAP1 rescues MAP1 or FIELD1.

## Implementation plan

Phase A:

- generic `AdaptiveCoherenceMapField`;
- Beta PriorSpec support in the shared NumPyro backend;
- exact endpoint covariance tests:
  kappa=0 -> BX, kappa=1 -> BC;
- exact trace/energy invariance for all kappa;
- JAX differentiation through covariance mixture and Cholesky;
- no confirmatory run.

Phase B:

- freeze G1-G3 geometry builders;
- freeze nine known-truth worlds;
- freeze oracle-detectability and low-regret gate;
- freeze MCMC profile and fit cardinality;
- only then authorize a one-shot outcome.

## Stop rule

- MAP1 remains terminal regardless of AMAP1;
- no MAP1 threshold or world is changed;
- AMAP1 may not use MAP1 outcome values to tune kappa prior or kernel shape;
- `Beta(1,1)`, `rho=1`, `alpha=0.90`, and `HalfNormal(0.75)` are fixed before
  AMAP1 outcome;
- no empirical biological response is authorized by this draft;
- after AMAP1 qualification is frozen, failed thresholds may not be retuned.
