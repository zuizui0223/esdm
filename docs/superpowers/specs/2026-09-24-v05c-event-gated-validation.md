# v0.5c Event-Gated Claim Validation

Status: **prospective design, pre-outcome**

Base: interaction-event endpoint core at
`0d6821608779304abf0ea79a1485214af2f5f615`.

## Purpose

v0.5b showed that an omitted common driver can make a distributional partner coefficient
strongly positive even when the true directed effect is zero.

v0.5c does **not** require that the event stream repair beta.

Instead it validates the claim firewall:

- distributional beta may support at most PREDICTIVE_DEPENDENCE;
- a separate direct event endpoint is required for REALIZED evidence.

## Fresh worlds

### True interaction + event

- beta_partner = +0.75;
- event probability = 0.25;
- no hidden common driver;
- event effort = 0.5 on the 24 training contexts;
- event detection = 0.9.

### Hidden-driver null

Uses the frozen v0.5b hidden-common-driver generating world:

- beta_partner = 0;
- hidden common driver omitted from the fitting model;
- event probability = 0.005;
- same event effort/detection profile.

The hidden-driver fitting beta is allowed to remain spuriously positive. The scientific
question is whether the independent event endpoint prevents that distributional signal
from becoming a REALIZED claim.

## Event-support rule

Posterior event probability is derived from the distinct stream parameter
`stream.interaction_events.event_logit`.

For each replicate:

`event_supported = lower bound of 90% posterior interval for P(event) > 0.05`.

This rule is frozen before outcome.

Distributional support is:

`beta_supported = lower bound of 90% beta interval > 0`.

The runtime `bounded_interaction_claim` then assigns:

- beta only -> PREDICTIVE_DEPENDENCE;
- event support -> REALIZED;
- no causal flag is supplied.

## Frozen target criteria

True interaction world:

- beta-supported rate >= 0.75;
- event-supported rate >= 0.75;
- REALIZED claim rate >= 0.75;
- abs(mean event-probability bias) <= 0.08;
- event-probability 90% coverage >= 0.75.

Hidden-driver null:

- event-supported rate <= 0.25;
- REALIZED claim rate <= 0.25;
- mean fitted event probability <= 0.05.

No criterion requires hidden-null beta to return to zero.

## Planned execution

- 16 replicates per world;
- 32 total fits;
- fresh seed family to be frozen in the gate;
- 300 warmup;
- 350 posterior samples;
- 2 chains;
- 90% intervals;
- target accept = 0.90.

## Boundary

PASS supports an evidence-tier firewall, not causal identification.

Even directly observed events establish at most REALIZED evidence. Functional effects and
causal claims still require stronger endpoints/designs.
