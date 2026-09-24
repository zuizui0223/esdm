# v0.5 Promotion Decision

Status: **PROMOTED WITH A BOUNDED INTERACTION-EVIDENCE CLAIM**

Authoritative endpoint: frozen v0.5e PASS, interpreted together with the frozen v0.5b
hidden-common-driver FAIL.

## Why promotion includes a failure

v0.5 is not promoted because every interaction coefficient is robust.

The opposite was observed prospectively.

v0.5b showed that an omitted common driver can generate:

- true `beta_partner = 0`;
- mean fitted beta about **+0.985**;
- nonzero 90% intervals in **16/16** replicates;
- Full > partner-knockout held-out prediction in **16/16** replicates.

This establishes that a predictive partner coefficient can be badly mechanistically
wrong while remaining strongly useful for prediction.

The v0.5 promotion therefore requires the architecture to **contain that failure** rather
than pretending to eliminate it.

## Evidence chain

### v0.5 core

`PartnerIntensityEffect` introduced directed dependence through a source species latent
ecological field rather than raw source observations.

The species dependency DAG is evaluated in topological order and reciprocal cycles remain
unsupported/fail-closed.

### v0.5a PASS

Frozen known-truth programme:

- true interaction world: `beta_partner=+0.75`;
- measured-shared-environment null: `beta_partner=0`.

Results:

- positive mean beta bias = **+0.00200**;
- positive 90% coverage = **1.00**;
- positive interval rate = **16/16**;
- positive held-out Full > knockout = **16/16**;
- null mean beta = **+0.00138**;
- null zero coverage = **0.75**;
- null nonzero interval rate = **4/16**;
- 64 fits, **0 divergences**.

Thus measured common environmental response did not reproduce the true directed signal.

### v0.5b FAIL

Frozen omitted-common-driver stress:

- true `beta_partner=0`;
- hidden source/focal driver omitted from fitting model.

Results:

- mean fitted beta = **+0.98541**;
- zero coverage = **0/16**;
- nonzero interval rate = **16/16**;
- Full > knockout = **16/16**;
- mean held-out gain = **+4.39472**;
- 32 fits, **0 divergences**.

Thus predictive gain does not identify interaction mechanism.

### v0.5c claim guard

Model-only interaction evidence is hard-capped at:

`PREDICTIVE_DEPENDENCE`.

Promotion rules are:

- model dependence -> at most PREDICTIVE_DEPENDENCE;
- independently authorized positive pair event -> REALIZED;
- realized event + independent functional endpoint -> FUNCTIONAL;
- realized + functional + intervention evidence -> CAUSAL.

### v0.5d pair-event likelihood

`PairEventCount` provides a generative pair-specific event-count likelihood using:

- source latent availability;
- target latent availability;
- explicit observation effort;
- pair-specific event-rate parameter.

Event occurrence is not equated with a functional effect.

### v0.5e PASS

Three prospectively frozen worlds separated the evidence states.

#### hidden_event_silent

- true beta = 0 with hidden common driver;
- fitted beta remained strongly false-positive:
  mean bias **+0.95255**, positive interval rate **16/16**;
- positive pair events = **0/16**;
- PREDICTIVE_DEPENDENCE authorization = **16/16**;
- REALIZED = **0/16**.

Thus inference can be wrong while claim authorization remains bounded.

#### realized_only

- true beta = 0;
- positive pair event = **16/16**;
- REALIZED authorization = **16/16**;
- beta mean bias = **+0.05754**;
- beta coverage = **0.875**;
- nonzero beta interval rate = **2/16**.

Thus realized pair interaction does not require a nonzero focal partner-effect coefficient.

#### directed_realized

- true beta = +0.75;
- beta mean bias = **+0.02743**;
- beta coverage = **0.9375**;
- beta positive interval = **16/16**;
- positive pair event = **16/16**;
- REALIZED authorization = **16/16**.

Across all 48 v0.5e fits:

- FUNCTIONAL-or-higher self-promotion = **0/48**;
- divergences = **0**.

## Promoted v0.5 contract

v0.5 may now serve as the stable base for later development under the following
interpretation:

1. partner latent fields may contribute directed predictive ecological dependence;
2. such dependence can be identified/recovered in declared known-truth worlds;
3. hidden common drivers can invalidate mechanistic interpretation of the coefficient;
4. predictive gain does not repair that ambiguity;
5. independently authorized pair events are a separate evidence channel for REALIZED;
6. REALIZED does not imply FUNCTIONAL;
7. FUNCTIONAL does not imply CAUSAL;
8. higher evidence tiers require their own endpoints.

## Strongest supported methodological claim

> Predictive dependence, realized interaction, functional consequence, and causal
> interaction are different inferential objects. A process-based ecological model should
> preserve those distinctions even when a lower-level statistical signal is strong,
> recoverable, or predictively useful.

## Promotion boundary

This promotion supports:

- a directed partner-latent predictive process;
- a generative pair-event observation stream;
- bounded promotion from model dependence to realized-event evidence;
- fail-closed prevention of functional/causal self-promotion;
- known-truth evidence-tier separation under the frozen programme.

It does **not** support:

- causal interpretation of `beta_partner` from presence-only data;
- hidden-confounder robustness of the coefficient;
- functional effect from event occurrence alone;
- causal claims without intervention;
- reciprocal/fixed-point interactions;
- empirical validity in a specific field system.

The next version-level process is movement/accessibility (v0.6). A future interaction
extension may add an independent functional endpoint, but v0.5 should not be retuned to
erase its hidden-driver failure.
