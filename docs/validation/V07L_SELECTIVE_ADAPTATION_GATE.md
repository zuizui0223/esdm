# v0.7l selective local adaptation gate

Status: **FROZEN BEFORE ANY v0.7l CONFIRMATORY MCMC OUTCOME**

Date frozen: 2026-09-26

## Parent result and motivation

v0.7k rejected blanket local re-piloting after population shift.

- modest predicted headroom world: mean predicted adaptive/transferred ratio 0.92341, independent confirmatory ratio 1.02068, only 9/16 precision wins;
- large predicted headroom world: mean predicted ratio 0.70651, confirmatory ratio 0.61075, 16/16 precision wins.

The next frozen policy is therefore selective:

> re-optimize the direct-occupancy placement only when the local burned pilot
> predicts at least a 20% reduction in worst dynamic posterior SD.

Trigger:

predicted adaptive/transferred worst-SD ratio <= 0.80.

## Frozen deterministic audit

The fresh-world audit was completed before any v0.7l confirmatory MCMC.

- audit merge commit: d17364d6b013a3ea0653c0d3961839c0d9454ae7
- audit workflow run: 36125673492
- audit artifact ID: 10859324317
- audit artifact digest: sha256:af13621c92793b067ac943f9a5ec100fb5ffac5d618d1a34f9afcfdbfa369e36
- audit JSON SHA256: 2c4be7f3e235a000a2db3bac60b9e63ad5f318644c538ec09b0378ffe9ad681a
- eligible fresh cells: 35 / 36

The four confirmatory roles are fixed:

1. strong_headroom
   - psi0 = 0.85
   - gamma = 0.25
   - epsilon = 0.38
   - local oracle placement = (1,2,7,8)
   - deterministic oracle/transferred ratio = 0.6737454617843512

2. threshold_below
   - psi0 = 0.85
   - gamma = 0.25
   - epsilon = 0.22
   - local oracle placement = (1,2,3,8)
   - deterministic oracle/transferred ratio = 0.7450786540043693

3. threshold_above
   - psi0 = 0.85
   - gamma = 0.25
   - epsilon = 0.08
   - local oracle placement = (1,3,4,8)
   - deterministic oracle/transferred ratio = 0.8692745421491

4. negligible_headroom
   - psi0 = 0.85
   - gamma = 0.65
   - epsilon = 0.22
   - local oracle placement = transferred placement (2,6,7,8)
   - deterministic oracle/transferred ratio = 1.0

These worlds are disjoint from the previous v0.7j/v0.7k confirmatory worlds.

## Frozen replicate design

For each world:

- independent replicates = 16;
- each replicate has a local burned pilot and an independent confirmatory dataset;
- the pilot selects its local four-context placement exactly as v0.7k;
- the pilot computes predicted adaptive/transferred worst-dynamic-SD ratio;
- if predicted ratio <= 0.80, policy action = adaptive;
- otherwise policy action = transferred;
- independent confirmation fits both adaptive and transferred placements for audit;
- total fits per replicate = 3;
- total replicates = 64;
- total fits = 192.

Fitting profile:

- warmup = 300;
- retained draws = 350;
- chains = 2;
- central interval mass = 0.90;
- target accept = 0.90.

Fresh seed families:

- strong_headroom pilot base = 20280131; confirm base = 20280231;
- threshold_below pilot base = 20290131; confirm base = 20290231;
- threshold_above pilot base = 20300131; confirm base = 20300231;
- negligible_headroom pilot base = 20310131; confirm base = 20310231;
- stride = 193.

No MCMC or scientific setting is configurable from the one-shot runner.

## Confirmatory headroom label

For each independent confirmatory pair:

actual adaptive/transferred worst-SD ratio
  = adaptive worst dynamic posterior SD
    / transferred worst dynamic posterior SD.

Actual material headroom is defined prospectively as:

actual ratio <= 0.80.

This uses the same 20% threshold as the pilot policy.

## Primary selective-policy criteria

World-specific pilot trigger:

- strong_headroom trigger rate >= 0.75;
- threshold_below trigger rate >= 0.75;
- threshold_above trigger rate <= 0.25;
- negligible_headroom trigger rate <= 0.25.

World-specific confirmatory headroom:

- strong_headroom actual material-headroom rate >= 0.75;
- threshold_below actual material-headroom rate >= 0.75;
- threshold_above actual material-headroom rate <= 0.25;
- negligible_headroom actual material-headroom rate <= 0.25.

Across all 64 pairs:

- trigger sensitivity for actual material headroom >= 0.75;
- trigger specificity >= 0.75;
- balanced accuracy >= 0.75.

## Policy precision criteria

For each replicate:

- policy/transferred ratio = actual ratio if action=adaptive, else 1;
- oracle-threshold ratio = actual ratio if actual ratio<=0.80, else 1;
- policy regret = policy/transferred ratio - oracle-threshold ratio.

Required across all 64 pairs:

- mean policy/transferred ratio <= 0.95;
- policy harm rate, defined as policy/transferred ratio > 1, <= 0.10;
- mean policy regret <= 0.05.

These criteria test whether selective adaptation captures material precision
headroom while avoiding the blanket-repiloting failure seen in v0.7k.

## Recovery guardrails

The parameter estimates from the policy-deployed fit are evaluated in every
fresh world.

For each of the four fitted targets and each world:

- absolute mean posterior bias <= 0.20;
- empirical 90% interval coverage >= 0.75.

Sampling criterion:

- mean divergences per fit across all 192 fits <= 0.10.

## Held-out prediction

Adaptive and transferred held-out joint-occurrence log predictive densities are
retained for description only.

They are not a v0.7l PASS criterion because the programme tests precision-aware
calibration placement, not a new ecological information filtration.

v0.7l is therefore not an ODSP information-transfer source.

## Mechanical decision

v0.7l = PASS only if every frozen trigger-classification, policy-precision,
recovery and sampling criterion above passes.

No failed criterion may be repaired inside v0.7l by changing:

- trigger ratio;
- selected fresh worlds;
- pilot or confirmatory seed family;
- placement selector;
- MCMC settings;
- recovery guardrails;
- headroom label;
- classification thresholds;
- policy regret threshold;
- sampling threshold.

A material infrastructure bug requires an explicit replacement authorization
that preserves every scientific element above.

## Interpretation boundary

PASS may support:

> A burned-pilot headroom trigger can selectively re-optimize direct occupancy
> calibration after population shift, capturing material precision gains while
> avoiding unnecessary blanket re-piloting in fresh known-truth worlds.

PASS does not establish:

- universal optimality of the 0.80 threshold;
- empirical field validity;
- realized transition events;
- movement or connectivity;
- causal biological adaptation;
- ODSP information transfer;
- EOG consumption or N4 action.
