# v0.5c Independent Interaction-Event Endpoint Core

Status: **implementation phase; no v0.5c outcome claim**

Base: frozen v0.5b hidden-driver FAIL at
`6a6052e5f0e87f00539ff09b4419e1a10eca3bae`.

## Motivation

v0.5b established a sharp failure mode:

- true partner coefficient = 0;
- omitted shared environmental driver;
- fitted beta was positive in 16/16 replicates;
- mean beta ≈ 0.627;
- yet the Full interaction model was worse than its knockout on average held out.

Therefore the distributional partner coefficient cannot be treated as realized
interaction evidence.

## New independent endpoint

`InteractionEventCount` observes direct source->target event counts.

For context c:

`lambda_event[c]
 = exp(source_log_intensity[c])
 × exp(target_log_intensity[c])
 × P(event | opportunity)
 × effort[c]
 × detection`.

The event probability has its own `event_logit` parameter. It is not the partner beta.

This separation is deliberate:

- partner beta asks whether source latent ecology improves the focal distribution;
- event_logit asks whether direct realized events occur conditional on latent
  coavailability.

A hidden common driver can corrupt the first while leaving the second unsupported.

## Claim firewall

Runtime claim policy is explicitly bounded:

- distributional partner evidence only -> `PREDICTIVE_DEPENDENCE`;
- independent event endpoint -> may reach `REALIZED`;
- `CAUSAL` additionally requires a separate causal-design flag and cannot skip REALIZED.

No posterior beta threshold alone can produce a REALIZED claim.

## Core contracts

The implementation must ensure:

1. event rates use source and target latent ecological fields, never raw records;
2. source/target context orders must agree;
3. event stream requires a valid source species and source log-intensity channel;
4. scalar and JAX array event rates agree;
5. event probability is a distinct stream parameter;
6. claim promotion cannot skip the event layer.

## Planned validation

A fresh v0.5c gate will compare:

- real interaction + event world:
  `beta_partner = 0.75`, `P(event)=0.25`;
- hidden-common-driver null:
  `beta_partner = 0`, omitted common cause, `P(event)=0.005`.

Frozen event observation profile planned prospectively:

- event effort = 0.5;
- event detection = 0.9;
- event support threshold = `P(event) > 0.05`.

Under the existing latent opportunity geometry this yields approximately:

- 40 expected training events in the real-interaction world;
- 0.65 expected training events in the hidden-driver null.

The validation target is not to force hidden-driver beta back to zero. It is to keep
hidden-driver distributional evidence below the REALIZED tier when the independent event
endpoint is absent.

## Non-claims

This layer does not establish causality. Directly observed events can support REALIZED
interaction evidence, while functional or causal consequences still require stronger
endpoints/designs.
