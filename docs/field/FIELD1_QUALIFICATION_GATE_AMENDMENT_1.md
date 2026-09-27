# FIELD1 Phase-A qualification gate — Amendment 1

Status: **FROZEN BEFORE ANY FIELD1 CONFIRMATORY OUTCOME — EXECUTION NOT AUTHORIZED**

Date frozen: 2026-09-27

This amendment records implementation-integrity and pre-fit identifiability hardening
added after the initial FIELD1 qualification gate was written but before any
`FIELD1_RUN_AUTHORIZED` marker or confirmatory K0-K5 outcome existed.

The amendments below are all frozen before any confirmatory outcome. They do not change:

- the K0-K5 truth-model identities or coefficient/hyperparameter values;
- M0-M4 model semantics;
- the 16-replicate design;
- positive/null gain thresholds;
- the 300/350 x 2-chain MCMC profile;
- the scientific interpretation boundary.

They do prospectively harden response-free geometry and execution integrity where noted.

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


## A7. Learned-barrier H2 transfer geometry

The original H2 geometry held out every node on one side of the only barrier. Although
the full GMRF prior can mathematically depend on an unobserved-side coupling, that design
does not provide a clean empirical learning path for the barrier axis before transfer.

Before any confirmatory outcome, H2 is therefore hardened as follows:

- the 4 x 3 graph contains two vertical barrier boundaries;
- barrier 1 (between columns 0 and 1) lies entirely inside H2 training;
- barrier 2 (between columns 2 and 3) defines the H2 transfer boundary;
- H2 holds out only the rightmost column (column 3);
- at horizontal distance 1.0, barrier and non-barrier edges both remain present.

Thus the frozen question becomes:

> can a barrier-modified dependence rule learned from one barrier improve prediction
> across a separate barrier of the same predeclared type?

A deterministic pre-fit audit requires both a training-internal barrier edge and a
separate train-to-heldout barrier edge. Failure of that geometry blocks the barrier
claim before MCMC.

This amendment changes no M0-M4 semantics, truth hyperparameter, comparison direction,
gain threshold, replicate count, MCMC profile, or claim wording.


## A8. H1 training-edge identifiability

A pre-outcome audit found that holding out the entire top row left the H1 training graph
with exact centered collinearity between geographic edge distance and environmental
dissimilarity. In that geometry, M2 could not cleanly distinguish `rho` from `gamma`.

H1 is therefore frozen as the contiguous top-middle two-node block:

```text
(c1r2, c2r2)
```

For both H1 and H2 training graphs, the deterministic active-axis ranks must be:

```text
M1 = 1
M2 = 2
M3 = 2
M4 = 3
```

Failure of this training-only rank audit blocks the corresponding FIELD1 claim before
MCMC. The audit uses geometry/covariates only and does not inspect any simulated
confirmatory response.

This pre-outcome hardening changes no truth coefficient/hyperparameter, comparison
direction, gain threshold, replicate count, or MCMC profile.


## A9. Authorization commit purity

The qualification outcome may be triggered only by a dedicated authorization commit on
`field1/qualification-v1`.

That commit must:

- add exactly one file: `docs/field/FIELD1_RUN_AUTHORIZED`;
- change no source, test, workflow, graph, gate, contract, threshold, or documentation
  file besides the marker;
- declare `programme: FIELD1`;
- declare `implementation_parent_sha` exactly equal to the commit's `HEAD^`;
- declare the frozen gate and Amendment 1 paths exactly.

The workflow verifies these conditions before installing dependencies or launching any
replicate. This prevents authorization from being combined with a last-moment scientific
or implementation change.
