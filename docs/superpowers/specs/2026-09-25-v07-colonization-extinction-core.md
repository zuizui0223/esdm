# v0.7 marginal colonization-extinction occupancy core

Status: **CORE IMPLEMENTATION ONLY — NOT VALIDATED OR PROMOTED**

Date: 2026-09-25

## Purpose

v0.6 separates potential ecological intensity from a static accessibility probability.
v0.7 starts a distinct dynamic layer so repeated occupancy limitation is not relabelled as
static accessibility.

The core target is deliberately narrow: a marginal two-state colonization/extinction
recursion over the existing discrete `space × doy × hour` domain.

## Latent process

For each spatial unit, declared contexts are ordered chronologically by `(doy, hour)`.

The first context has

```text
psi_0 = logistic(initial_logit)
```

and each later declared context applies one transition

```text
psi_t
  = psi_(t-1) × (1 - epsilon_t)
  + (1 - psi_(t-1)) × gamma_t
```

with

```text
gamma_t   = logistic(alpha_gamma   + X_gamma,t beta_gamma)
epsilon_t = logistic(alpha_epsilon + X_epsilon,t beta_epsilon)
```

The process emits the semantic latent channel `occupancy`.

Its knockout is explicit:

```text
occupancy = 1
```

so removing the dynamic layer means no occupancy limitation rather than deleting a term
by convention.

## Observation contract

`OccupiedPresenceOnly` is a Poisson stream with

```text
lambda_record
  = exp(log_intensity)
  × occupancy
  × effort
  × detection
```

It is intentionally separate from both:

- `PresenceOnly`, which remains intensity-only; and
- `AccessiblePresenceOnly`, which remains intensity × static accessibility.

## Time semantics

This first core uses **one transition per adjacent declared sampling context**.

Therefore:

- a gap from day 1 to day 2 and a gap from day 1 to day 20 each represent one transition
  in the current core;
- no continuous-time hazard or elapsed-time scaling is implied;
- each spatial unit starts independently from the same declared initial occupancy model;
- no migration among spatial units is represented;
- no year-wrap semantics are added beyond the chronological ordering of the contexts
  explicitly present in the grid.

These restrictions are part of the model contract, not implementation accidents.

## Marginal-state boundary

`psi_t` is a **marginal occupancy probability**. The v0.7 core does not sample or infer a
realized binary latent occupancy history `z_t`.

Consequently this core does not yet establish:

- realized colonization or extinction events;
- movement paths or dispersal kernels;
- resistance or path connectivity;
- source-sink dynamics;
- metapopulation rescue effects;
- causal movement limitation.

The new process is also not a standard repeated-detection occupancy survey model. The
current observation endpoint remains Poisson record intensity conditioned on marginal
occupancy.

## Required core tests

The implementation must verify:

1. the exact two-state recursion under known transition probabilities;
2. chronological evaluation even when the grid declaration order is non-chronological;
3. independent trajectory initialization across spatial units;
4. explicit occupancy knockout to one;
5. multiplication of record intensity by marginal occupancy;
6. fail-closed design checking when a stream requires occupancy but no occupancy process
   exists;
7. scalar/JAX array agreement.

## Next scientific gate

No identification or biological claim is authorized by this core PR.

The next fresh programme, v0.7a, should freeze a known-truth design before outcomes and
ask whether initial occupancy, colonization, and extinction are structurally and
practically identifiable from declared dynamic evidence. A joint occurrence-only design
must not be assumed sufficient merely because the recursion is executable.

A later gate can compare dynamic transition-specific evidence against additional static or
joint records at a matched information/effort budget, following the v0.6c logic.
