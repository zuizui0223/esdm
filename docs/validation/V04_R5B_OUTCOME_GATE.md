# v0.4-R5b Recovery and Held-Out Transfer Gate

Status: **FROZEN BEFORE R5b OUTCOME**

R5b is the full outcome gate for the exact R5a-qualified observation design.

R5a remains a frozen PASS. R5b does not modify the R5a stream definitions, observation
geometry, label effort, truths, identification thresholds, or refusal controls.

## Frozen prerequisite

R5b may run only for the exact R5a design that passed:

- R5a qualification run: 35841753079;
- R5a qualification head:
  `f98586a61a9a3be5c7573e9e271744bd501cf11b`;
- R5a gate freeze commit:
  `d013b5168d7d10848d1d366669d45f83f873692a`;
- R5a gate blob:
  `e5cef8c3ce8e1dd096ef45cc436a93ba6740bafb`;
- R5a frozen result status: PASS.

The R5a qualification contract must still pass mechanically at R5b aggregation.

## Frozen source and spatial/temporal domain

Unchanged from R2-R5a:

- source repository: the-pudding/data;
- source commit: 3dcb0a80c838ff9503e3957d7e004a7f4b888b0a;
- path: rain/annual_precipitation.csv;
- source Git blob SHA1: 40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949;
- first 120 data rows;
- six DOY values and four hour values;
- west + central training block;
- east held-out block;
- eastness is standardized from training data only and east remains extrapolative.

## Frozen observation design

All four positive streams are unchanged from R5a.

### Opportunistic PresenceOnly

- broad west + central training coverage;
- unknown multi-covariate effort;
- unknown global detection;
- consumes only ecological log intensity.

### Calibrated PresenceOnly

- exact frozen 18-site calibration sequence;
- all 24 temporal contexts;
- 432 calibration contexts;
- known observation process.

### StateAnnotatedCount

- exact R4a/R5a 36-site spatial sequence;
- exact R4a/R5a 12 phase-balanced temporal contexts;
- 432 training contexts;
- effort = 8.0;
- known detection = 0.85;
- held-out east annotations remain available for evaluation.

### StateCompositionCount

- exact same 36 × 12 training contexts as StateAnnotatedCount;
- 432 direct state-composition contexts;
- label effort = 1.0 per exposed context;
- expected direct labels = 432.0;
- consumes only the latent state channel;
- no free observation parameter;
- **zero held-out east exposure**.

No direct state-composition observation is available in held-out scoring.

## Frozen identification prerequisite

The exact R5a qualification is required:

- same 13 R2 targets;
- same three anchors;
- JAX exact Jacobian;
- structural rtol = 1e-8;
- structural atol = 1e-10;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10;
- sparse practical refusal preserved;
- unknown annotated-detection refusal preserved.

## Frozen replicated outcome profile

R5b runs exactly 16 independently generated replicates.

Per replicate:

1. generate one complete four-stream dataset from the frozen R5a truth;
2. fit the full model on west + central training data;
3. fit the activity knockout on the identical generated training data;
4. fit the state knockout on the identical generated training data;
5. recover the same 13 full-model parameters;
6. score full and both knockouts on the identical east-heldout StateAnnotatedCount data.

Total fits = 16 × 3 = 48.

The direct StateCompositionCount stream is used during training only and contributes no
held-out observations.

## Frozen random and MCMC profile

- base seed = 20260926;
- seed stride = 47;
- replicate r seed = base seed + r × stride, for r = 0,...,15;
- full fit seed = replicate seed + 1;
- activity-knockout fit seed = replicate seed + 2;
- state-knockout fit seed = replicate seed + 3;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- credible mass = 0.90;
- target accept probability = 0.90.

No scientific or MCMC control above is configurable from the command line.

## Frozen recovery criteria

The same 13 R2 recovery targets are used.

For every target:

- absolute mean posterior bias across 16 replicates <= 0.18;
- empirical coverage of the frozen 90% posterior interval >= 0.75.

Every target must pass both conditions.

## Frozen east-heldout activity criterion

For each replicate:

`activity_gain = full east StateAnnotatedCount log score - activity-knockout score`.

Required:

- proportion of replicates with activity_gain > 0 >= 0.75;
- mean activity_gain >= 0.005.

## Frozen east-heldout state criterion

For each replicate:

`state_gain = full east StateAnnotatedCount log score - state-knockout score`.

Required:

- proportion of replicates with state_gain > 0 >= 0.75;
- mean state_gain >= 0.005.

A positive direct state-calibration score is not part of either held-out criterion.

## Frozen divergence criterion

Across all 48 fits:

- total divergences / 48 <= 0.10.

## Mechanical R5b decision

R5b = PASS only if:

1. the complete R5a qualification contract still passes;
2. replicate count = 16;
3. fit count = 48;
4. all five identification/refusal booleans remain true;
5. east extrapolation integrity remains true;
6. all 13 absolute mean-bias criteria pass;
7. all 13 coverage criteria pass;
8. activity positive-gain rate >= 0.75;
9. mean activity gain >= 0.005;
10. state positive-gain rate >= 0.75;
11. mean state gain >= 0.005;
12. mean divergences per fit <= 0.10.

No failed term can be repaired by changing a threshold or rerunning with a new scientific
profile.

## Execution architecture

The 16 replicates may run as separate fresh GitHub Actions matrix jobs to isolate JAX/XLA
memory. Aggregation must verify all 16 unique replicate indices and exact frozen seeds
before applying the gate.

Parallelization is an execution detail only and may not change generated data, model
definitions, or gate criteria.

## Interpretation

R5b PASS would show, in this semi-synthetic known-truth benchmark, that the R5 observation
contract is not only locally estimable but also supports parameter recovery and held-out
predictive information from activity and state environmental slopes.

R5b FAIL remains a valid frozen negative result and does not authorize retuning inside R5.

## Non-claims

Even R5b PASS does not establish:

- empirical biological validity;
- causal interaction identification in real data;
- universal superiority over SDM, JSDM, or ecological-network models;
- field cost-effectiveness;
- universal sufficiency of one direct label per context.
