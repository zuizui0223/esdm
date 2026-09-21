# v0.4-R2 hard state/activity separation results

Status: **FAIL at frozen pre-MCMC practical-identification gate**

This record belongs to the frozen R2 gate in
`docs/validation/V04_R2_PROMOTION_GATE.md`.

The result is a methodological semi-synthetic result only. It is not an empirical
biological claim and it does not emit scientific `Supported`.

## Freeze provenance

- gate freeze commit:
  `9e6db6fbe8336c6eb8bbe354713d2863fc40033f`;
- gate blob SHA:
  `92e937a19f89f125f44ecd746e0537cd989dc9cc`;
- outcome decision head:
  `621123e051ef11e6b842bdbd9d5bf4e84cc065f7`;
- R2 workflow run:
  `35549957893`;
- artifact:
  `v04-r2-state-activity-35549957893`;
- artifact ID:
  `10618082465`;
- GitHub artifact digest:
  `sha256:b9af099df6b7526141f0f66427bc86d20a38f66c307da41e87410c684e6cfb0e`.

The downloaded ZIP was independently hashed and produced the same SHA256:
`b9af099df6b7526141f0f66427bc86d20a38f66c307da41e87410c684e6cfb0e`.

## Source integrity and extrapolation

Pinned source:

- repository: `the-pudding/data`;
- source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`;
- path: `rain/annual_precipitation.csv`;
- expected/observed Git blob SHA1:
  `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`;
- source SHA256:
  `088263312c61c875cb5cda7d826ecdb7444ca4a55f7c4a594a1de96c7cf4e705`.

Geometry:

- training spaces: 67;
- held-out east spaces: 53;
- positive calibration spaces: 18;
- total full-domain contexts: 2,880.

The frozen extrapolation check passed:

- maximum training `eastness_z_train`:
  `0.7690432636975336`;
- minimum held-out `eastness_z_train`:
  `0.7831898085656614`;
- therefore held-out east is outside the training eastness range.

## Frozen gate decision

The exact artifact reports:

- `status = FAIL`;
- `decision_stage = pre_mcmc_required_conditions`;
- failed necessary condition:
  `positive_practical_pass`;
- `replicates_executed = 0`;
- `fits_executed = 0`.

The outcome runner intentionally stopped before recovery MCMC because the frozen
conjunction had already failed a necessary condition. Recovery, coverage, held-out
knockout transfer, and divergence criteria are therefore **not evaluated**, rather than
being treated as failed observations.

This short-circuit does not alter the frozen gate: a conjunction cannot pass after one
required term is already false.

## Identification result

The R2 design did pass all structural/refusal checks:

- positive structural identification: **PASS**;
- sparse structural identification: **PASS**;
- sparse practical refusal: **PASS**;
- unknown annotated-detection refusal: **PASS**;
- positive practical identification: **FAIL**.

The sparse profile classified 11, 10, and 11 of the 13 targets as practically weak at
anchors A, B, and C respectively, satisfying the frozen refusal criterion.

The unknown-detection profile returned both
`sp.activity.activity_intercept` and
`stream.annotated.detection_intercept` as `NotIdentified` at all three frozen
anchors.

## Positive-profile practical diagnostics

The positive profile was structurally well-conditioned at every anchor. The failure was
not a rank defect or near-singular Jacobian.

### Anchor A

- relative minimum singular value: `0.059293`;
- condition number: `16.865`;
- all 13 target SD proxies were below `0.25`;
- largest state SD proxy:
  `sp.state.beta_foraging_eastness = 0.234981`.

Result: **all 13 targets non-weak**.

### Anchor B

- relative minimum singular value: `0.054661`;
- condition number: `18.295`;
- all 13 target SD proxies were below `0.25`;
- closest target to the threshold:
  `sp.activity.activity_beta_hour = 0.247145`.

Result: **all 13 targets non-weak**.

### Anchor C

- relative minimum singular value: `0.053736884767063994`;
- condition number: `18.60919188625747`.

All ecological-intensity, opportunistic-effort/detection, and activity targets remained
non-weak. The four state slopes exceeded the frozen target-SD threshold `0.25`:

| target | target SD proxy | criterion |
|---|---:|---:|
| `sp.state.beta_foraging_precip` | 0.26277152695059747 | <= 0.25 |
| `sp.state.beta_foraging_eastness` | 0.32592184483507364 | <= 0.25 |
| `sp.state.beta_foraging_season` | 0.3000975628964157 | <= 0.25 |
| `sp.state.beta_foraging_hour` | 0.29095173467869706 | <= 0.25 |

Each weak classification was caused only by the target-SD rule. The shared relative
minimum singular value remained far above `1e-3`, and the condition number remained far
below `1e3`.

## Interpretation of the negative result

R2 therefore answers a narrower question than a generic implementation failure.

The three-stream design successfully preserves:

- structural separation of ecological intensity from unknown opportunistic effort;
- structural separation of opportunistic global detection;
- structural identification of spatial and temporal activity terms;
- structural identification of spatial and temporal state terms;
- sparse-design practical refusal;
- activity-versus-unknown-annotation-detection refusal.

What fails is the stronger frozen requirement that **every state slope remain practically
precise at the deliberately hard Anchor C under only 18 calibrated/annotated training
spaces**.

The observed weakness is state-specific rather than observation-process-wide:
opportunistic effort/detection and activity parameters remain under the practical SD
threshold at the same anchor.

No threshold, seed, truth, calibration geometry, or anchor was changed in response to
this result.

## Infrastructure history

An earlier authorized R2 run, `35495217922`, was correctly classified
`INFRASTRUCTURE_BLOCKED`.

Its replicate-0 MCMC completed, but worker shard serialization failed at
`dataclasses.asdict(row)` because the frozen result object contains
`MappingProxyType` fields:

`TypeError: cannot pickle 'mappingproxy' object`.

The infrastructure-only repair:

- added explicit JSON-safe recursive serialization;
- retained every frozen scientific control unchanged;
- added anchor-level identification evidence to the audit artifact;
- added fail-fast evaluation of already-failed necessary pre-MCMC gate terms.

The corrected run `35549957893` produced the scientific R2 FAIL above.

## CI verification

At outcome head `621123e051ef11e6b842bdbd9d5bf4e84cc065f7`:

- Python 3.10: **271 passed, 23 skipped**;
- Python 3.11: **294 passed**;
- Python 3.12: **294 passed**.

The R2 precheck also passed before the gate decision.

## Promotion status

**v0.4-R2 is not promoted.**

The failure should not be repaired by loosening the frozen `target_sd_proxy <= 0.25`
criterion after observing the result. Any altered calibration design, state information
content, or anchor set belongs to a new prospective gate version.
