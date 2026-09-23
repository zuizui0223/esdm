# v0.4-R4a Phase-Balanced Temporal Qualification Results

Status: **FAIL**

R4a tested a new prospective observation-design hypothesis after the frozen R3a FAIL.
It kept the exact R3a 36-site spatial sequence and the exact positive StateAnnotatedCount
budget of 432 training contexts, but replaced R3a joint cyclic temporal maximin sampling
with a 3-season × 4-hour phase-balanced Cartesian design.

This was an identification-only qualification. No MCMC recovery, posterior coverage,
held-out transfer, or divergence benchmark was run.

## Frozen provenance

- Qualification head: `81f041ad24df8d0b28ea122782a336433a629be7`
- Workflow run: `35837783606`
- Artifact ID: `10740852641`
- Artifact name: `v04-r4a-qualification-35837783606`
- GitHub artifact digest:
  `sha256:69dd110fa2b54fe930282756e1c76c095b7eb0477cb9f9178929703aeab5d34b`
- Independently downloaded ZIP SHA256:
  `69dd110fa2b54fe930282756e1c76c095b7eb0477cb9f9178929703aeab5d34b`
- Frozen gate commit:
  `65115f31425d4d8655137eeea9a0bdb40f56aa53`
- Frozen gate blob:
  `c55af9dfbc6347218fecebb27542ee7bb59310b0`
- Observed gate blob during qualification:
  `c55af9dfbc6347218fecebb27542ee7bb59310b0`
- Source Git blob SHA1 expected/observed:
  `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`

The audit artifact reports `infrastructure_block = null`, so this is a scientific gate
FAIL rather than an infrastructure failure.

## Mechanical decision

Twelve of the thirteen frozen qualification terms passed.

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
- exact R3a 36-site spatial sequence preserved;
- exact R4a 3 × 4 temporal phase balance preserved.

FAIL:

- **positive practical identification**.

Therefore the frozen mechanical decision is **R4a FAIL**.

## What improved relative to R3a

The phase-balanced design removed every practical failure at Anchor A and Anchor B.

R3a had:

- Anchor A: `sp.state.beta_foraging_eastness = 0.2512177434`;
- Anchor B: `sp.activity.activity_beta_season = 0.2561568315`.

Under R4a, all 13 targets were practically non-weak at both A and B.

This is evidence that the temporal allocation mattered: the same 36 × 12 × 432 budget
can change practical precision without changing structural identification.

## Remaining hard-regime failure

Only Anchor C failed, and only the four state slopes were weak:

- `sp.state.beta_foraging_precip`: **0.2761798117**
- `sp.state.beta_foraging_eastness`: **0.3257965541**
- `sp.state.beta_foraging_season`: **0.2967722921**
- `sp.state.beta_foraging_hour`: **0.2738623869**

The global design remained well-conditioned at Anchor C:

- relative minimum singular value = **0.0600135240**
- condition number = **16.6629108**

Thus R4a fails because state-specific practical information remains insufficient in the
hard regime, not because of structural rank loss or global near-singularity.

## Interpretation across R2, R3a, and R4a

The three frozen designs all used 432 positive state-annotation training contexts:

- R2: 18 sites × 24 temporal contexts;
- R3a: 36 sites × 12 joint-maximin temporal contexts;
- R4a: 36 sites × 12 phase-balanced temporal contexts.

R4a shows that allocation is not irrelevant: balancing temporal contrasts repaired the
near-threshold failures that R3a produced at Anchors A and B.

But no fixed-432 allocation tested so far makes all four Anchor-C state slopes practically
non-weak.

The next hypothesis should therefore not be another post-outcome reshuffling of the same
432 context cells. A scientifically distinct next gate should change the information
contract of state observation itself, or prospectively test additional annotation depth.

## Claim boundary

R4a is an identification-only semi-synthetic design qualification.

This result does not establish:

- v0.4 promotion;
- posterior parameter recovery;
- held-out transfer;
- empirical biological validity;
- universal failure of all fixed-budget designs;
- universal superiority or inferiority of factorial temporal sampling.

Because R4a is **FAIL**, **R4b is not created**.
