# v0.7b Dynamic Occupancy Recovery and Late-Transfer Results

Status: **PASS**

v0.7b asked whether the marginal colonization/extinction process that passed the v0.7a
identification gate can be recovered in replicated known-truth data and transfer to later
joint occurrence contexts where occupancy itself is not directly observed.

## Frozen provenance

- gate freeze commit:
  `e1f805c6681d33bfc92758b2cdf9d95673353ccc`
- gate blob:
  `b0f721ac334a2e76e0387510f5a889980eaefe53`
- authorized outcome run: `36076155807`
- outcome head:
  `c1622dea9168d1f8ad9a57ed5ecf823fa0953f49`
- qualification artifact ID: `10840113175`
- qualification artifact SHA256:
  `a956b81173d0d4a91b6f4964af340bf45646c7f325e6f6f3350ed095de09473a`
- final result artifact ID: `10839488324`
- final artifact SHA256:
  `ac2f9d51fef951a188de037dcf04c6444531a741d8309cb7ae45383d2428784e`

The independently computed ZIP hashes matched the GitHub artifact digests for both
artifacts.

## Frozen information split

The 12-context trajectory was generated with joint occurrence at all contexts.

The fitting design used:

- joint occurrence at contexts **1-8**;
- direct OccupancyCount at contexts **1-4** only.

The held-out score used joint occurrence at contexts **9-12** only.

There was **zero direct occupancy exposure** in every held-out context.

## Qualification

The joint-only training design retained the exact v0.7a scale ambiguity:

- free parameters = **4**;
- exact-JAX rank = **3**;
- all four targets = **NotIdentified**.

Adding direct occupancy calibration at only the first four contexts restored:

- exact-JAX rank = **4**;
- rank without each target = **3**;
- condition number = **13.06**;
- relative minimum singular value = **0.07656**.

Target-SD proxies:

- suitability intercept alpha = **0.0415**;
- initial occupancy logit = **0.0869**;
- colonization logit = **0.1032**;
- extinction logit = **0.2325**.

All four passed the frozen practical threshold of 0.25.

## Replicated parameter recovery

Across **16 fresh replicates / 32 fits**, all frozen recovery criteria passed.

Mean posterior bias:

- alpha = **-0.00748**;
- initial occupancy logit = **-0.00492**;
- colonization logit = **+0.02782**;
- extinction logit = **+0.01442**.

Empirical 90% interval coverage:

- alpha = **0.9375**;
- initial occupancy logit = **1.0000**;
- colonization logit = **0.8750**;
- extinction logit = **0.8750**.

Total divergences across all 32 fits: **0**.

## Late-time transfer

The full dynamic model and the explicit occupancy knockout were trained on the same
realization. The knockout sets `psi = 1`; it does not receive a different data split.

On held-out joint occurrence at contexts 9-12:

- Full > occupancy knockout: **16/16 = 1.00**;
- frozen requirement: >= 14/16;
- mean Full-minus-knockout log predictive gain:
  **+8.3118 nats/context**;
- frozen requirement: >= +0.50;
- minimum replicate gain:
  **+5.1125 nats/context**.

The late-transfer result therefore did not depend on direct observation of held-out
occupancy.

## Interpretation

The v0.7a and v0.7b results together establish a clear information boundary in the frozen
marginal dynamic model:

> Repeated joint occurrence alone can leave colonization/extinction dynamics
> underidentified even with a time series. A small amount of process-specific occupancy
> calibration can anchor the missing scale, after which the declared dynamic parameters
> are recoverable and their learned trajectory can improve prediction at later times where
> occupancy is not directly measured.

This is stronger than merely showing that a dynamic equation is executable. The same
process that resolves the known-truth parameters also transfers beyond the direct
calibration window.

## Claim boundary

v0.7b supports **marginal dynamic recovery and late predictive transfer** under the frozen
semi-synthetic design.

It does not establish:

- realized binary occupancy histories;
- directly observed colonization or extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.

The current predictive comparison is against the explicit occupancy knockout. A fresh,
matched **static-occupancy versus dynamic-occupancy** benchmark is still needed before
claiming that temporal recursion itself adds information beyond a lower-resolution static
occupancy representation.
