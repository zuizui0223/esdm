# v0.7i Disjoint Burned-Pilot Adaptive Calibration Results

Status: **PASS**

v0.7i asked whether the temporal calibration-placement advantage from v0.7g/v0.7h can
be recovered without using generating truth to choose the schedule.

## Frozen provenance

- gate freeze commit: `aa3ac6917b9e990c6da9f0cf3e5ae7efcb281e4e`
- gate blob: `c6679964dbc62d08ad3dcf925d271f7a6c625353`
- authorized outcome run: `36110445348`
- outcome head: `a02da1065d7699e68c18a13aea324a52cd65b319`
- final result artifact ID: `10852871167`
- final artifact SHA256:
  `78c9b5fb6cb87351c8a7925d505dc5b8a8e96a4337965fbfb96c01961d22b368`

The independently computed ZIP SHA256 matched the GitHub artifact digest.

## Two-stage design

Every replicate used a disjoint two-stage programme.

### Burned pilot

- early-four direct OccupancyCount at contexts 1-4;
- joint occurrence exposed for fitting at contexts 1-8;
- pilot fit only;
- placement selector received the four ecological posterior means;
- all 70 choose(8,4) placements rescored by the frozen minimax dynamic-SD objective.

### Independent confirmation

- independent confirmatory seed family;
- same ecological truth but a fresh generated realization;
- pilot-selected design versus early-four baseline;
- both candidates used four direct contexts at effort 500/context;
- total direct field effort = 2000 for each candidate;
- held-out contexts 9-12 had zero direct occupancy exposure.

Across 16 replicates the programme used **48 fits**:
16 pilot + 16 selected confirmatory + 16 baseline confirmatory.

## Pilot selection result

The plug-in selector chose:

`(2,6,7,8)`

in **16/16 pilots**.

Thus:

- oracle-placement selection rate = **1.00**;
- mean pilot-predicted selected/baseline worst-SD ratio = **0.6870**.

The selector did not receive the generating truth or any confirmatory observations.

## Independent confirmatory precision

Across **16 fresh confirmatory pairs**:

- selected lower worst dynamic posterior SD: **16/16 = 1.00**;
- frozen requirement: **>=12/16 = 0.75**;
- mean selected/baseline worst-SD ratio: **0.66924**;
- frozen requirement: **<=0.90**;
- minimum ratio: **0.46034**;
- maximum ratio: **0.92971**.

The average confirmatory reduction in the worst dynamic posterior SD was therefore about
**33.1%**.

The pilot prediction (ratio 0.6870) closely tracked the independent confirmatory result
(ratio 0.6692).

## Recovery guardrails

Selected-design mean posterior bias:

- alpha: **+0.00254**
- initial occupancy logit: **-0.02472**
- colonization logit: **+0.03508**
- extinction logit: **+0.08237**

Empirical 90% coverage:

- alpha: **0.9375**
- initial occupancy logit: **0.9375**
- colonization logit: **0.8125**
- extinction logit: **0.8750**

All frozen recovery guardrails passed.

Total divergences across all 48 fits: **0**.

## Descriptive prediction

Prediction was deliberately not a promotion endpoint.

- selected > baseline held-out score: **8/16 = 0.50**
- mean selected-minus-baseline held-out gain: **+0.03831 nats/context**
- minimum gain: **-0.13212**

Once again, a large gain in process-parameter precision coexisted with almost no change
in held-out predictive performance.

## Frozen decision

**v0.7i = PASS. All 13 frozen checks passed.**

## Interpretation

The truth-based design result from v0.7g/v0.7h survives a realistic information
constraint:

> A small burned pilot can recover the same late-weighted occupancy-calibration schedule
> and deliver about one-third lower worst-case uncertainty in dynamic parameters on
> independent confirmatory data, without using generating truth to select the schedule.

This supports **pilot-adaptive calibration placement** in the frozen semi-synthetic
programme.

The broader eSDM message is also strengthened:

> predictive equivalence can coexist with substantial differences in information about
> the ecological process.

## Boundary

This does not establish:

- universal optimality of (2,6,7,8);
- robustness when pilot and confirmatory populations differ;
- universal optimality under different truths, costs, detection models, or horizons;
- universal cost efficiency;
- realized colonization/extinction events;
- movement kernels or connectivity;
- empirical biological validity.
