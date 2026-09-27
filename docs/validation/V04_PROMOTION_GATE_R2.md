# v0.4 state/activity promotion gate R2

Status: **FROZEN BEFORE R2 OUTCOME-PRODUCING VALIDATION**

Core base: PR #9 head `f0b269c026e944e922fef539505be450a0a72122`.

R1 was invalidated before results inspection. R2 is a new gate definition; no R1 outcome
is used to choose R2 geometry, truth, priors, thresholds, seeds, or pass criteria.

Passing R2 is semi-synthetic methodological validation only. It is not empirical
biological validation and it does not create a scientific `Supported` claim.

## R2 claim boundary

R2 tests the bounded methodological claim:

> With partial calibrated observation streams, esdm can separate ecological
> intensity/activity from unknown observation effort/detection, recover explicit DOY/hour
> activity and state effects, and transfer those ecological fields to a spatially held-out
> block. When the relevant calibration stream is removed, the intended confounding is
> refused rather than silently regularized away.

R2 does not test directed biotic interactions, movement/accessibility, state-specific
detection, multiple simultaneous state axes, or empirical mechanism validity.

## Frozen source and domain

R2 reuses the pinned v0.3.1/v0.3.2 station geometry:

- repository: `the-pudding/data`;
- source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`;
- source path: `rain/annual_precipitation.csv`;
- source blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`;
- selected rows: first **120** rows after the header;
- DOY bins: **15, 75, 135, 195, 255, 315**;
- hour bins: **0, 6, 12, 18**;
- total contexts: **2,880**.

Longitude split:

- west: longitude `< -110`;
- central: `-110 <= longitude < -85`;
- east: longitude `>= -85`.

Fits use west + central only. East is held out from every fit.

## Frozen covariates

Spatial station covariates are standardized using training stations only:

- `precip_z_train`;
- `lat_z_train`;
- `eastness_z_train`.

Temporal covariates are deterministic functions of each context:

`season_sin = sin(2*pi*(doy - 15)/365)`

`season_cos = cos(2*pi*(doy - 15)/365)`

`diurnal_sin = sin(2*pi*hour/24)`

`diurnal_cos = cos(2*pi*hour/24)`.

The east block must satisfy

`min(heldout eastness_z_train) > max(training eastness_z_train)`.

## Frozen ecological truth

### Ecological intensity

`eta = -2.0
       + 0.45*precip_z_train
       - 0.20*lat_z_train
       + 0.35*eastness_z_train
       + 0.30*season_sin`.

The seasonal ecological coefficient is deliberately confounded with the seasonal
opportunistic-presence effort coefficient unless the calibrated presence stream is used.

### Conditional activity

`activity_logit = -0.35
                  + 0.40*precip_z_train
                  + 0.30*eastness_z_train
                  + 0.50*season_cos
                  + 0.45*diurnal_cos`.

`activity = sigmoid(activity_logit)`.

Activity therefore varies over both DOY and hour as well as space.

### Conditional categorical state

State space:

- reference: `resting`;
- non-reference: `foraging`.

Reference logit is fixed at zero.

`foraging_logit = 0.20
                  - 0.35*precip_z_train
                  + 0.40*eastness_z_train
                  - 0.50*season_sin
                  + 0.55*diurnal_sin`.

State probabilities are the two-state softmax.

## Frozen observation streams

R2 uses four streams.

### 1. Opportunistic presence stream

Name: `presence_opportunistic`.

- type: `PresenceOnly`;
- covers every context;
- detection: known 1.0;
- effort:
  `4.0 * exp(gamma_presence_season * season_sin)`;
- unknown truth:
  `gamma_presence_season = 0.35`;
- informs: suitability.

Because ecological intensity also contains `season_sin`, this stream alone identifies
only their sum on the log-rate scale.

### 2. Calibrated presence stream

Name: `presence_calibrated`.

- type: `PresenceOnly`;
- known effort **3.0** on its calibration spaces;
- zero effort elsewhere;
- detection: known 1.0;
- informs: suitability.

Select exactly **12 training stations** by eastness-rank quantiles. Sort training spaces
by `(eastness_z_train, station_id)` and select the nearest integer ranks to

`k*(n_train-1)/11`, for `k=0..11`.

All 24 temporal contexts at those spaces are calibrated.

### 3. Opportunistic state-annotated stream

Name: `annotated_opportunistic`.

- type: `StateAnnotatedCount`;
- covers every context;
- effort:
  `6.0 * exp(gamma_annotation_diurnal * diurnal_cos)`;
- unknown effort truth:
  `gamma_annotation_diurnal = 0.30`;
- detection:
  `sigmoid(detection_intercept)`;
- unknown detection-intercept truth:
  `detection_intercept = 0.40`;
- informs: activity and state.

Activity also contains `diurnal_cos`, so activity and annotation effort are deliberately
difficult to separate without the calibrated annotated stream. Activity intercept and
global detection also enter the overall annotated rate multiplicatively.

### 4. Calibrated state-annotated stream

Name: `annotated_calibrated`.

- type: `StateAnnotatedCount`;
- known effort **5.0** on its calibration spaces;
- zero effort elsewhere;
- known detection probability **0.85**;
- informs: activity and state.

Select exactly **18 training stations** by eastness-rank quantiles. Sort training spaces
by `(eastness_z_train, station_id)` and select the nearest integer ranks to

`k*(n_train-1)/17`, for `k=0..17`.

All 24 temporal contexts at those spaces are calibrated.

## Held-out evaluation stream

Only `annotated_opportunistic` east counts are used for the v0.4 transfer score.

Calibrated streams are fitting/calibration information only and have zero exposure in the
east block.

The east block is never used for fitting, standardization, calibration-space selection,
threshold selection, or model choice.

## Frozen positive identification targets

At each positive anchor, exact structural identification and practical identification are
checked for the following targets:

1. `sp.suitability.beta_season`;
2. `stream.presence_opportunistic.gamma_presence_season`;
3. `sp.activity.activity_intercept`;
4. `sp.activity.activity_beta_season`;
5. `sp.activity.activity_beta_diurnal`;
6. `sp.activity.activity_beta_eastness`;
7. `stream.annotated_opportunistic.gamma_annotation_diurnal`;
8. `stream.annotated_opportunistic.detection_intercept`;
9. `sp.state.beta_foraging_season`;
10. `sp.state.beta_foraging_diurnal`;
11. `sp.state.beta_foraging_eastness`.

Structural identification uses exact `jax.jacfwd` with:

- `rtol = 1e-8`;
- `atol = 1e-10`.

Practical identification uses:

- relative minimum singular value `>= 1e-3`;
- condition number `<= 1e3`;
- Fisher-like target SD proxy `<= 0.30`;
- Fisher ridge `1e-10`.

All 11 targets must be structurally `Identified` and practically non-weak at all three
positive anchors.

## Frozen positive anchors

Parameters not listed remain at generating truth.

### Anchor A

Generating truth.

### Anchor B

- intensity `beta_season = 0.55`;
- presence `gamma_presence_season = 0.10`;
- activity intercept `-0.05`;
- activity `beta_season = 0.25`;
- activity `beta_diurnal = 0.70`;
- activity `beta_eastness = 0.15`;
- annotation `gamma_annotation_diurnal = 0.10`;
- annotation detection intercept `-0.20`;
- state `beta_foraging_season = -0.25`;
- state `beta_foraging_diurnal = 0.75`;
- state `beta_foraging_eastness = 0.20`.

### Anchor C

- intensity `beta_season = 0.10`;
- presence `gamma_presence_season = 0.60`;
- activity intercept `-0.70`;
- activity `beta_season = 0.75`;
- activity `beta_diurnal = 0.20`;
- activity `beta_eastness = 0.55`;
- annotation `gamma_annotation_diurnal = 0.60`;
- annotation detection intercept `0.90`;
- state `beta_foraging_season = -0.75`;
- state `beta_foraging_diurnal = 0.25`;
- state `beta_foraging_eastness = 0.65`.

## Frozen no-presence-calibration refusal

Remove the calibrated presence stream while retaining all other positive-profile
components.

At each of the three positive anchors:

- `sp.suitability.beta_season`;
- `stream.presence_opportunistic.gamma_presence_season`

must both be structurally `NotIdentified`.

This is an exact log-rate confounding control.

## Frozen activity/detection refusal

Use the positive geometry but:

- remove the calibrated annotated stream;
- replace the activity process with intercept-only activity;
- retain unknown `detection_intercept`;
- retain opportunistic annotated effort.

Three refusal anchors are used:

- R-A: activity intercept `-0.35`, detection intercept `0.40`;
- R-B: activity intercept `0.20`, detection intercept `-0.30`;
- R-C: activity intercept `-0.90`, detection intercept `0.90`.

At all three anchors:

- `sp.activity.activity_intercept`;
- `stream.annotated_opportunistic.detection_intercept`

must both be structurally `NotIdentified`.

This is the required refusal that demonstrates the calibrated annotated stream is what
permits the positive profile to separate activity level from global detection.

## Frozen inference profile

Outcome runs use **16** independent generated datasets.

- base seed: **20260926**;
- seed stride: **47**;
- chains: **2**, sequential;
- warmup per chain: **300**;
- retained draws per chain: **350**;
- target acceptance: **0.92**;
- intervals: **90%**.

Every replicate is generated once from the complete four-stream positive truth.

Training fits receive west + central counts only.

Each replicate fits:

1. full model;
2. activity knockout;
3. state knockout.

All three fits receive identical training data and identical observation-stream
definitions. Knockouts preserve activity intercept or baseline state composition and
remove only environmental slopes.

## Frozen recovery targets

Across the 16 full fits, R2 requires recovery of these 11 parameters:

| target | truth | max abs mean bias |
| --- | ---: | ---: |
| `sp.suitability.beta_season` | 0.30 | 0.15 |
| `stream.presence_opportunistic.gamma_presence_season` | 0.35 | 0.15 |
| `sp.activity.activity_intercept` | -0.35 | 0.20 |
| `sp.activity.activity_beta_season` | 0.50 | 0.15 |
| `sp.activity.activity_beta_diurnal` | 0.45 | 0.15 |
| `sp.activity.activity_beta_eastness` | 0.30 | 0.15 |
| `stream.annotated_opportunistic.gamma_annotation_diurnal` | 0.30 | 0.15 |
| `stream.annotated_opportunistic.detection_intercept` | 0.40 | 0.20 |
| `sp.state.beta_foraging_season` | -0.50 | 0.15 |
| `sp.state.beta_foraging_diurnal` | 0.55 | 0.15 |
| `sp.state.beta_foraging_eastness` | 0.40 | 0.15 |

For every target separately, 90% interval truth coverage must be `>= 0.75`.

Other parameters are recorded but are not promotion targets.

## Frozen held-out transfer criteria

Score east `annotated_opportunistic` state counts using state-specific Poisson posterior
log predictive density averaged over all state-context observations.

### Activity knockout

`gain_activity = full_score - activity_knockout_score`.

Require:

- positive gain in at least **75%** of replicates;
- mean gain `>= 0.005` per state-context.

### State knockout

`gain_state = full_score - state_knockout_score`.

Require:

- positive gain in at least **75%** of replicates;
- mean gain `>= 0.005` per state-context.

## Frozen temporal-signal criteria

The four explicitly temporal ecological slopes must each satisfy the recovery and coverage
criteria above:

- activity `beta_season`;
- activity `beta_diurnal`;
- state `beta_foraging_season`;
- state `beta_foraging_diurnal`.

Therefore DOY/hour cannot pass the gate merely by contributing repeated counts.

## Frozen computation criterion

Exactly **48** fits are required: 16 replicates × 3 fits.

Mean divergences per fit must be `<= 0.10`.

Worker interruption, source mismatch, cancellation, timeout, missing artifact, or memory
failure is `INFRASTRUCTURE_BLOCKED`, not scientific PASS/FAIL.

## Mechanical PASS rule

R2 PASS requires every frozen condition:

1. all positive structural targets identified at all anchors;
2. all positive practical targets non-weak at all anchors;
3. no-presence-calibration seasonal intensity/effort pair refused at all anchors;
4. no-annotated-calibration activity/detection pair refused at all refusal anchors;
5. eastness extrapolation integrity;
6. all 11 recovery-bias checks;
7. all 11 recovery-coverage checks;
8. activity-knockout positive-gain rate and mean gain;
9. state-knockout positive-gain rate and mean gain;
10. exactly 16 replicates and 48 fits;
11. mean divergences per fit <= 0.10.

No condition may compensate for another.

The gate produces evidence and a mechanical decision only. It does not emit a scientific
`Supported` claim.
