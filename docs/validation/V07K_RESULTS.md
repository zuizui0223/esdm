# v0.7k Incremental Local Adaptation Results

Status: **FAIL**

v0.7k asked whether a local burned pilot can add precision beyond the already broadly
robust transferred calibration schedule from the final v0.7j PASS lineage.

The frozen thresholds were not changed after outcome.

## Provenance

- deterministic local-oracle audit run: `36118088393`
- audit artifact ID: `10855618140`
- audit artifact SHA256:
  `1a3505cda24e32b86f5ef18bfc79a0228786eb9357f718ce5003082b32621150`
- gate freeze commit:
  `0f45d8239f46b12236ef2d567e605e7c4b29949d`
- gate blob:
  `5e8d62c4610202e942935d16dd77664a3937227a`
- authorized outcome run: `36123495515`
- outcome head:
  `5cf6d2b9c66f233e0b24f799939c8d6b0466cedd`
- final result artifact ID: `10859390456`
- final artifact SHA256:
  `387e3618cc657778fdacaf9f95d0c2e806286a9fad1cd93cd1f72dc444a095a9`

Independent ZIP SHA256 matched the GitHub artifact digest.

## Frozen programme

For each of two preregistered stress worlds, every replicate used:

1. a local early-four burned pilot;
2. pilot-posterior means to rescan all 70 four-context placements;
3. a disjoint confirmatory realization;
4. one adaptive confirmatory fit;
5. one fixed transferred-schedule confirmatory fit.

Across both worlds:

- pilot/confirmatory pairs: **32**;
- total fits: **96**;
- total divergences: **0**.

The primary endpoint was worst posterior SD across initial occupancy, colonization, and
extinction logits. Held-out prediction remained descriptive.

## transfer_positive

Truth:

- psi0 = **0.20**;
- gamma = **0.15**;
- epsilon = **0.05**.

The deterministic local oracle predicted only modest headroom relative to the transferred
schedule:

- local oracle: **(1,3,7,8)**;
- local-oracle / transferred SD-proxy ratio: **0.92473**.

Pilot selection:

- oracle placement selected: **11/16 = 0.6875**;
- alternative `(1,3,4,8)`: **5/16**;
- mean pilot-predicted adaptive/transferred ratio: **0.92341**.

Independent confirmatory result:

- adaptive lower worst dynamic SD: **9/16 = 0.5625**;
- frozen requirement: **>=12/16 = 0.75 — FAIL**;
- mean adaptive/transferred ratio: **1.02068**;
- frozen requirement: **<=0.95 — FAIL**;
- minimum ratio: **0.71202**;
- maximum ratio: **1.38734**.

All adaptive recovery bias and 90% coverage guardrails passed.

Descriptive prediction:

- adaptive > transferred: **14/16 = 0.875**;
- mean adaptive-minus-transferred held-out gain: **+0.13458 nats/context**.

So the local pilot often predicted modest parameter-precision headroom, but the
confirmatory precision gain did not survive pilot/confirmation noise.

## reversal

Truth:

- psi0 = **0.80**;
- gamma = **0.15**;
- epsilon = **0.30**.

The deterministic local oracle predicted large headroom:

- local oracle: **(1,2,7,8)**;
- local-oracle / transferred SD-proxy ratio: **0.69437**.

Pilot selection:

- oracle placement selected: **12/16 = 0.75**;
- `(1,2,3,8)`: **2/16**;
- `(1,3,7,8)`: **2/16**;
- mean pilot-predicted adaptive/transferred ratio: **0.70651**.

Independent confirmatory result:

- adaptive lower worst dynamic SD: **16/16 = 1.00**;
- frozen requirement: **>=0.75 — PASS**;
- mean adaptive/transferred ratio: **0.61075**;
- frozen requirement: **<=0.95 — PASS**;
- minimum ratio: **0.32786**;
- maximum ratio: **0.91392**.

All adaptive recovery bias and 90% coverage guardrails passed.

Descriptive prediction:

- adaptive > transferred: **8/16 = 0.50**;
- mean held-out gain: **−0.00649 nats/context**.

Thus local re-optimization was strongly useful when the underlying design headroom was
large, despite almost no predictive-score difference.

## Global decision

Frozen checks passed: **23/25**.

The two failures were both in transfer_positive:

- adaptive win rate below 0.75;
- mean adaptive/transferred ratio above 0.95.

Therefore **v0.7k = FAIL**.

## Interpretation

The result rejects a blanket “always re-pilot after population shift” rule.

Instead it supports a sharper hypothesis:

> local re-optimization has substantial value when the target population creates large
> design headroom, but small predicted headroom can be erased by pilot and confirmatory
> sampling noise.

The reversal world is the clearest demonstration: a local pilot recovered a
population-specific schedule and reduced worst-case dynamic-parameter uncertainty by
about **39%** on independent confirmatory data.

The next fresh programme should therefore test a **selective re-piloting trigger**:
adapt only when the local pilot predicts sufficiently large precision headroom;
otherwise retain the transferred schedule.

## Boundary

This does not establish:

- a validated numerical trigger threshold;
- universal usefulness or uselessness of local re-piloting;
- universal transportability of the transferred schedule;
- empirical field validity;
- realized colonization/extinction events;
- movement kernels or connectivity.
