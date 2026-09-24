# v0.5c Event-Gated Claim Firewall Gate

Status: **FROZEN BEFORE v0.5c OUTCOME**

v0.5c validates an evidence-tier firewall after the frozen hidden-common-driver failure.

The purpose is **not** to force the distributional partner coefficient back to zero under
hidden confounding. The purpose is to require an independent direct-event endpoint before
a distributional signal can be promoted from PREDICTIVE_DEPENDENCE to REALIZED.

## Frozen prerequisite

The event-endpoint core is the already tested implementation at:

`0d6821608779304abf0ea79a1485214af2f5f615`.

The endpoint is `InteractionEventCount`.

For source j and focal i in context c:

`lambda_event[c]
 = exp(source_log_intensity[c])
 × exp(focal_log_intensity[c])
 × P(event | opportunity)
 × effort[c]
 × detection`.

The event probability uses its own stream parameter:

`stream.interaction_events.event_logit`.

It is distinct from:

`focal.partner_effect.beta_partner`.

## Frozen claim firewall

For each fitted replicate:

Distributional support:

`beta_supported = lower 90% posterior bound(beta_partner) > 0`.

Event support:

`event_supported = lower 90% posterior bound(P(event)) > 0.05`.

The runtime claim policy is frozen as:

- beta supported, event unsupported -> **PREDICTIVE_DEPENDENCE**;
- event supported -> may reach **REALIZED**;
- no causal-design flag is supplied in v0.5c;
- v0.5c therefore cannot produce CAUSAL evidence.

A positive beta by itself may never produce REALIZED evidence.

## Frozen worlds

### Interaction + event world

Ecological generating model:

- exact v0.5a measured-environment interaction world;
- true `beta_partner = +0.75`;
- no hidden common driver.

Interaction-event endpoint:

- true event probability = **0.25**;
- event effort = **0.5** on every training context;
- event effort = **0** on held-out contexts;
- event detection = **0.9**.

### Hidden-common-driver null

Ecological generating model:

- exact earlier frozen v0.5b hidden-common-driver world used by PR #21;
- true `beta_partner = 0.0`;
- omitted hidden driver shared by source and focal;
- fitting model does not observe that hidden driver.

Interaction-event endpoint:

- true event probability = **0.005**;
- event effort = **0.5** on every training context;
- event effort = **0** on held-out contexts;
- event detection = **0.9**.

The hidden-null fitted beta is allowed to remain falsely positive. The gate asks whether
the independent event endpoint prevents that false distributional signal from crossing
the REALIZED evidence boundary.

## Frozen geometry

Both worlds inherit:

- 36 spatial contexts;
- first 24 contexts as training;
- final 12 contexts as held out;
- one day/hour context;
- source and focal PresenceOnly streams from their source programme.

The event stream is **training-only**. v0.5c evaluates event evidence itself, not event
transfer to held-out contexts.

## Frozen execution profile

- replicates per world = **16**;
- worlds = **2**;
- one joint full fit per replicate;
- total fits = **32**;
- credible mass = **0.90**;
- warmup = **300**;
- posterior samples = **350**;
- chains = **2**;
- target accept probability = **0.90**.

Fresh seed family:

- base seed = **20261009**;
- seed stride = **83**;
- hidden-null offset = **1000000**;
- interaction-event replicate r seed = `20261009 + 83*r`;
- hidden-driver-null replicate r seed = `20261009 + 1000000 + 83*r`;
- fit seed = generated-data seed + 1.

No scientific or MCMC control above is configurable from the command line.

## Frozen true-world criteria

All must hold in the interaction-event world:

- replicates = 16;
- beta-supported rate >= **0.75**;
- event-supported rate >= **0.75**;
- REALIZED claim rate >= **0.75**;
- abs(mean event-probability bias) <= **0.08**;
- 90% event-probability coverage >= **0.75**.

## Frozen hidden-null firewall criteria

All must hold in the hidden-common-driver null:

- replicates = 16;
- event-supported rate <= **0.25**;
- REALIZED claim rate <= **0.25**;
- mean fitted event probability <= **0.05**.

There is deliberately **no hidden-null beta-refusal criterion** in v0.5c.
The prior frozen hidden-driver tests already showed that beta can be badly confounded.
The independent endpoint must stop claim-tier promotion even if beta remains positive.

## Frozen divergence criterion

Across all 32 fits:

- total divergences / 32 <= **0.10**.

## Mechanical v0.5c decision

v0.5c = PASS only if:

1. both worlds contain exactly 16 replicates;
2. total fit count = 32;
3. every true-world event/beta/REALIZED criterion passes;
4. every hidden-null event/REALIZED firewall criterion passes;
5. the divergence criterion passes.

No failed criterion can be repaired inside v0.5c by changing:

- event-support threshold;
- event probabilities;
- event effort or detection;
- hidden-driver world;
- beta-support rule;
- evidence-tier policy;
- seed family;
- MCMC profile;
- gate thresholds.

## Interpretation boundary

PASS may support:

> An independent interaction-event endpoint can keep a hidden-driver-induced
> distributional false positive below the REALIZED evidence tier while permitting a
> genuine interaction-event world to reach REALIZED evidence.

PASS would **not** establish causal interaction.

Directly observed events are a REALIZED endpoint. Functional effects and causal claims
still require independent outcome/intervention evidence.
