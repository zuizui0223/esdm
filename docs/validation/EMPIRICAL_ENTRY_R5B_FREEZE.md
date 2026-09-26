# Empirical Entry Freeze — v0.4-R5b

Status: **SEMI-SYNTHETIC PROGRAMME FROZEN; EMPIRICAL OUTCOME NOT YET OPENED**

Scientific freeze source:

- branch: `feature/v04-r5b-recovery-transfer`
- R5b branch head: `3320431b300f34b326363713fb1d993ea5e43a87`
- outcome run: `35879936964`
- outcome head: `3c757ccf243c9bab415d59f40d4ab39ae2a06a69`
- gate freeze commit: `98c828797e73d6b40cf9a73651662d7877473bbc`
- gate blob: `227938d2b104d6e900dbbc7ca9d82d019db9f526`
- final artifact SHA256:
  `ead0e17a4da17b3c27b84bcbb0c4aa034379f9930ce32987e1940215ba839477`

R5b passed all frozen recovery and east-heldout transfer checks. This document therefore
ends the iterative semi-synthetic design programme for the first empirical application.

## Frozen scientific contract

The empirical application must preserve the R5b information architecture:

1. an opportunistic PresenceOnly-like count stream;
2. a calibrated PresenceOnly-like count stream with explicit known effort;
3. a state-annotated count stream informing activity and state;
4. a direct conditional state-composition calibration stream informing state only.

The ecological decomposition remains:

- suitability;
- activity;
- conditional state composition.

The first empirical application may adapt names and units to the biological system, but
may not add or remove latent processes in response to observed empirical outcomes.

## Frozen state contract

The first empirical application must preregister exactly two mutually exclusive states
before outcome inspection. The state labels may be biologically renamed, but the
two-state model structure is fixed before fitting.

The direct state-composition stream must remain conditional on state and must not carry
ecological intensity or activity information by construction.

## Frozen spatial extrapolation contract

A geographic east/extrapolation holdout must be defined from coordinates before model
fitting.

Requirements:

- non-empty training block;
- non-empty held-out block;
- held-out eastness strictly outside the training eastness range after the frozen
  training-only standardization;
- direct state-composition calibration has zero exposure in held-out contexts;
- held-out observations are not used for parameter fitting.

The exact longitude cut may be data-system specific, but it must be declared and hashed
before outcome fitting. It may not be chosen after seeing model scores.

## Frozen temporal contract

The empirical domain must retain explicit day-of-year and hour.

The R5b process covariates remain the conceptual template:

- suitability: precipitation, latitude/eastness, seasonal phase;
- activity: precipitation, eastness, seasonal phase, diurnal phase;
- state: precipitation, eastness, seasonal phase, diurnal phase.

Covariate substitutions are allowed only if declared before empirical fitting and justified
as direct measurements of the same ecological role. Outcome-conditioned feature search
is not allowed in the first empirical opening.

## Eligibility before opening outcomes

An empirical dataset is eligible only if all of the following are true before fitting:

- every observation has a stable spatial unit, day-of-year, and hour;
- spatial coordinates exist for every spatial unit;
- the environmental covariates needed by the frozen model are available or have a
  preregistered role-equivalent substitute;
- opportunistic occurrence counts can be constructed;
- at least one calibrated occurrence/effort stream exists;
- state-annotated observations exist;
- an independent/direct conditional state-composition calibration subset exists;
- the two state labels are fixed before outcome inspection;
- the direct state calibration subset is absent from the east holdout;
- the east holdout contains state-annotated observations so transfer can be scored.

If any item fails, the dataset is **INELIGIBLE FOR THIS R5b EMPIRICAL TEST**. The model is
not modified to make it fit.

## One-open rule

The first empirical result is one-shot.

Before fitting, the repository must contain:

- a dataset manifest with immutable source identifiers;
- SHA256 hashes of every local input snapshot;
- the fixed state-label mapping;
- the fixed spatial holdout rule;
- the fixed covariate mapping;
- the fixed observation-stream mapping;
- the fixed fitted-model and knockout comparison;
- the fixed MCMC profile;
- the fixed reporting endpoints;
- an explicit authorization marker.

After authorization:

- no scientific setting may change;
- failure remains failure;
- no empirical threshold may be tuned from the opened result;
- any follow-up analysis becomes a separately named exploratory programme.

## First empirical endpoints

The first empirical opening is intentionally narrow.

Primary:

- convergence/sampling diagnostics;
- posterior estimates for the frozen suitability/activity/state terms;
- east-heldout log predictive density for the full model;
- east-heldout full-minus-activity-knockout gain;
- east-heldout full-minus-state-knockout gain.

Secondary/descriptive:

- posterior uncertainty;
- state probabilities;
- activity probabilities;
- maps or temporal summaries derived from the fitted latent fields.

No empirical parameter recovery claim is possible because truth is unknown.

## Stopping rule

No new semi-synthetic v0.x gate is required before this empirical opening.

The v0.7 programme may remain in the repository as methodological robustness evidence,
but it does not reopen or revise the R5b empirical contract.

The next development milestone is therefore **empirical dataset qualification and one-shot
fit**, not v0.7l/v0.8 simulation tuning.
