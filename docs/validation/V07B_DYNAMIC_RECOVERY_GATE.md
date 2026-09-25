# v0.7b dynamic occupancy recovery and late-transfer gate

Status: **FROZEN BEFORE v0.7b MCMC OUTCOME**

Date frozen: 2026-09-25

## Scientific question

After a marginal colonization/extinction process is made identifiable by a small amount of
direct occupancy-scale information, can the declared dynamic parameters be recovered and
does that learned process improve prediction at later contexts where no direct occupancy
measurement is available?

## Frozen dynamic truth

One spatial trajectory with 12 ordered contexts:

- suitability log-intensity intercept: `alpha = 0.30`;
- initial occupancy: `psi0 = 0.20`;
- colonization probability: `gamma = 0.35`;
- extinction probability: `epsilon = 0.15`.

The fitted dynamic parameters are the corresponding declared logit-scale parameters.

Transition recursion:

```text
psi_t
  = psi_(t-1) * (1 - epsilon)
  + (1 - psi_(t-1)) * gamma
```

## Frozen information split

The generator produces:

- joint occupied-presence records at all 12 contexts;
- direct OccupancyCount only at contexts 1-4.

The fitting design sees:

- joint occupied-presence records at contexts **1-8**;
- direct OccupancyCount at contexts **1-4**;
- no joint or direct outcome from contexts 9-12.

The held-out score uses:

- joint occupied-presence records at contexts **9-12** only;
- zero direct OccupancyCount exposure in all held-out contexts.

Effort is fixed:

- joint effort = **500** at exposed joint contexts;
- direct occupancy effort = **500** at exposed direct contexts.

Thus direct occupancy calibration is strictly training-only and the late-time score cannot
be improved by directly observing held-out occupancy.

## Frozen pre-MCMC qualification

Exact JAX identification settings:

- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular-value threshold = 1e-3;
- condition-number threshold = 1e3;
- Fisher-like target-SD threshold = 0.25;
- Fisher ridge = 1e-10.

Required before any replicated MCMC:

1. all four targets are structurally Identified in the training design;
2. all four targets are practically non-weak;
3. all four target-SD proxies are <= 0.25;
4. under the matched joint-only training design, all four targets remain NotIdentified.

Targets:

- `sp.suitability.alpha`;
- `sp.occupancy.psi0_logit`;
- `sp.occupancy.gamma_logit`;
- `sp.occupancy.epsilon_logit`.

If qualification fails, replicated MCMC is not authorized.

## Frozen replicated profile

Only after qualification passes:

- replicates = **16**;
- fits per replicate = **2**;
- total fits = **32**;
- full dynamic model and explicit occupancy knockout use the same training realization;
- occupancy knockout sets `psi = 1`;
- credible mass = **0.90**;
- warmup = **300**;
- posterior samples = **350**;
- chains = **2**;
- target accept probability = **0.90**.

Fresh seed family:

- base seed = **20261117**;
- seed stride = **113**;
- replicate r data seed = `20261117 + 113*r`;
- full fit seed = data seed + 1;
- occupancy-knockout fit seed = data seed + 2.

No scientific or MCMC setting is configurable from the command line.

## Frozen recovery criteria

For each of the four free targets:

- abs(mean posterior bias) <= **0.20**;
- empirical 90% interval coverage >= **0.75**.

## Frozen late-transfer criteria

The full and occupancy-knockout fits are scored on the same held-out joint occurrence
realization at contexts 9-12.

Required:

- Full > occupancy knockout in at least **14/16 = 0.875** replicates;
- mean Full-minus-knockout held-out log predictive density >= **+0.50 nats/context**.

The minimum replicate gain is reported but is not itself a pass/fail criterion.

## Frozen sampling criterion

Across all 32 fits:

- divergences / 32 <= **0.10**.

## Mechanical decision

v0.7b = PASS only if every frozen qualification, recovery, late-transfer, and sampling
criterion passes.

A failed outcome may not be repaired inside v0.7b by changing:

- truth values;
- number or placement of training/held-out contexts;
- observation efforts;
- direct-calibration window;
- seed family;
- MCMC settings;
- bias/coverage thresholds;
- late-transfer thresholds.

## Interpretation boundary

PASS may support:

> A small training-only occupancy-scale calibration can resolve the frozen marginal
> colonization/extinction decomposition well enough to recover its parameters and improve
> prediction of later joint occurrence where occupancy itself is not directly observed.

PASS would **not** establish:

- realized binary occupancy histories;
- observed colonization/extinction events;
- dispersal or movement pathways;
- resistance or connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical validity in a biological system.

A later matched static-versus-dynamic comparison is required before claiming that temporal
recursion itself is superior to a lower-resolution static occupancy representation.
