# v0.4-R3a Budget-Neutral Qualification Results

Status: **FAIL**

R3a tested whether the frozen R2 state-annotation budget could be redistributed from
18 sites × 24 temporal contexts to 36 sites × 12 temporal contexts while keeping the
total positive StateAnnotatedCount training exposure fixed at 432 context opportunities.

This was an identification-only qualification. No MCMC recovery, posterior coverage,
held-out transfer, or divergence benchmark was run.

## Frozen provenance

- Qualification head: `18eddcbbb2afda65f4bc816dab1bc58ffc227f79`
- Workflow run: `35684689619`
- Artifact ID: `10675814867`
- Artifact name: `v04-r3a-qualification-35684689619`
- GitHub artifact digest:
  `sha256:193a47569b3a2237d32b8abb1bfe6af8c7a6e03a9112a65a8e95f5c92d38e919`
- Independently downloaded ZIP SHA256:
  `193a47569b3a2237d32b8abb1bfe6af8c7a6e03a9112a65a8e95f5c92d38e919`
- Frozen gate commit:
  `aa38b790e094261addd07c301edc24afa110cb4c`
- Frozen gate blob:
  `ed470d4f6166c5107aeda9432ca44a985cb55e72`
- Observed gate blob during qualification:
  `ed470d4f6166c5107aeda9432ca44a985cb55e72`
- Source Git blob SHA1 expected/observed:
  `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`

The frozen gate file was byte-identical at execution.

## Mechanical decision

Eleven of the twelve frozen qualification terms passed.

PASS:

- positive structural identification;
- sparse structural identification;
- sparse practical refusal;
- unknown annotated-detection refusal;
- annotated context count = 432;
- annotated site count = 36;
- annotated temporal-context count = 12;
- calibrated PresenceOnly context count = 432;
- calibrated site count = 18;
- calibrated temporal-context count = 24;
- first-18 R3a spatial prefix equals the frozen R2 calibration sequence.

FAIL:

- **positive practical identification**.

Therefore the frozen mechanical decision is **R3a FAIL**.

## Positive practical failures

All 13 positive targets remained structurally `Identified` at all three anchors.
The practical failure came only from the unchanged target-SD threshold
`target_sd_proxy <= 0.25`.

### Anchor A

One target was weak:

- `sp.state.beta_foraging_eastness`:
  target-SD proxy = **0.2512177434**.

This is only ~0.00122 above the frozen 0.25 threshold, but the threshold was not relaxed.

### Anchor B

One target was weak:

- `sp.activity.activity_beta_season`:
  target-SD proxy = **0.2561568315**.

### Anchor C

Four state targets were weak:

- `sp.state.beta_foraging_precip`: **0.2901969985**
- `sp.state.beta_foraging_eastness`: **0.3448844366**
- `sp.state.beta_foraging_season`: **0.2549179529**
- `sp.state.beta_foraging_hour`: **0.3034392649**

At Anchor C the global practical diagnostic was otherwise well conditioned:

- relative minimum singular value = **0.0599314651**
- condition number = **16.6857259**

Thus the failure is not structural rank loss or a near-singular global design. It is
target-specific practical precision under the frozen Fisher-like SD criterion.

## Refusal controls

The sparse profile behaved as required at every anchor:

- all 13 targets remained structurally identified;
- at least one target was practically weak at every sparse anchor.

The unknown annotated-detection control also behaved as required at all three anchors:

- `sp.activity.activity_intercept` = `NotIdentified`;
- `stream.annotated.detection_intercept` = `NotIdentified`.

## Frozen budget and selected temporal contexts

Positive StateAnnotatedCount training exposure:

- 36 sites;
- 12 temporal contexts;
- 432 exposed state-annotation contexts total.

Calibrated PresenceOnly remained:

- 18 sites;
- all 24 temporal contexts;
- 432 calibrated contexts total.

The selected R3a temporal contexts, in frozen order, were:

1. (15, 0)
2. (195, 12)
3. (15, 12)
4. (195, 0)
5. (315, 6)
6. (315, 18)
7. (75, 6)
8. (75, 18)
9. (195, 6)
10. (195, 18)
11. (315, 0)
12. (315, 12)

The first 18 selected spatial sites were exactly the frozen R2 calibration sequence.

## Interpretation

The budget-neutral 36 × 12 redistribution improved the information geometry enough that
all targets remained structurally identifiable and most positive practical targets passed,
but it did **not** make all 13 targets practically non-weak under the unchanged R2
thresholds.

The negative result therefore rejects the specific prospective hypothesis that this
36-site × 12-time maximin redistribution is sufficient, at the same total annotation
budget, to qualify the v0.4 state/activity model for a full R3b outcome gate.

This does not show that allocation is irrelevant. It shows that this particular
response-independent 36 × 12 allocation is insufficient under the frozen hard criterion.

## Claim boundary

R3a is an identification-only semi-synthetic design qualification.

This result does not establish:

- v0.4 promotion;
- posterior parameter recovery;
- held-out transfer;
- empirical biological validity;
- universal optimality or failure of fixed-budget reallocation.

Because R3a is **FAIL**, **R3b is not created**.

Any further observation-design hypothesis must be a new gate version with a new
prospective freeze. R3a thresholds, selectors, anchors, or budget are not retuned.
