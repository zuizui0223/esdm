# FIELD1 Phase-A qualification gate — Amendment 1

Status: **FROZEN BEFORE ANY FIELD1 CONFIRMATORY OUTCOME — EXECUTION NOT AUTHORIZED**

Date frozen: 2026-09-27

This amendment records implementation-integrity and pre-fit identifiability hardening
added after the initial FIELD1 qualification gate was written but before any
`FIELD1_RUN_AUTHORIZED` marker or confirmatory K0-K5 outcome existed.

It does **not** change:

- the K0-K5 truth worlds;
- the K6 barrier geometry audit;
- H1 or H2 held-out definitions;
- M0-M4 model semantics;
- the 16-replicate design;
- positive/null gain thresholds;
- the 300/350 x 2-chain MCMC profile;
- any claim-promotion rule.

## A1. Exact edge-axis rank refusal

Normalized graph conductance is invariant to multiplying every edge weight by the same
constant. Raw variation of distance/environment/barrier columns is therefore not enough.

Before fitting an active FIELD1 spatial process, the centered edge-covariate design must
have full rank for its active axes:

- M1: centered distance rank = 1;
- M2: centered [distance, environmental dissimilarity] rank = 2;
- M3: centered [distance, barrier exposure] rank = 2;
- M4: centered [distance, environmental dissimilarity, barrier exposure] rank = 3.

An exactly rank-deficient design fails closed before MCMC.

This is a structural eligibility check, not a new outcome criterion.

## A2. Frozen execution-cardinality invariants

The declared 9-world x 16-replicate matrix contains exactly:

- 144 replicate shards;
- 704 model fits.

Aggregation must reject incomplete or expanded fit plans. Extra fits may not dilute the
mean-divergence denominator, and missing fits may not silently disappear.

## A3. Infrastructure-blocked receipt

If the one-shot workflow cannot produce a complete valid frozen shard set, the aggregate
artifact must distinguish that state from a scientific FAIL:

`status = INFRASTRUCTURE_BLOCKED`

with no scientific decision.

A scientific PASS/FAIL is emitted only when all declared shards and fit-plan invariants
are present.

## A4. Implementation smoke boundary

A tiny non-confirmatory NumPyro smoke is allowed before authorization solely to verify:

```text
train domain
 -> NUTS
 -> shared FIELD1 posterior parameter sites
 -> unseen H1 projection
 -> finite held-out score
```

The smoke does not evaluate a frozen replicate family, does not enter the qualification
aggregate, and does not authorize threshold or model changes from gain signs.

## One-shot status

At this amendment freeze:

- `FIELD1_RUN_AUTHORIZED`: absent;
- qualification outcome shards: 0;
- qualification aggregate: absent;
- empirical response: unopened.


## A5. Implementation/outcome branch separation

The implementation and frozen gate are reviewed and merged without consuming the
qualification outcome.

The one-shot workflow listens only to:

`field1/qualification-v1`

That branch must be created from the merged FIELD1 implementation commit on `main`.
The authorization marker is then added as a separate commit. The implementation PR branch
`feature/field1-continuous-map-prior` cannot trigger the frozen outcome workflow.

This keeps code/gate review, outcome authorization, and result freezing as distinct
audit events.


## A6. Fresh latent-field realization per replicate

Each stochastic FIELD1 replicate must draw a fresh zero-sum latent-field innovation
vector from the declared generating distribution.

Frozen hierarchy:

```text
world hyperparameters + graph + mean coefficients
    fixed within world
latent innovations z
    independently redrawn for every replicate
Poisson observations
    independently generated conditional on that replicate's latent field
```

The latent-field seed is deterministically separated from the observation seed:

```text
generation_seed
    = base_seed + world_index * 1,000,000 + replicate * 10,000
latent_field_seed
    = generation_seed + 503
```

This prevents the 16 replicate gate from reducing to repeated observation noise around
one fixed spatial map. The qualification therefore evaluates predictive behavior across
independent realizations of the declared dependence structure.

This amendment changes no truth hyperparameter, graph, holdout, comparison, threshold,
MCMC profile, or claim rule.
