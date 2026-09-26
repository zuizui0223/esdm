# v0.4-R5 Direct State-Composition Calibration Design

Status: **approved prospective design, pre-qualification**

Base: frozen R4a FAIL branch head
`ea32219e65c8f0a7ba700ace2259439323027ad2`.

R5 begins a new observation-contract hypothesis after three frozen 432-context designs:
R2, R3a, and R4a.

## What the previous gates established

R4a repaired all practical failures at Anchors A and B, but Anchor C still left all four
state slopes above the unchanged target-SD threshold. The system remained structurally
identified and globally well-conditioned.

The next test therefore does not reshuffle the same context cells again.

## Scientific hypothesis

The existing `StateAnnotatedCount` stream has expected state-specific counts proportional
to:

`exp(log_intensity) × activity × effort × detection × state_probability`.

State information therefore becomes weak when ecological intensity or activity is low,
even when state labels are structurally available.

R5 tests a distinct observation contract:

> a small direct calibration sample of conditional state composition can supply the
> state-specific information that abundance/activity-weighted annotated counts cannot.

## Generic new stream

R5 introduces `StateCompositionCount`.

For exposed context c and state s:

`lambda_state_cal[c,s] = label_effort[c] × P(state=s | active, available, c)`.

Properties:

- consumes only the latent `state` channel;
- does not consume ecological intensity;
- does not consume activity;
- has no detection parameter because it is conditional on a focal individual entering
  the calibration sample;
- uses the existing backend-neutral Poisson observation-block path;
- total expected labels at a context equal the declared label effort exactly.

This is a Poissonized conditional-composition calibration device, not a claim that every
empirical protocol literally has Poisson label totals.

## Prospective R5a positive design

R5a inherits the complete R4a positive model and adds one stream only.

Unchanged:

- opportunistic PresenceOnly;
- calibrated PresenceOnly;
- StateAnnotatedCount;
- R4a 36-site annotated spatial sequence;
- R4a 12-context phase-balanced temporal sequence;
- 432 existing StateAnnotatedCount context opportunities;
- all truth coefficients;
- all R2 anchors;
- all 13 identification targets;
- all structural/practical thresholds;
- held-out east geometry.

New state-composition calibration:

- exposed at the exact same 36 × 12 R4a training contexts;
- zero exposure outside those training contexts;
- label effort = 1.0 at every exposed context;
- expected direct labels = 36 × 12 × 1 = **432**;
- target species = `sp`;
- state space = `resting, foraging`;
- informs only the `state` process.

The value 1.0 is frozen as the unit-label design: one expected classified focal
individual per exposed context. It is not selected from R4a target-SD values.

## Qualification discipline

R5a is identification-only and contains no MCMC.

Before any R5a identification outcome:

1. implement and test the generic state-composition stream;
2. implement the exact R5a fixture;
3. freeze a gate reusing the unchanged R2 thresholds, anchors, and refusal controls;
4. pin the gate blob;
5. run the qualification once.

If R5a fails, label effort or context allocation is not tuned within R5.

If R5a passes, a separate R5b recovery/held-out-transfer gate may be frozen.

## Refusal controls

R5a preserves the frozen R2 controls unchanged:

- sparse practical refusal uses the original sparse design without direct state calibration;
- unknown annotated-detection refusal uses the original unknown-detection design without
  direct state calibration.

The new positive stream is therefore not allowed to erase established refusal behavior.

## Interpretation boundary

A PASS would mean only that a prospectively fixed, direct state-composition calibration
stream supplies enough local information for the hard pre-MCMC identification gate in
this semi-synthetic system.

It would not establish posterior recovery, held-out transfer, empirical feasibility,
causality, or universal superiority of direct state calibration.
