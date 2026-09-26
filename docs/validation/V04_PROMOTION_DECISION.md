# v0.4 Promotion Decision

Status: **PROMOTED WITHIN THE DECLARED SEMI-SYNTHETIC VALIDATION SCOPE**

Authoritative outcome: v0.4-R5b frozen PASS.

## Evidence chain

The promotion decision is not based on one successful fit.

The frozen sequence was:

1. **R2 FAIL** — the factorized state/activity model was structurally identified but hard
   state slopes lacked practical precision under the initial partial annotation design.
2. **R3a FAIL** — redistributing the same 432 annotated contexts from 18×24 to 36×12 did
   not rescue the hard practical gate.
3. **R4a FAIL** — balanced temporal contrasts repaired moderate A/B weaknesses but hard
   Anchor-C state precision still failed.
4. **R5a PASS** — adding a prospectively frozen direct conditional state-composition
   calibration channel made all 13 frozen targets practically non-weak while preserving
   sparse and unknown-detection refusal controls.
5. **R5b PASS** — the exact R5a-qualified design passed replicated posterior recovery and
   east-heldout transfer.

## R5b authoritative provenance

- outcome run: `35879936964`
- outcome head: `3c757ccf243c9bab415d59f40d4ab39ae2a06a69`
- final frozen-results commit: `871e50a4a71d92264641f40d25a9dcb789cf8d6d`
- gate freeze commit: `98c828797e73d6b40cf9a73651662d7877473bbc`
- gate blob: `227938d2b104d6e900dbbc7ca9d82d019db9f526`
- final artifact ID: `10761956596`
- artifact / independently verified ZIP SHA256:
  `ead0e17a4da17b3c27b84bcbb0c4aa034379f9930ce32987e1940215ba839477`

## Promotion requirements satisfied

### Identification

- all 13 positive targets structurally identified at all three frozen anchors;
- all 13 positive targets practically non-weak;
- sparse practical refusal preserved;
- unknown annotated-detection refusal preserved.

### Recovery

Across 16 independent replicates and 48 total fits:

- every one of the 13 targets had |mean bias| <= 0.18;
- every target had 90% interval coverage >= 0.75;
- maximum absolute mean bias = 0.12227;
- minimum coverage = 0.8125;
- total divergences = 0.

### Spatial transfer

Direct state-composition calibration had zero east-heldout exposure.

Nevertheless:

- full model beat the activity knockout in 16/16 replicates;
- mean activity gain = 0.006999;
- full model beat the state knockout in 16/16 replicates;
- mean state gain = 0.028965.

Thus the promoted state/activity processes retained predictive information under the
frozen east spatial extrapolation.

## Promoted v0.4 contract

The promoted generative/observation contract includes:

- ecological log intensity / availability;
- conditional activity;
- conditional categorical state;
- PresenceOnly with explicit observation effort/detection;
- StateAnnotatedCount;
- StateCompositionCount for direct conditional state calibration;
- shared observation blocks across simulation, likelihood, posterior rates, and
  identification;
- fail-closed structural/practical identification;
- explicit process knockouts;
- bounded refusal when observation design does not separate parameters.

## Scientific interpretation

The frozen R2-R5 sequence supports a specific methodological conclusion:

> Rearranging abundance-weighted state observations can improve information geometry but
> may still leave latent state effects weak. Directly calibrating the conditional state
> composition can make those effects identifiable, recoverable, and predictively useful
> outside the calibration region.

This is an information-contract result, not merely a sample-size result.

## Promotion boundary

This promotion means:

- **yes**: v0.4 is validated for its declared semi-synthetic known-truth benchmark;
- **yes**: the exact state/activity + direct-state-calibration contract is eligible to
  serve as the stable base for v0.5 development;
- **no**: empirical biological validity is not established;
- **no**: causal correctness in field systems is not established;
- **no**: universal superiority over SDM/JSDM/network methods is not established;
- **no**: direct state calibration has not yet been shown field-cost-effective.

The next validation programme should therefore be a matched-model comparison and/or a
fresh empirical system, rather than another internal retuning of v0.4.
