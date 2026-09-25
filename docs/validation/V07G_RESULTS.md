# v0.7g Budget-Matched Calibration-Placement Results

Status: **PASS**

v0.7g asked whether the same direct-occupancy field effort can yield substantially more
information about marginal colonization/extinction dynamics simply by changing **when**
calibration is collected.

## Frozen design selection

Before any MCMC outcome, all **70 = choose(8,4)** four-context placements inside the
training window were evaluated with the exact-JAX/Fisher-like design diagnostic.

Every design used:

- 4 direct OccupancyCount contexts;
- effort 500 per direct context;
- total direct effort = **2000**;
- joint occurrence at contexts 1-8;
- held-out joint scoring at contexts 9-12;
- zero direct occupancy exposure in held-out contexts.

The frozen minimax objective selected:

- optimized = **(2,6,7,8)**
- early baseline = **(1,2,3,4)**

Deterministic worst dynamic SD proxy:

- optimized = **0.158831**
- baseline = **0.232454**
- ratio = **0.68328**

The deterministic stage therefore predicted roughly a **31.7%** reduction in the worst
dynamic-parameter uncertainty at identical field effort.

## Frozen provenance

- selection run: `36105062429`
- selection artifact ID: `10850198439`
- selection artifact SHA256:
  `45d19db95b45f03c0144a9e11e5636edd3387ff1c8e393eaefbbe0478356eae5`
- gate freeze commit:
  `5efbb6a34ab202c702d1206de325d3781185204a`
- gate blob:
  `a37866fb2bd368515f697aa5dbd3f3fb9da04ca8`
- authorized MCMC run: `36105638747`
- outcome head:
  `c033585d0a4fe958675d7c9f838be1532551785f`
- final result artifact ID: `10851250653`
- final artifact SHA256:
  `d3e736de84b62b399f3b61e1b22755069b0236e99616acf4680ae6dbcdb78bbf`

The independently computed ZIP SHA256 matched the GitHub artifact digest.

## Confirmatory precision result

Across **16 fresh paired replicates / 32 fits**:

- optimized worst dynamic posterior SD < baseline: **16/16 = 1.00**
- frozen requirement: **>=12/16 = 0.75**
- mean optimized/baseline worst-SD ratio: **0.67795**
- frozen requirement: **<=0.85**
- minimum ratio: **0.55032**
- maximum ratio: **0.81495**
- total divergences: **0**

Thus every replicate reproduced the precision advantage, and the observed mean reduction
(**32.2%**) closely matched the deterministic design-stage prediction (**31.7%**).

## Optimized-design recovery guardrail

Mean posterior bias:

- alpha = **-0.00091**
- initial occupancy logit = **+0.04583**
- colonization logit = **-0.02672**
- extinction logit = **-0.05925**

Empirical 90% coverage:

- alpha = **0.8750**
- initial occupancy = **0.8125**
- colonization = **0.9375**
- extinction = **0.8750**

All frozen recovery checks passed.

## Descriptive held-out prediction

Prediction was deliberately not a promotion criterion.

On held-out joint occurrence at contexts 9-12:

- optimized > baseline: **9/16 = 0.5625**
- mean optimized-minus-baseline gain: **+0.01939 nats/context**
- minimum replicate gain: **-0.23815**

The two designs therefore had broadly similar held-out predictive performance despite a
large difference in process-parameter precision.

## Interpretation

v0.7g adds an observation-design result to the eSDM programme:

> At the same number of direct occupancy calibration visits and the same total field-effort
> budget, moving calibration effort from an early-only cluster to a design with one early
> and three late-training measurements reduced the worst posterior uncertainty in the
> dynamic parameters by about one third.

The result also sharpens a broader distinction:

> Similar predictive performance does **not** imply similar information about the
> underlying ecological process.

Here the optimized and baseline designs predicted later occurrence similarly, but the
optimized design recovered the dynamic decomposition much more precisely.

## Boundary

This does not establish:

- universal optimality of contexts (2,6,7,8);
- optimality under different truths, survey costs, detection models, or time horizons;
- equality of expected direct record counts across placements;
- universal predictive superiority of the optimized design;
- realized colonization/extinction events;
- movement kernels or connectivity;
- empirical biological validity.
