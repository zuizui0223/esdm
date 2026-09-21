# v0.4-R3 Budget-Neutral State Information Allocation Design

Status: **approved architectural design, pre-implementation**

Base: frozen v0.4-R2 FAIL branch head
`946451a69b79739de9564fb9a3eb6fbca6203e7c`.

This design starts a new prospective hypothesis after the frozen R2 negative result. It
does not modify, reinterpret, or retune the R2 gate. R2 remains a valid FAIL.

The R3 design changes only how state-annotated training effort is allocated. It does not
change the ecological truth, observation-process truth, identification thresholds,
identification anchors, refusal controls, or total state-annotation context budget.

## Scientific question

R2 established the following combination:

- ecological intensity versus opportunistic effort/detection was structurally separated;
- activity slopes were structurally and practically identified;
- state slopes were structurally identified;
- sparse-design and unknown-detection refusal controls behaved correctly;
- four state slopes alone became practically weak at the hard positive Anchor C;
- the R2 state-annotation budget was 432 training state-contexts:
  18 sites × 24 DOY/hour combinations.

The fresh R3 hypothesis is:

> Practical recovery of ecological state depends on how a fixed annotation budget is
> allocated across independent spatial and temporal dimensions, not only on the total
> number of annotated contexts.

R3 therefore asks whether the exact same state-annotation budget can recover the four
state slopes when annotation is spread across more spatial sites and fewer, deliberately
well-spaced temporal contexts.

This is not an R2 threshold repair. The frozen R2 criterion remains unchanged.

## Core prediction

R3 changes the positive StateAnnotatedCount training geometry from:

`18 spatial sites × 24 temporal contexts = 432 annotated contexts`

to:

`36 spatial sites × 12 temporal contexts = 432 annotated contexts`.

All other positive-profile components remain unchanged unless explicitly stated below.

If this redistribution makes all 13 frozen R2 identification targets practically
non-weak under the unchanged R2 thresholds and anchors, R3a qualifies the design for a
separate R3b outcome gate.

If R3a fails, R3 stops. The design is not tuned again after observing the failure.

## Why the intervention is isolated

The positive R3 design deliberately keeps the two observation-separation streams fixed.

### Opportunistic PresenceOnly

Unchanged from frozen R2:

- full broad coverage;
- unknown multi-covariate observation effort;
- unknown global detection;
- consumes only `log_intensity`.

### Calibrated PresenceOnly

Unchanged from frozen R2:

- 18 training calibration sites;
- all 24 temporal contexts at those sites;
- known effort and known detection;
- consumes only `log_intensity`.

The 18 calibrated sites are the first 18 sites in the deterministic spatial maximin
sequence defined below. This is the same greedy sequence used by R2.

### StateAnnotatedCount

This is the only positive-profile information geometry changed by R3:

- R2: first 18 maximin sites × all 24 temporal contexts;
- R3: first 36 maximin sites × 12 maximin temporal contexts.

Known annotated-stream effort, known annotated-stream detection, state labels, ecological
truth, activity truth, state truth, and held-out evaluation remain unchanged.

Because opportunistic and calibrated PresenceOnly information remains fixed, any R2→R3
change in state-slope practical precision is attributable to the redistribution of state
annotation information within this semi-synthetic design.

## Frozen state-annotation budget

The positive R3 training StateAnnotatedCount budget is exactly 432 exposed contexts.

No additional state-annotated training contexts are allowed.

This means R3 must not:

- increase annotated effort per exposed context;
- add extra temporal replicates;
- add more than 36 annotated training sites;
- add extra state labels;
- add additional annotation streams;
- use held-out east annotations during fitting.

The change is allocation only.

## Spatial allocation

Candidate set: all frozen training spaces.

Each space is represented in the two-dimensional vector:

`(precip_z_train, eastness_z_train)`.

The deterministic greedy maximin sequence is:

1. The first site is the station with maximum
   `precip_z_train^2 + eastness_z_train^2`.
2. Ties are broken by station ID.
3. For every later step, compute for each unselected site its minimum squared Euclidean
   distance to any already-selected site in the two-dimensional standardized plane.
4. Select the site maximizing that minimum distance.
5. Ties are broken by station ID.
6. Continue until 36 sites are selected.

The positive calibrated PresenceOnly stream uses positions 1–18 of this sequence.

The positive StateAnnotatedCount stream uses positions 1–36.

The first 18 sites must therefore remain byte-for-byte identical to the frozen R2
positive calibration site sequence when computed from the same geometry.

No counts, posterior quantities, identification diagnostics, or R2 target-SD values enter
selection.

## Temporal allocation

The temporal candidate set contains the frozen 24 combinations:

- six DOY values;
- four hour values.

Each temporal context is represented in the four-dimensional deterministic vector:

`(season_sin, season_cos, hour_sin, hour_cos)`.

The 12 annotated temporal contexts are selected by deterministic greedy maximin:

1. First context = lexicographically smallest `(doy, hour)`, which is `(15, 0)`.
2. For each unselected temporal context, calculate its minimum squared Euclidean
   distance in the four-dimensional temporal-vector space to any selected context.
3. Select the candidate maximizing that minimum distance.
4. Break ties lexicographically by `(doy, hour)`.
5. Continue until exactly 12 temporal contexts are selected.

The sine/cosine pairs are already on a common unit-circle scale, so no outcome-dependent
or data-dependent temporal standardization is applied.

No identification result enters temporal selection.

## Training and held-out geometry

### Positive training

- Opportunistic PresenceOnly: unchanged broad west+central training coverage.
- Calibrated PresenceOnly: first 18 spatial maximin sites × all 24 temporal contexts.
- StateAnnotatedCount: first 36 spatial maximin sites × selected 12 temporal contexts.

### Held-out evaluation

Held-out east annotations remain generated on all frozen east spaces × all 24 temporal
contexts.

They are not used for:

- fitting;
- spatial standardization;
- site selection;
- temporal-context selection;
- threshold selection;
- R3a qualification.

They are reserved for R3b if R3a passes.

## Prospective freeze discipline

R3a qualification results must not be computed before an R3a gate artifact is frozen.

The implementation sequence is:

1. implement and test the deterministic selectors and fixture mechanics without running the R3a practical-identification outcome;
2. write and commit the R3a qualification gate, including the unchanged thresholds, anchors, refusal controls, and exact budget rules;
3. verify the gate artifact is stable;
4. only then execute the R3a structural/practical qualification;
5. record PASS or FAIL without retuning the design.

The deterministic selected site/time identities may be recorded for audit after applying the already-frozen selection algorithm, but identification outcomes must not influence the selection.

## R3a: prospective design qualification

R3a contains **no MCMC outcome benchmark**.

Its only role is to test whether the budget-neutral redistribution creates a design
worthy of a full R3b gate.

R3a uses the same exact structural and practical identification machinery as frozen R2.

### Identification target set

The same 13 positive targets as R2:

Observation separation:

- `sp.suitability.beta_precip`;
- `stream.opportunistic.gamma_precip`;
- `stream.opportunistic.gamma_season`;
- `stream.opportunistic.gamma_hour`;
- `stream.opportunistic.detection_intercept`.

Activity:

- `sp.activity.activity_beta_precip`;
- `sp.activity.activity_beta_eastness`;
- `sp.activity.activity_beta_season`;
- `sp.activity.activity_beta_hour`.

State:

- `sp.state.beta_foraging_precip`;
- `sp.state.beta_foraging_eastness`;
- `sp.state.beta_foraging_season`;
- `sp.state.beta_foraging_hour`.

### Positive anchors

R3a reuses the frozen R2 Anchor A, Anchor B, and Anchor C parameter values exactly.

No anchor is weakened or replaced.

### Structural thresholds

Unchanged from R2:

- exact JAX `jax.jacfwd`;
- relative SVD rtol = `1e-8`;
- absolute atol = `1e-10`.

All 13 targets must be structurally `Identified` at all three anchors.

### Practical thresholds

Unchanged from R2:

- relative minimum singular value >= `1e-3`;
- condition number <= `1e3`;
- target SD proxy <= `0.25`;
- Fisher ridge = `1e-10`.

All 13 targets must be practically non-weak at all three anchors.

R3a is therefore explicitly tested against the same target-SD rule that caused the R2
failure.

## R3a refusal controls

R3a must preserve both forms of refusal established in R2.

### Sparse practical-refusal profile

The sparse profile is **not redesigned**.

It remains exactly the frozen R2 sparse geometry:

- the same four training sites minimizing `precip_z_train^2 + eastness_z_train^2`, with station-ID tie-breaker;
- calibrated PresenceOnly exposure at those four sites × all 24 temporal contexts;
- StateAnnotatedCount exposure at those four sites × all 24 temporal contexts;
- the same truth and thresholds.

Required behavior remains:

- all 13 targets structurally Identified at all three sparse anchors;
- at least one target practically weak at every sparse anchor.

This control prevents R3 from turning the practical diagnostic into a universally
permissive test.

### Unknown annotated-detection refusal

Unchanged exactly from R2:

- intercept-only activity;
- unknown annotated-stream global detection;
- no independent detection information for the annotated stream;
- same three refusal anchors.

Both:

- `sp.activity.activity_intercept`;
- `stream.annotated.detection_intercept`;

must remain structurally `NotIdentified` at all three anchors.

## R3a mechanical decision

R3a = PASS only if all are true:

1. positive structural identification passes for all 13 targets at all three anchors;
2. positive practical identification passes for all 13 targets at all three anchors;
3. sparse structural identification passes;
4. sparse practical refusal passes;
5. unknown annotated-detection refusal passes;
6. positive StateAnnotatedCount exposure count is exactly 432;
7. positive spatial annotated-site count is exactly 36;
8. positive annotated temporal-context count is exactly 12;
9. calibrated PresenceOnly positive design remains exactly 18 sites × 24 contexts;
10. the first 18 R3 spatial maximin sites equal the frozen R2 positive calibration
    sequence.

No MCMC recovery, coverage, transfer, or divergence result is part of R3a.

## R3a interpretation

### If R3a FAILS

R3 stops and records a frozen negative result.

No site count, temporal count, practical threshold, anchor, truth coefficient, or
selection algorithm may be changed in response within R3.

A further design would be a new gate version.

### If R3a PASSES

The exact qualified design is handed unchanged to R3b.

R3a PASS is not v0.4 promotion. It means only that the prospective observation design
passes the pre-MCMC identification gate.

## R3b: full validation handoff

R3b is a separate gate and must be frozen after an R3a PASS and before any R3b
outcome-producing run.

R3b must inherit unchanged from R3a/R2:

- all three streams;
- the 36 × 12 positive state-annotation geometry;
- the 18 × 24 calibrated PresenceOnly geometry;
- all ecological, observation, activity, and state truths;
- all 13 recovery targets;
- R2 recovery bias threshold;
- R2 recovery coverage threshold;
- activity-knockout held-out transfer criteria;
- state-knockout held-out transfer criteria;
- divergence criterion;
- east held-out evaluation geometry;
- activity and state knockout definitions.

R3b may define a new deterministic RNG seed sequence before outcomes, but that seed
sequence must be frozen in the R3b gate before any outcome run.

R3b must not use R2 or R3a numerical outcomes to alter scientific thresholds.

## R3b outcome structure

If qualified, R3b retains the same conceptual evaluation:

1. generate one complete multi-stream dataset per replicate;
2. fit the full model on west+central training data;
3. fit the activity knockout on the identical training data;
4. fit the state knockout on the identical training data;
5. recover the same 13 parameters from full-model posterior samples;
6. evaluate both knockouts on the same east held-out state annotations.

The full/knockout comparisons therefore continue to isolate activity and state
environmental slopes while preserving baseline intercept/composition.

## Why not simply increase annotation volume

A larger annotation sample could plausibly improve the R2 state target-SD values, but it
would only establish that more data help.

R3 instead keeps the training state-annotation context count fixed at 432.

That makes the scientific interpretation sharper:

> the arrangement of annotation effort across ecological dimensions can determine
> practical recoverability even when the number of annotated context opportunities is unchanged.

## Why not optimize directly on Fisher information

A direct Fisher-optimal or target-SD-minimizing design is deliberately rejected for R3.

R2 already exposed the state target-SD weakness. Optimizing contexts directly against the
same diagnostic used for the gate would blur the distinction between prospective design
and passing-the-test optimization.

R3 therefore uses a response-independent geometric maximin design:

- spatial maximin over declared environmental coordinates;
- temporal maximin over declared cyclic time coordinates.

The gate diagnostic evaluates the design but does not construct it.

## Compatibility and invariants

R3 must preserve:

- PR #9 v0.4 runtime semantics;
- R2 negative result and result files;
- V031/V032 frozen validation files;
- PresenceOnly legacy behavior;
- explicit observation-process parameter separation;
- state reference coding;
- static zero-exposure semantics;
- array-first JAX behavior;
- structural versus practical identification distinction;
- scientific claim boundary.

## Non-claims

R3a does not establish:

- parameter recovery;
- posterior calibration;
- held-out transfer;
- empirical biological validity;
- v0.4 promotion;
- universal optimality of the 36 × 12 allocation;
- a general theorem that spatial replication always dominates temporal replication.

Even an R3b PASS would remain semi-synthetic methodological validation.

## Planned branch decomposition

### R3a qualification PR

Stacked from PR #10.

Contains:

- deterministic 36-site spatial selector;
- deterministic 12-context temporal selector;
- R3a fixture;
- frozen R3a qualification gate;
- identification/refusal evaluation;
- audit result.

No outcome MCMC benchmark.

### R3b full-validation PR

Created only if R3a PASS.

Stacked from exact R3a reviewed head.

Contains:

- separately frozen R3b execution profile;
- replicated outcome runner;
- held-out transfer evaluation;
- frozen R3b result record.

If R3a FAILS, R3b is not created.
