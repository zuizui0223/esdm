# v0.6c Budget-Matched Accessibility Evidence Benchmark

Status: prospective design, pre-outcome.

Base: v0.6b corrected static-accessibility interpretation at
`8a69c8e364c1d57352c6b9cbb79b8ca35f30e7e4`.

## Question

v0.6a showed that adding a direct AccessibilityCount endpoint improves practical
identification and enables recovery.

But that design also added observations.

v0.6c asks:

> At the same expected auxiliary record budget, does a process-specific accessibility
> endpoint carry more information about accessibility than simply collecting more joint
> occurrence records?

## Shared ecology and geometry

Use the exact v0.6a truth and 36-context geometry.

Training = first 24 contexts.
Held-out = final 12 contexts.

Truth:

- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility intercept = 0.40;
- distance/accessibility slope = -1.10.

## Shared base data

Both conditions receive the same Base AccessiblePresenceOnly realization:

- effort = 8 in all 36 contexts.

The same simulated base counts are used in both fits within each replicate.

## Auxiliary condition A: direct accessibility

AccessibilityCount:

- effort = 20 in each training context;
- effort = 0 held-out.

Expected auxiliary total under the frozen truth is computed from the shared generative
graph.

## Auxiliary condition B: matched extra joint occurrence

A second independent AccessiblePresenceOnly stream is added only in training.

Its constant effort is frozen at:

`12.168687798294679`.

This value is derived before outcome so that:

`expected total direct-access auxiliary records
 == expected total matched-joint auxiliary records`

under the frozen truth and training geometry.

The expected-budget relative error must be <= 1e-12.

Realized auxiliary counts are allowed to differ because both are Poisson samples.

## Deterministic qualification

Both designs must retain structural identification of all four targets.

The direct condition must meet the v0.6a practical threshold for all four targets.

For each accessibility target:

`direct target-SD proxy / matched-joint target-SD proxy <= 0.50`.

This establishes a material information advantage before replicated MCMC is opened.

## Replicated outcome

If qualification passes:

- 16 fresh replicates;
- two fits/replicate: Direct and MatchedJoint;
- 32 total fits;
- base joint realization shared within replicate;
- 300 warmup;
- 350 posterior samples;
- 2 chains;
- 90% intervals;
- target accept = 0.90.

Fresh seed family will be frozen before outcome.

Direct condition must retain:

- abs mean bias <= 0.15 for all four targets;
- 90% coverage >= 0.75 for all four targets.

For both accessibility targets:

- Direct posterior SD < MatchedJoint in >= 0.875 of replicates;
- mean Direct/MatchedJoint posterior-SD ratio <= 0.75.

Sampling:

- divergences / 32 <= 0.10.

## Held-out prediction

Both fitted conditions are additionally scored on the same held-out Base
AccessiblePresenceOnly counts, where neither auxiliary stream has exposure.

Held-out Direct-minus-MatchedJoint score is reported descriptively only.

No predictive winner criterion is frozen because the scientific question is process
information per auxiliary record, not generic predictive superiority.

## Interpretation boundary

PASS may support:

> A process-specific accessibility endpoint can improve practical accessibility
> estimation more efficiently than the same expected number of extra joint occurrence
> records.

It does not show that direct accessibility observations are always necessary, nor that
the accessibility process is causally correct in empirical systems.
