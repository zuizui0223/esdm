# v0.4-R2 hard state/activity separation promotion gate

Status: **FROZEN BEFORE v0.4-R2 OUTCOMES**

This R2 gate supersedes the earlier v0.4 validation draft because the earlier profile had
known observation parameters in its positive state/activity benchmark and no temporal
truth on the activity/state axes. No earlier v0.4 outcome artifact or replicate result is
used by this gate.

Base implementation: PR #9 head
`f0b269c026e944e922fef539505be450a0a72122`.

Passing this gate is semi-synthetic methodological validation only. It does not create an
empirical biological or scientific `Supported` claim.

## Promotion question

Can one joint generative model separate:

1. ecological intensity;
2. unknown observation effort;
3. unknown global detection;
4. conditional activity;
5. conditional categorical state;

when only partial calibrated/annotated observations are available and activity/state plus
sampling effort vary over both space and time?

A PASS requires all layers to remain separable under the frozen positive design and
requires explicit refusal controls to fail closed.

## Frozen source and domain

Reuse the pinned 120-station geometry:

- repository: `the-pudding/data`;
- commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`;
- path: `rain/annual_precipitation.csv`;
- blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`;
- first 120 data rows;
- DOY: `15, 75, 135, 195, 255, 315`;
- hour: `0, 6, 12, 18`;
- total contexts: 2,880.

Spatial split:

- west: longitude < -110;
- central: -110 <= longitude < -85;
- east: longitude >= -85.

Training uses west + central only. East is held out from every fit.

## Frozen covariates

Spatial covariates are standardized using training stations only:

- `precip_z_train`;
- `lat_z_train`;
- `eastness_z_train`.

Temporal covariates are deterministic functions of the declared domain:

- `season_sin = sin(2*pi*(doy - 15)/365)`;
- `season_cos = cos(2*pi*(doy - 15)/365)`;
- `hour_sin = sin(2*pi*hour/24)`;
- `hour_cos = cos(2*pi*hour/24)`.

The east block must satisfy:

`min(heldout eastness_z_train) > max(training eastness_z_train)`.

## Frozen ecological intensity truth

Ecological availability remains spatial:

`eta = -2.0 + 0.45*precip_z_train - 0.20*lat_z_train + 0.35*eastness_z_train`.

## Frozen activity truth

Activity varies in space and time:

`activity_logit = -0.35 + 0.50*precip_z_train + 0.35*eastness_z_train + 0.55*season_sin + 0.40*hour_sin`.

Truth:

- activity intercept = -0.35;
- activity beta_precip = 0.50;
- activity beta_eastness = 0.35;
- activity beta_season = 0.55;
- activity beta_hour = 0.40.

## Frozen state truth

State space:

- reference = `resting`;
- non-reference = `foraging`.

The foraging reference-coded logit varies in space and time:

`state_logit_foraging = 0.20 - 0.45*precip_z_train + 0.40*eastness_z_train + 0.50*season_cos - 0.45*hour_cos`.

Truth:

- alpha_foraging = 0.20;
- state beta_precip = -0.45;
- state beta_eastness = 0.40;
- state beta_season = 0.50;
- state beta_hour = -0.45.

## Frozen observation streams

### Stream O: broad opportunistic PresenceOnly

Coverage: all 2,880 contexts in generation; west + central in fitting.

This stream consumes only `log_intensity`.

Its observation effort is unknown and log-linear:

`effort_O = 4.0 * exp(0.35*precip_z_train + 0.30*season_cos - 0.25*hour_sin)`.

Free effort parameters:

- `gamma_precip = 0.35`;
- `gamma_season = 0.30`;
- `gamma_hour = -0.25`.

Its global detection is unknown:

- `detection_intercept = -0.20`;
- probability = sigmoid(-0.20).

Thus Stream O deliberately contains:

- ecological-vs-effort confounding on precipitation;
- ecological-intercept-vs-detection confounding;
- time-varying observation effort.

### Stream C: partial calibrated PresenceOnly

Coverage in fitting: exactly the positive calibration training spaces below, all 24
DOY/hour contexts.

Coverage in held-out evaluation is not used as a promotion score.

Observation process:

- known effort = 3.0;
- known detection = 0.90.

Stream C consumes only `log_intensity`.

Its role is to provide partial independent information that separates ecological
intensity from Stream O's unknown effort and detection.

### Stream A: partial StateAnnotatedCount

Training coverage: the same positive calibration spaces, all 24 DOY/hour contexts.

Held-out generation/evaluation coverage: every east space, all 24 temporal contexts.

Observation process:

- known effort = 8.0;
- known detection = 0.85.

Stream A consumes `log_intensity`, `activity`, and `state`.

East annotations are generated but never supplied to fitting.

## Frozen positive calibration geometry

Select exactly 18 training stations by deterministic maximin coverage in the
`(precip_z_train, eastness_z_train)` plane.

Algorithm:

1. candidate set = all training spaces;
2. first point = lexicographically smallest station among those maximizing
   `precip_z_train^2 + eastness_z_train^2`;
3. each later point maximizes its minimum squared Euclidean distance to already selected
   points in the two-dimensional standardized plane;
4. ties are broken by station ID;
5. stop at 18 points.

No observed counts or fitted outcomes enter selection.

All 24 temporal contexts are exposed at those 18 training stations for Streams C and A.

## Frozen sparse practical-refusal geometry

Use exactly 4 training stations minimizing

`precip_z_train^2 + eastness_z_train^2`

with station ID tie-breaker.

All 24 temporal contexts are exposed for Streams C and A at those 4 stations.

The sparse profile changes only calibration/annotation geometry.

Required sparse behavior:

- the frozen positive identification targets below remain structurally Identified at all
  three anchors;
- at least one target is practically weak at every anchor.

## Frozen positive identification targets

Observation-separation targets:

- `sp.suitability.beta_precip`;
- `stream.opportunistic.gamma_precip`;
- `stream.opportunistic.gamma_season`;
- `stream.opportunistic.gamma_hour`;
- `stream.opportunistic.detection_intercept`.

Activity targets:

- `sp.activity.activity_beta_precip`;
- `sp.activity.activity_beta_eastness`;
- `sp.activity.activity_beta_season`;
- `sp.activity.activity_beta_hour`.

State targets:

- `sp.state.beta_foraging_precip`;
- `sp.state.beta_foraging_eastness`;
- `sp.state.beta_foraging_season`;
- `sp.state.beta_foraging_hour`.

All 13 targets must be structurally Identified and practically non-weak in the positive
profile at all frozen anchors.

## Frozen identification anchors

Anchor A: generating truth.

Anchor B changes only:

- ecological beta_precip = 0.70;
- gamma_precip = 0.10;
- gamma_season = 0.55;
- gamma_hour = -0.05;
- detection_intercept = -0.70;
- activity intercept = -0.05;
- activity beta_precip = 0.70;
- activity beta_eastness = 0.15;
- activity beta_season = 0.30;
- activity beta_hour = 0.65;
- alpha_foraging = -0.10;
- state beta_precip = -0.20;
- state beta_eastness = 0.65;
- state beta_season = 0.25;
- state beta_hour = -0.70.

Anchor C changes only:

- ecological beta_precip = 0.20;
- gamma_precip = 0.60;
- gamma_season = 0.10;
- gamma_hour = -0.50;
- detection_intercept = 0.35;
- activity intercept = -0.75;
- activity beta_precip = 0.25;
- activity beta_eastness = 0.60;
- activity beta_season = 0.75;
- activity beta_hour = 0.20;
- alpha_foraging = 0.50;
- state beta_precip = -0.70;
- state beta_eastness = 0.20;
- state beta_season = 0.70;
- state beta_hour = -0.20.

Structural identification:

- JAX `jax.jacfwd`;
- relative SVD rtol = 1e-8;
- absolute atol = 1e-10.

Practical identification:

- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

## Frozen structural refusal control

A separate refusal fixture keeps:

- the same intensity process;
- the same state process;
- the same Stream C partial calibrated PresenceOnly;
- the same positive 18-space Stream A geometry.

But Stream A uses:

- intercept-only activity;
- unknown `LogitDetection("detection_intercept")`;
- no independent detection information for Stream A.

The activity intercept and Stream A detection intercept must both be structurally
`NotIdentified` at each of three anchors:

- U-A: activity -0.35, detection 0.40;
- U-B: activity 0.20, detection -0.30;
- U-C: activity -0.90, detection 0.90.

## Frozen inference profile

Outcome runs:

- replicates = 16;
- base seed = 20260926;
- seed stride = 47;
- chains = 2 sequential;
- warmup = 300 per chain;
- retained = 350 per chain;
- target_accept = 0.90;
- interval mass = 0.90.

Each replicate generates all three streams once, then fits the same west+central training
data with:

1. full model;
2. activity knockout;
3. state knockout.

Thus there are exactly 48 fits.

## Frozen recovery targets

Across 16 full fits, recover all of:

Observation separation:

- beta_precip ecological truth = 0.45;
- gamma_precip = 0.35;
- gamma_season = 0.30;
- gamma_hour = -0.25;
- opportunistic detection_intercept = -0.20.

Activity:

- beta_precip = 0.50;
- beta_eastness = 0.35;
- beta_season = 0.55;
- beta_hour = 0.40.

State:

- beta_precip = -0.45;
- beta_eastness = 0.40;
- beta_season = 0.50;
- beta_hour = -0.45.

For each of the 13 targets separately:

- abs(mean posterior bias) <= 0.18;
- 90% truth coverage >= 0.75.

## Frozen held-out transfer criteria

Score east held-out Stream A state counts by mean state-context posterior Poisson log
predictive density.

Activity comparison:

`gain_activity = full - activity_knockout`.

Requires:

- positive gain in >= 75% of replicates;
- mean gain >= 0.005 per state-context.

State comparison:

`gain_state = full - state_knockout`.

Requires:

- positive gain in >= 75% of replicates;
- mean gain >= 0.005 per state-context.

## Frozen computation criterion

Across all 48 fits:

- mean divergences per fit <= 0.10.

Infrastructure interruption, cancellation, missing artifact, source mismatch, or worker
failure is `INFRASTRUCTURE_BLOCKED`, not scientific PASS/FAIL.

## Mechanical PASS

v0.4-R2 PASS requires every frozen check above to pass simultaneously:

- positive structural identification;
- positive practical identification;
- sparse structural identification;
- sparse practical refusal;
- unknown-detection refusal;
- eastness extrapolation integrity;
- all 13 recovery-bias checks;
- all 13 recovery-coverage checks;
- both activity transfer checks;
- both state transfer checks;
- replicate count = 16;
- fit count = 48;
- divergence criterion.

No threshold, seed, truth, geometry, or prior may be changed after this freeze in response
to observed outcomes.
