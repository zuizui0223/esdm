# AMAP1 qualification gate

Status: **FROZEN BEFORE ANY AMAP1 CONFIRMATORY OUTCOME — EXECUTION NOT AUTHORIZED**

Date frozen: 2026-09-28

## Claim

AMAP1 qualifies exactly one claim:

`LOW_REGRET_MAP_SUPPORTED`

The claim means that the adaptive single-field model BA remains predictively close to the
truth-aligned oracle map across all frozen geometry and residual-structure worlds.

It does not mean that the inferred coherence weight is scientifically identified.

## Frozen universe

Three response-blind geometry families:

- G1: irregular 2D lattice, 24 nodes / 38 edges, central 4-node holdout;
- G2: elongated corridor with branches, 20 nodes / 19 edges, interior 3-node holdout;
- G3: two clustered patches with two long bridges, 18 nodes / 26 edges, right-cluster
  3-node holdout.

Three truth classes per geometry:

- T0: B0 truth, oracle B0;
- TX: BX truth, oracle BX;
- TC: BC truth, oracle BC.

Total: **9 worlds**.

Each world has exactly **16 independent replicates** with a fresh latent realization in
field-positive worlds.

## Fit plan

Per replicate:

- T0: fit BA and B0 = 2 fits;
- TX: fit BA, BX, and B0 = 3 fits;
- TC: fit BA, BC, and B0 = 3 fits.

Frozen total:

- **144 shards**
- **384 model fits**

The oracle is determined by known truth before fitting. It is never selected from
held-out outcomes.

## Detectability firewalls

A low-regret comparison is informative only if the relevant residual structure is itself
predictively detectable.

For every geometry:

### TX

```text
BX - B0 on outer holdout
```

must be positive-qualified.

### TC

```text
BC - B0 on outer holdout
```

must be positive-qualified.

Positive-qualified means both:

- positive-gain rate >= **0.75**
- mean gain >= **+0.005** per held-out context

## Low-regret estimand

For each replicate:

```text
regret
  = oracle mean heldout log predictive density
  - BA mean heldout log predictive density
```

Positive regret means BA is worse.

Material regret is:

```text
regret > 0.005
```

A geometry x truth world is low-regret-qualified only if both:

- material-regret rate <= **0.25**
- mean regret <= **0.005** per held-out context

BA being better than the oracle is not a failure. AMAP1 is a mapping decision problem,
not a structure-selection test.

The low-regret rule must pass separately in all nine worlds.

## Sampling guardrail

Across all 384 fits:

- mean NUTS divergences per fit <= **0.10**

Frozen MCMC profile:

- warmup: **300**
- retained samples: **350**
- chains: **2**
- target accept probability: **0.90**
- progress bar disabled in confirmatory automation

## Parameter non-gates

No PASS condition uses:

- posterior mean or interval of kappa;
- recovery of kappa=0 or kappa=1;
- posterior probability that kappa exceeds a threshold;
- recovery of individual latent innovations.

The adaptive weight remains interpretation-bounded.

## Promotion rule

`LOW_REGRET_MAP_SUPPORTED = true` only if:

1. all six TX/TC oracle-detectability comparisons pass;
2. all nine BA-vs-oracle low-regret comparisons pass;
3. the global sampling guardrail passes;
4. all shard and fit cardinality checks pass.

No geometry can rescue another geometry.

## Nonclaims

Even a PASS would not support:

- geographic coherence as a biological mechanism;
- dispersal or movement;
- migration or gene flow;
- environmental isolation;
- a barrier effect;
- interpretation of kappa as a probability that spatial coherence is true.

## Stop rule

After one-shot authorization:

- G1-G3 graphs and holdouts cannot change;
- T0/TX/TC truths cannot change;
- priors, fixed rho, alpha, and amplitude normalization cannot change;
- thresholds cannot change;
- the MCMC profile cannot change;
- failed worlds cannot be dropped;
- no same-program AMAP1 rescue generation may be created.

A material infrastructure bug may be repaired only by an explicit replacement
authorization that preserves every scientific item above.
