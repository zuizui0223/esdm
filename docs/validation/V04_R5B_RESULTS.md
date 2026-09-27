# v0.4-R5b Recovery and Held-Out Transfer Results

Status: **PASS**

R5b is the full replicated outcome test of the exact R5a-qualified observation contract.
No scientific threshold, observation geometry, direct-label effort, truth coefficient,
random profile, or MCMC profile was changed after the R5b gate was frozen.

## Frozen provenance

- outcome run: `35879936964`
- outcome head: `3c757ccf243c9bab415d59f40d4ab39ae2a06a69`
- gate freeze commit: `98c828797e73d6b40cf9a73651662d7877473bbc`
- frozen gate blob: `227938d2b104d6e900dbbc7ca9d82d019db9f526`
- observed gate blob: `227938d2b104d6e900dbbc7ca9d82d019db9f526`
- final artifact ID: `10761956596`
- artifact name: `v04-r5b-outcome-35879936964`
- GitHub artifact digest:
  `sha256:ead0e17a4da17b3c27b84bcbb0c4aa034379f9930ce32987e1940215ba839477`
- independently downloaded ZIP SHA256:
  `ead0e17a4da17b3c27b84bcbb0c4aa034379f9930ce32987e1940215ba839477`

All 16 replicate jobs and the final aggregation job completed successfully.
The final audit artifact reports `infrastructure_block = null`.

## Mechanical decision

**R5b = PASS. Every frozen qualification and outcome check passed.**

Execution:

- 16 independently generated replicates;
- 3 fits per replicate;
- 48 total fits;
- 300 warmup draws;
- 350 posterior draws;
- 2 chains;
- 90% posterior intervals;
- target accept = 0.90.

The R5a qualification also remained valid at aggregation:

- positive structural identification: PASS;
- positive practical identification: PASS;
- sparse practical refusal: PASS;
- unknown annotated-detection refusal: PASS;
- 432 existing annotated contexts preserved;
- 432 direct state-calibration contexts preserved;
- expected direct labels = 432.0;
- held-out direct-calibration contexts = 0.

## Parameter recovery

All 13 frozen recovery targets passed both:

- absolute mean bias <= 0.18;
- empirical 90% interval coverage >= 0.75.

The largest absolute mean bias was the opportunistic detection intercept:

- |bias| = **0.12227**, below the frozen 0.18 limit.

The lowest coverage was:

- state eastness = **0.8125**, above the frozen 0.75 limit.

State-process recovery was:

| target | mean bias | coverage |
|---|---:|---:|
| state precip | 0.01515 | 0.8750 |
| state eastness | 0.08024 | 0.8125 |
| state season | 0.03480 | 0.8750 |
| state hour | 0.00225 | 0.9375 |

Activity-process recovery was:

| target | mean bias | coverage |
|---|---:|---:|
| activity precip | 0.04262 | 0.8750 |
| activity eastness | 0.03775 | 0.9375 |
| activity season | 0.04804 | 0.9375 |
| activity hour | 0.02854 | 0.8750 |

## East-heldout transfer

Direct state-composition calibration had **zero east-heldout exposure**. The transfer
scores therefore come only from the original held-out StateAnnotatedCount observations.

### Activity process

Full model beat the activity knockout in:

- **16 / 16 replicates = 1.00**.

Frozen requirement: >= 0.75.

Mean full-minus-activity-knockout log-score gain:

- **0.006999**.

Frozen requirement: >= 0.005.

Even the smallest replicate-level activity gain remained positive:

- **0.000354**.

### State process

Full model beat the state knockout in:

- **16 / 16 replicates = 1.00**.

Frozen requirement: >= 0.75.

Mean full-minus-state-knockout log-score gain:

- **0.028965**.

Frozen requirement: >= 0.005.

The smallest replicate-level state gain was still:

- **0.017969**.

Thus state environmental structure contributed a substantially larger held-out gain than
activity structure under this frozen benchmark, while both contributions were positive
in every replicate.

## Sampling diagnostics

Total divergences across 48 fits:

- **0**.

Mean divergences per fit:

- **0.0** versus frozen maximum 0.10.

## Interpretation across R2-R5

The frozen development sequence separates two distinct problems.

1. **Observation placement matters, but has limits.**
   R3a and R4a changed how the same 432 abundance/activity-weighted state observations
   were arranged. R4a repaired moderate Anchor-A/B failures, but hard Anchor-C state
   precision remained insufficient.

2. **Observation type was the decisive intervention.**
   R5a added direct conditional state-composition information without supplying it in the
   east held-out region. This made every hard identification target practically estimable.

3. **The improvement survives full inference and transfer.**
   R5b recovered all 13 parameters within the frozen bias/coverage criteria and retained
   positive east-heldout information from both activity and state processes in every
   replicate.

The strongest supported methodological statement is therefore:

> In a latent ecological state/activity model, rearranging abundance-weighted records
> alone may not resolve weak state information. A small, process-targeted calibration
> channel can make the latent state process estimable, recoverable, and predictively
> useful under spatial extrapolation.

This is stronger than “more data help”: the **information type** matters.

## Claim boundary

R5b is a semi-synthetic known-truth validation.

It supports:

- parameter recovery under the frozen generating model;
- calibrated interval coverage under the frozen replicate programme;
- positive east-heldout predictive information from activity slopes;
- positive east-heldout predictive information from state slopes.

It does **not** establish:

- empirical biological validity;
- causal correctness in field data;
- universal superiority over SDM/JSDM/network alternatives;
- field cost-effectiveness of direct state calibration.

The next decisive test should therefore be a **matched-model comparison**, not another
internal ESDM validation layer.
