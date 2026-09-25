# v0.7c Matched Static-versus-Dynamic Occupancy Results

Status: **PASS**

v0.7c asked whether the late-time predictive advantage seen in v0.7b came merely from
including an occupancy layer, or whether the recursive colonization/extinction
representation itself added information beyond a simpler memoryless occupancy trend.

## Frozen provenance

- gate freeze commit:
  `42772573e83b85174cfad8dc5d9ba5bcd77655af`
- gate blob:
  `95c6e8b7d77a7164574e7afd013dc47fbfbdcb4a`
- authorized outcome run: `36078426459`
- outcome head:
  `08a3fca65cb4fcb3ba1cdd135d92e7bde9513775`
- qualification artifact ID: `10841151051`
- qualification artifact SHA256:
  `6e85671b476a703a4f431011e4eaa10b7a95e52550f03e7ac51fd7c00ef52617`
- final result artifact ID: `10841011706`
- final artifact SHA256:
  `470e3e3ce22f0a9b28791d539a1f09280b55c99de3fce12124fe60e1816e022c`

Independent ZIP hashes matched the GitHub artifact digests.

The authorization marker was consumed immediately after the unique authorized run had
started. Later dedicated-workflow attempts were therefore not eligible to produce a
scientific result.

## Frozen matched design

Both fitted models used the same generated realization and the same observation programme:

- joint occurrence generated at contexts **1-12**;
- joint occurrence exposed for fitting at contexts **1-8**;
- direct OccupancyCount exposed at contexts **1-4**;
- joint occurrence scored at contexts **9-12**;
- direct occupancy exposure in all held-out contexts = **zero**.

The generator was exactly the frozen v0.7b colonization/extinction world.

### Dynamic candidate

Four ecological parameters:

- suitability intercept;
- initial occupancy;
- colonization;
- extinction.

Occupancy at a context depends recursively on previous occupancy.

### Static comparator

Three ecological parameters:

- suitability intercept;
- occupancy intercept;
- linear time slope.

The static model uses a frozen time covariate from -1 to +1 and evaluates occupancy at
each context independently. It has **fewer free parameters** than the dynamic candidate.

## Qualification

Both models passed the prospectively frozen exact-JAX structural and practical gates.

For the static comparator:

- exact-JAX rank = **3 / 3 free parameters**;
- rank without each target = **2**;
- condition number = **6.8934**;
- relative minimum singular value = **0.14507**.

Static target-SD proxies:

- suitability intercept = **0.06673**;
- occupancy intercept = **0.11366**;
- time slope = **0.11195**.

All were well below the frozen 0.25 practical threshold.

Thus the static comparator was not losing because it was unidentified or practically
unstable.

## Replicated held-out comparison

Across **16 fresh paired replicates / 32 fits**:

- Dynamic > Static: **15/16 = 0.9375**;
- frozen requirement: **>= 14/16 = 0.875**;
- mean Dynamic-minus-Static held-out gain:
  **+3.32124 nats/context**;
- frozen requirement: **>= +0.50 nats/context**;
- minimum replicate gain:
  **-0.11684 nats/context**;
- total divergences: **0**.

One replicate weakly favored the static model, so v0.7c does not support per-replicate
dominance. The replicated rate and mean-gain criteria both passed.

## Interpretation

v0.7a showed that a time series can remain underidentified when ecological intensity and
occupancy scale are confounded.

v0.7b showed that a small amount of direct occupancy calibration can anchor that missing
scale, recover the declared marginal colonization/extinction parameters, and improve later
prediction relative to removing occupancy entirely.

v0.7c now closes the main alternative explanation in that sequence:

> Under the frozen dynamic world and exactly the same observation programme, a recursive
> colonization/extinction occupancy representation predicted later joint occurrence
> substantially better than a simpler, fully estimable memoryless linear occupancy trend.

The gain therefore cannot be attributed merely to adding an occupancy layer or to the
static comparator being unidentified.

The ecological interpretation remains bounded: **temporal dependence in occupancy can
carry predictive information that a static occupancy trend cannot preserve**, when the
data-generating process truly has the declared recursive dynamics.

## Claim boundary

v0.7c supports a semi-synthetic **dynamic-resolution value** result.

It does not establish:

- universal superiority of dynamic occupancy models;
- realized binary occupancy histories;
- directly observed colonization or extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.

An empirical application would still need process-appropriate repeated observations and
external validation before translating this result into a biological mechanism claim.
