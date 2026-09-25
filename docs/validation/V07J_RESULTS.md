# v0.7j Population-Shift Transportability Results

Status: **FAIL**

v0.7j asked whether the fixed occupancy-calibration schedule selected in v0.7i could be
transported to shifted dynamic populations, and whether a sufficiently strong population
shift would reverse the preferred schedule.

The frozen thresholds were not changed after outcome.

## Provenance

- deterministic surface run: `36111568220`
- surface artifact ID: `10853645888`
- surface artifact SHA256:
  `9166004059c6ee451594d6609b91ed9b40c963e130e6a3a5d62c8043a35eb445`
- gate freeze commit: `41d669b2b3fce602d969bd60b7c469de6e9ebc83`
- gate blob: `7d576aef64fdc16373ec56eb60ba5a5c40bb6666`
- authorized confirmatory run: `36117154435`
- outcome head: `cb91c1f3df498c169e8c820a58f250382c8b2f47`
- final result artifact ID: `10855459150`
- final artifact SHA256:
  `37832f6a825a395ea10c0261af47f4cd7ce6d6bc3ad20f35125bfdaa1529e52b`

Independent ZIP SHA256 matched the GitHub artifact digest.

## Deterministic surface

Across 36 frozen truth cells:

- jointly eligible: **35/36**;
- fixed selected schedule `(2,6,7,8)` better than early-four baseline in **30/35**;
- mean selected/baseline SD-proxy ratio: **0.86468**;
- minimum ratio: **0.58044**;
- maximum ratio: **1.37923**.

This already showed that the fixed schedule was not universally optimal.

## Confirmatory transfer-positive world

Truth:

- psi0 = **0.20**;
- gamma = **0.15**;
- epsilon = **0.05**.

The stress cell was chosen before MCMC as the hardest eligible deterministic case with
predicted selected/baseline ratio <=0.90.

Across **16 fresh paired replicates / 32 fits**:

- selected lower worst dynamic SD: **12/16 = 0.75**;
- frozen rate requirement: **>=0.75** — PASS;
- mean selected/baseline worst-SD ratio: **0.96827**;
- frozen requirement: **<=0.95** — **FAIL**.

Recovery guardrails:

- alpha mean bias: **+0.00112** — PASS;
- psi0-logit mean bias: **−0.02940** — PASS;
- gamma-logit mean bias: **−0.01394** — PASS;
- epsilon-logit mean bias: **−0.34893** — **FAIL** against abs(mean bias) <=0.20;
- all four 90% coverage criteria passed.

Thus the selected schedule retained a weak directional advantage in many replicates, but
the mean precision advantage was too small and extinction recovery was biased beyond the
frozen guardrail.

Descriptive held-out prediction:

- selected > baseline: **7/16 = 0.4375**;
- mean selected-minus-baseline held-out gain: **−0.07422 nats/context**.

## Confirmatory reversal world

Truth:

- psi0 = **0.80**;
- gamma = **0.15**;
- epsilon = **0.30**.

This was the strongest eligible deterministic reversal cell.

Across **16 fresh paired replicates / 32 fits**:

- baseline correctly beat selected in **15/16 = 0.9375**;
- frozen requirement: **>=0.75** — PASS;
- mean selected/baseline worst-SD ratio: **1.58140**;
- frozen reversal requirement: **>=1.10** — PASS;
- all recovery bias and 90% coverage guardrails passed;
- divergences: **0**.

The reversal is therefore a robust result: under this shifted population, the early-four
baseline is substantially more informative than the previously selected late-weighted
schedule.

## Global decision

Across both worlds:

- confirmatory datasets: **32**;
- total fits: **64**;
- total divergences: **0**;
- frozen checks passed: **23/25**.

Therefore **v0.7j = FAIL**.

## Interpretation

The negative result sharpens the observation-design claim:

> A calibration schedule learned from one population is not automatically transportable
> to another population with different occupancy dynamics.

At the same time, the framework successfully identifies a strong reversal region:

> under a sufficiently different dynamic population, the preferred temporal placement can
> reverse, so the appropriate response is re-optimization rather than forcing the original
> schedule to transfer.

The next fresh question is therefore not how to rescue the fixed `(2,6,7,8)` schedule.
It is whether a **local burned pilot in the shifted population** can re-select an
appropriate schedule and recover the precision advantage on independent confirmatory
data.

## Boundary

This does not establish:

- a universal numerical threshold for when re-optimization is required;
- field transportability across real populations;
- universal failure of the selected schedule;
- universal optimality of the early-four baseline;
- realized colonization/extinction events;
- movement kernels or connectivity;
- empirical biological validity.
