# v0.7m absolute-adequacy-first calibration policy gate

Status: **FROZEN BEFORE ANY v0.7m CONFIRMATORY MCMC OUTCOME**

Date frozen: 2026-09-26

## Motivation

v0.7l showed that relative placement headroom alone is not a sufficient policy target.
The frozen 0.80 trigger failed, and exhaustive post-outcome auditing showed that no
scalar retuning of that trigger can satisfy the frozen recovery guardrails.

The key separation is now:

1. absolute recovery adequacy: is any four-context direct-occupancy placement
   predicted to reach the already frozen practical precision target?
2. relative placement headroom: only after absolute adequacy is satisfied, is
   local re-optimization materially better than the transferred placement?

## Frozen thresholds

The thresholds are inherited from pre-v0.7l contracts and are not fitted to the
opened v0.7l outcome.

- absolute worst-dynamic-SD threshold = 0.35
- relative adaptive/transferred worst-dynamic-SD ratio threshold = 0.80

The 0.35 threshold is the practical target-SD criterion already used by the
v0.7a/v0.7b identification programme.

## Frozen three-way pilot policy

For each local burned pilot:

1. estimate posterior-mean process parameters;
2. score the locally selected four-context placement and the transferred
   placement (2,6,7,8);
3. let A be the predicted local-best worst dynamic SD;
4. let T be the predicted transferred-placement worst dynamic SD;
5. let R = A / T.

Action:

- if A > 0.35: abstain;
- else if T > 0.35: adaptive;
- else if R <= 0.80: adaptive;
- else: transferred.

Thus a transferred placement can be selected only if it first satisfies the
absolute precision requirement.

Abstain means insufficient calibration evidence under the frozen four-context
budget. It is not a failed fit and it does not authorize a recovery claim.

## Frozen fresh confirmatory roles

All four roles are disjoint from the v0.7l confirmatory worlds and from the
earlier v0.7j/v0.7k confirmatory worlds.

### adaptive_large_headroom

- psi0 = 0.85
- gamma = 0.45
- epsilon = 0.38
- deterministic local placement = (1,2,7,8)
- local-best worst dynamic SD = 0.2472385696777683
- transferred worst dynamic SD = 0.3646050116562837
- local/transferred ratio = 0.6780997566507458
- expected action = adaptive

### adaptive_absolute_rescue

- psi0 = 0.35
- gamma = 0.25
- epsilon = 0.22
- deterministic local placement = (1,2,7,8)
- local-best worst dynamic SD = 0.33916535312516777
- transferred worst dynamic SD = 0.35202920272273763
- local/transferred ratio = 0.9634580043414706
- expected action = adaptive

This role is deliberately important: relative headroom is small, but the
transferred placement lies just outside the pre-existing 0.35 adequacy boundary.

### transfer_adequate

- psi0 = 0.35
- gamma = 0.25
- epsilon = 0.08
- deterministic local placement = (1,3,7,8)
- local-best worst dynamic SD = 0.31342660399042044
- transferred worst dynamic SD = 0.3309299120235847
- local/transferred ratio = 0.9471087157817368
- expected action = transferred

### abstain_inadequate

- psi0 = 0.65
- gamma = 0.45
- epsilon = 0.08
- deterministic local placement = (1,2,3,8)
- local-best worst dynamic SD = 0.42356213088384326
- transferred worst dynamic SD = 0.46239800754752164
- local/transferred ratio = 0.9160120155585075
- expected action = abstain

## Frozen replicate design

For each role:

- independent pilot/confirm pairs = 16
- pilot fit = 1
- confirmatory adaptive fit = 1
- confirmatory transferred fit = 1
- fits per replicate = 3
- total replicates = 64
- total fits = 192

Confirmatory adaptive and transferred fits are always run for audit, including
in abstain worlds. They do not convert abstention into a recovery claim.

MCMC profile:

- warmup = 300
- retained draws = 350
- chains = 2
- central interval mass = 0.90
- target accept = 0.90

Fresh seed families:

- adaptive_large_headroom pilot base = 20320131; confirm base = 20320231
- adaptive_absolute_rescue pilot base = 20330131; confirm base = 20330231
- transfer_adequate pilot base = 20340131; confirm base = 20340231
- abstain_inadequate pilot base = 20350131; confirm base = 20350231
- stride = 197

No scientific or MCMC setting is configurable from the one-shot runner.

## Confirmatory oracle action

For each confirmatory pair, use the posterior SDs from the independent adaptive
and transferred fits to apply the same three-way rule:

- if adaptive worst dynamic SD > 0.35: oracle action = abstain;
- else if transferred worst dynamic SD > 0.35: oracle action = adaptive;
- else if adaptive/transferred ratio <= 0.80: oracle action = adaptive;
- else: oracle action = transferred.

This oracle label is used only to evaluate pilot policy classification.

## Frozen action criteria

World-specific pilot action rate:

- adaptive_large_headroom: adaptive >= 0.75
- adaptive_absolute_rescue: adaptive >= 0.75
- transfer_adequate: transferred >= 0.75
- abstain_inadequate: abstain >= 0.75

World-specific independent confirmatory oracle-action rate must satisfy the same
expected-action thresholds.

Across all 64 pairs:

- pilot action equals confirmatory oracle action in >= 0.75 of pairs;
- abstain sensitivity among confirmatory-oracle abstain pairs >= 0.75;
- non-abstain specificity among confirmatory-oracle non-abstain pairs >= 0.75.

## Frozen recovery criteria

Recovery is evaluated only for policy-deployed non-abstain fits.

For each non-abstain role:

- at least 12 / 16 policy decisions must be non-abstain;
- for every fitted target, absolute mean posterior bias <= 0.20;
- for every fitted target, empirical 90% interval coverage >= 0.75.

The abstain_inadequate role carries no recovery claim. Its confirmatory oracle
abstain rate must instead be >= 0.75.

## Frozen precision and safety criteria

Among non-abstain policy deployments:

- mean policy/transferred worst-SD ratio <= 0.95;
- policy harm rate (ratio > 1) <= 0.10.

Across all 192 fits:

- mean divergences per fit <= 0.10.

Held-out joint-occurrence log scores are retained for description only and are
not a PASS criterion. v0.7m remains an observation-design policy programme, not
an ODSP information-transfer source.

## Mechanical decision

v0.7m = PASS only if every frozen action-classification, safe-abstention,
non-abstain recovery, precision and sampling criterion passes.

No failed criterion may be repaired inside v0.7m by changing:

- the 0.35 absolute threshold
- the 0.80 relative threshold
- selected fresh worlds
- expected role actions
- seed families
- placement selector
- MCMC settings
- recovery thresholds
- action-rate thresholds
- sampling threshold

A material infrastructure bug requires an explicit replacement authorization
that preserves every scientific element above.

## Interpretation boundary

PASS may support:

> A burned pilot can separate when local placement should be adapted, when the
> transferred placement is adequate, and when the fixed calibration budget is
> insufficient for a recovery claim.

PASS does not establish:

- universal optimality of 0.35 or 0.80
- empirical field validity
- movement or connectivity
- realized transition events
- causal biological adaptation
- ODSP information transfer
- EOG consumption or N4 action
