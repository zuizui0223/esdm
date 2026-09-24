# v0.4-R6 Matched Resolution Benchmark Results

Status: **PASS**

R6 compared the promoted full-resolution v0.4 model against a matched collapsed-resolution
baseline using fresh seeds and identical data within each replicate.

The baseline retained suitability, observation effort/detection, baseline activity, and
baseline state composition. It removed only environmental activity and state slopes.

## Frozen provenance

- outcome run: `35942054740`
- outcome head: `51b98d90d439ecf8c671247c3aea65946412cc08`
- gate freeze commit: `3bae2166fdae6b568a0bb155d795e369445cadf1`
- gate blob expected/observed:
  `d6c15b922895aee40c072a1cab4c92781507c2e5`
- final artifact ID: `10786317524`
- artifact name: `v04-r6-matched-35942054740`
- artifact digest / independently verified ZIP SHA256:
  `81ff97d9bfe0e76e9e0d5547032838b5ec0c8245c88a6901c0f8da3ac877a69c`

All 32 replicate shards and final aggregation completed successfully.
The final artifact reports `infrastructure_block = null`.

## Structured world

When the non-zero environmental activity/state slopes generated the data:

- Full beat Collapsed in **16/16 replicates**;
- positive gain rate = **1.00**;
- material gain rate (`gain > 0.005`) = **1.00**;
- mean resolution gain = **+0.03552**;
- minimum replicate gain = **+0.00896**;
- maximum replicate gain = **+0.04939**.

Thus the Full model passed the frozen requirement with margin.

## Resolution-null world

When all eight environmental activity/state slopes were exactly zero:

- Full beat Collapsed in **0/16 replicates**;
- positive gain rate = **0.00**;
- material gain rate (`gain > 0.005`) = **0.00**;
- mean resolution gain = **−0.00402**;
- maximum replicate gain was still negative: **−0.000782**.

The more complex model therefore did **not** reproduce its structured-world advantage
when the added ecological resolution was absent.

## Sampling

Across 64 fits:

- total divergences = **0**;
- mean divergences per fit = **0.0**.

## Interpretation

R6 closes a major internal comparison gap.

The R5b result alone showed that activity and state environmental slopes can be recovered
and can improve east-heldout prediction relative to process knockouts.

R6 now shows that this predictive advantage is **conditional on the corresponding
ecological structure actually existing**:

- when environmental activity/state gradients are present, higher resolution improves
  held-out state-resolved prediction in every fresh replicate;
- when those gradients are absent, the collapsed representation is better in every fresh
  replicate.

Therefore the result is not explained by a generic tendency of the larger model to win.

The supported comparison claim is:

> Under the declared semi-synthetic worlds and matched observation contract, environmental
> activity/state resolution adds predictive value exactly when that ecological resolution
> is present, and the advantage disappears when it is absent.

## Claim boundary

R6 compares ESDM with a matched collapsed low-resolution representation.

It does **not** establish superiority over every named SDM/JSDM implementation, arbitrary
model misspecification, or real ecological datasets.

A remaining internal question is whether the success of direct state-composition
calibration reflects its **information geometry** rather than simply the addition of more
state labels. That requires a new budget-matched observation-design comparison.
