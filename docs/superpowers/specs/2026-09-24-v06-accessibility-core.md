# v0.6 Accessibility Core

Status: implementation phase; no v0.6 promotion claim.

Base: promoted v0.5 bounded interaction-evidence core at
`796da648fa007ff8641d3dbe52f20dd2e0cef798`.

## Scientific distinction

v0.6 separates:

- environmental suitability / potential ecological intensity;
- accessibility / ability to reach or remain available at a context.

Low observed occurrence can result from either component. The model must not decompose the
product unless an observation design contains independent accessibility information.

## New latent channel

`LinearAccessibility` contributes `log_accessibility`.

For linear predictor eta:

`accessibility = sigmoid(eta)`

`log_accessibility = log(sigmoid(eta))`.

Multiple accessibility processes combine multiplicatively because their log
probabilities add.

The explicit knockout is:

`log_accessibility = 0`

so accessibility = 1: no accessibility limitation.

A species with no accessibility process also retains accessibility = 1.

## New observation streams

### AccessiblePresenceOnly

`lambda_joint
 = exp(log_intensity)
   * accessibility
   * effort
   * detection`.

This is the joint occurrence endpoint where habitat and accessibility both limit records.

### AccessibilityCount

`lambda_access
 = accessibility
   * effort
   * detection`.

This is a direct calibration endpoint for movement/accessibility information and does not
consume suitability intensity.

The existing PresenceOnly stream remains intensity-only and is not silently changed.

## Identification contract

A joint occurrence stream alone need not separate suitability and accessibility.

The core negative control is an intercept-only suitability process plus intercept-only
accessibility observed only through AccessiblePresenceOnly. Their effects enter through a
single product and the accessibility target must return NotIdentified.

Adding AccessibilityCount supplies an independent channel and should make the accessibility
intercept structurally identifiable.

## Core implementation requirements

- scalar accessibility is strictly in (0,1) for finite parameters;
- accessibility knockout equals 1 exactly;
- AccessiblePresenceOnly uses intensity times accessibility;
- AccessibilityCount is independent of suitability at fixed accessibility;
- legacy PresenceOnly remains accessibility-blind;
- accessibility-aware streams fail closed if the accessibility process is absent;
- scalar and JAX array latent paths carry the new accessibility channel;
- posterior latent-field summaries expose accessibility;
- joint-only intercept design is NotIdentified;
- adding direct accessibility calibration identifies the accessibility intercept.

## Boundary

This core does not yet establish:

- recovery of accessibility gradients;
- spatial transfer;
- movement kernels, dispersal distances, or connectivity;
- dynamic colonization/extinction;
- causal movement limitation.

The next fresh v0.6a programme should freeze a positive recovery design and a joint-only
refusal control before any outcome-producing run.
