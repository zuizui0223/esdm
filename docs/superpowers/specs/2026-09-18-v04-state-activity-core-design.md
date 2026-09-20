# v0.4 Ecological State and Activity Core Design

## Status

Approved architecture for the first v0.4 implementation.

This design is stacked on the verified v0.3.2 hardening head
`5be236bbb05666e2c43c5a9642bee3fa50dab1de` and deliberately leaves the
v0.3.1/v0.3.2 frozen validation records unchanged.

The implementation belongs on `feature/v04-state-activity-core`. A separate stacked
validation PR will freeze and execute the full v0.4 promotion benchmark after the core is
implemented and reviewed.

## Goal

Extend the v0.3 generative graph from one ecological latent channel
(`log_intensity`) to a factorized ecological state model that distinguishes:

1. ecological intensity / availability;
2. conditional activity;
3. conditional ecological state;
4. observation effort and detection.

The central factorization is

```text
environment
  -> ecological intensity eta
  -> activity probability a | available
  -> state probabilities q | active, available
  -> observation process
  -> records / annotations
```

For context `c`, species `i`, and state `s`:

```text
lambda_available[c] = exp(eta[c])
a[c]                = P(active | available, c)
q[c, s]             = P(state=s | active, available, c)

lambda_annotated[c, s]
  = lambda_available[c]
  * a[c]
  * q[c, s]
  * effort[c]
  * detection
```

This is equivalent to a Poisson total active-event count followed by a conditional
multinomial state annotation. The implementation uses the independent-Poisson
representation because it composes naturally with the existing count-stream likelihood.

## Scientific interpretation

The factors are deliberately distinct.

- `exp(eta)` is ecological availability/intensity, not record intensity.
- `a` is conditional activity probability, not occurrence.
- `q` is conditional state composition among active/available ecological units.
- effort and detection remain observation-process quantities.

The model must not silently convert one layer into another. In particular:

- a presence-only stream does not automatically multiply ecological intensity by
  activity;
- state annotation is not treated as a direct observation of unconditional occupancy;
- unknown detection is not absorbed into ecological activity and then reported as if
  identified.

## Scope boundary

v0.4 adds ecological state/activity and annotated observation streams only.

It does **not** add:

- directed biotic interactions;
- partner-latent-field kernels;
- movement/accessibility;
- reciprocal/fixed-point dynamics;
- multiple simultaneous categorical state axes;
- state-specific unknown detection;
- a scientific `Supported` claim.

Those remain later-version concerns.

## Canonical state declaration

The generative model uses `esdm.domain.StateSpace`, `Partition`, and
`RefinementChain` as the canonical state declarations.

The older `esdm.core.StateAxis` object remains a compatibility/downstream primitive and
must not become a new generative dependency.

The first v0.4 implementation supports one categorical ecological state axis per species.
The state labels are ordered and fixed by the declared `StateSpace`.

## Latent channels

### Existing channel: ecological intensity

`log_intensity` remains the v0.3 ecological latent predictor and preserves current
semantics.

A species with only suitability processes behaves exactly as in v0.3.2.

### New channel: activity

The activity channel is represented on a logit scale:

```text
activity_logit[c] = alpha_activity + sum_k beta_activity[k] x_k[c]
activity[c]       = sigmoid(activity_logit[c])
```

Activity is conditional on ecological availability. It is therefore used only by streams
that explicitly consume the activity channel.

If no activity process is declared, the neutral derived activity value is `1.0`.
This preserves v0.3 presence-only behaviour. A stream that declares activity as an
information target must still have a declared process-to-stream path under
`Model.check_design()`.

### New channel: categorical state

The state channel is represented by reference-coded logits:

```text
state_logit[c, reference] = 0
state_logit[c, s] =
    alpha_state[s] + sum_k beta_state[s, k] x_k[c]
    for s != reference

q[c, :] = softmax(state_logit[c, :])
```

Fixing one reference-state logit to zero removes the softmax additive invariance at the
parameterization level.

The reference state is declared explicitly and must belong to the state space.

## Process API refactor

The existing process protocol is hard-wired to `log_intensity`. v0.4 introduces a
generic backend-neutral contribution API while retaining the old suitability methods as
compatibility shims.

Canonical process methods become conceptually:

```python
process.contribution(...)
process.contribution_array(...)
```

Each contribution carries:

- a semantic `output_channel`;
- ordered values over model contexts;
- optional categorical labels for a state channel.

The first supported channel algebras are:

- `log_intensity`: additive real predictor;
- `activity`: additive logit predictor;
- `state`: additive reference-coded logit vector.

Because v0.4 supports exactly one categorical state axis per species, the semantic
channel is the single name `state`. Multiple named state axes are intentionally deferred
rather than encoded prematurely into the channel string.

`LinearSuitability` is adapted to the generic contribution API without changing its
numerical semantics.

This channel abstraction is intentionally sufficient for v0.4 and later allows v0.5
processes to consume partner latent fields without rewriting the model composition layer.

## New ecological processes

### `LinearActivity`

A backend-neutral ecological process with:

- `name = "activity"` by default;
- `output_channel = "activity"`;
- an intercept parameter;
- zero or more environmental coefficient parameters;
- Normal prior declarations using `PriorSpec`;
- scalar and array evaluation;
- explicit knockout.

Knockout semantics:

```text
preserve baseline activity intercept
neutralize environmental activity slopes
```

This parallels `LinearSuitability.knockout()`: a process knockout removes the
environmentally varying effect while retaining the baseline layer.

### `LinearState`

A categorical ecological process with:

- a declared state space;
- one explicit reference state;
- non-reference state intercept parameters;
- optional non-reference state environmental slope parameters;
- reference-coded logits;
- scalar and array evaluation;
- explicit knockout.

Knockout semantics:

```text
preserve baseline state composition
neutralize environmental state slopes
```

The knockout must not force all states to equal probability unless that was already the
baseline composition.

## Latent field containers

The current `LatentFields` / `LatentFieldArrays` objects are extended rather than
replaced.

They retain `log_intensity` and add explicit derived channels:

- activity logit;
- activity probability;
- state logits;
- state probabilities.

Array-first evaluation remains mandatory for JAX/NumPyro. Context is always the leading
axis. State is the second axis for categorical fields.

No Python loop over contexts may be introduced into a parameter-dependent JAX trace.

The existing v0.3.2 JAXPR scaling contract remains a regression requirement.

## Observation-stream contract

v0.4 adds a backend-neutral observation-block abstraction so NumPyro and simulation do
not need a second copy of stream mathematics.

A stream converts latent channels plus observation-process parameters into one or more
observation blocks. Each block declares:

- likelihood family;
- ordered expected values;
- observed values;
- static structural-exposure mask;
- a deterministic block name.

The first supported family remains Poisson.

`PresenceOnly` becomes the one-block special case of this interface while preserving
its public behaviour.

## Existing `PresenceOnly` semantics

`PresenceOnly` continues to consume only `log_intensity` unless explicitly changed in
a future version.

Its rate remains:

```text
lambda_record
  = exp(log_intensity)
  * effort
  * detection
```

It does not automatically use the activity or state channels merely because those
channels exist in the same model.

This is necessary for cross-stream separation: broad presence-only data can inform
ecological intensity while partial annotated data inform activity/state.

## New `StateAnnotatedCount` stream

`StateAnnotatedCount` observes state-labelled event counts.

Required declarations:

- explicit stream name;
- explicit target species;
- explicit state axis;
- effort model;
- detection model/constant;
- `informs` process names;
- consumed channels:
  `log_intensity`, `activity`, and the declared state channel.

For species `i`, context `c`, and state `s`:

```text
lambda[c, s]
  = exp(log_intensity[i, c])
  * activity[i, c]
  * state_probability[i, c, s]
  * effort[c]
  * detection
```

Counts for each state are conditionally independent Poisson variables under this
representation.

Required fail-closed rules:

- counts must be non-negative;
- state labels must exactly match the declared state space;
- unknown states are errors;
- missing target-species blocks are errors;
- positive counts in structurally zero-exposure cells are errors;
- a stream consuming state/activity without a valid computational path fails design
  checking.

## Detection

The first stream implementation supports:

1. known constant detection probability; and
2. an optional unknown global detection intercept used for identification tests.

Unknown detection remains an observation-process parameter.

v0.4 does not introduce unknown state-specific detection.

The negative-control design uses an intercept-only activity process plus unknown global
detection. With only their product observed, the activity intercept and detection
parameter are structurally non-identifiable. This is intentional and must be detected by
the exact Jacobian diagnostic rather than resolved by prior regularization.

## Model composition and design checking

`Model.check_design()` remains a path check, not an identification claim.

For every ecological process it must verify:

```text
process
 -> semantic latent channel
 -> targeted observation stream consuming that channel
```

Additional v0.4 validation:

- all state processes for one species must refer to the same declared state space;
- categorical contribution labels must agree exactly;
- a state stream cannot target a species lacking its declared state channel;
- parameter names remain unique within each species parameter block;
- existing acyclic latent-species dependency rules remain unchanged.

## Parameter layout and NumPyro

The NumPyro backend continues to obtain priors from the process/stream graph.

The parameter layout must include activity/state process parameters with stable fully
qualified sample-site names.

Suggested naming:

```text
sp.activity.intercept
sp.activity.beta_<covariate>

sp.state.alpha_<state>
sp.state.beta_<state>_<covariate>

stream.<name>.detection_intercept
```

Reference-state parameters do not exist as free sample sites.

The backend must consume generic observation blocks rather than reimplementing the
state/activity equations.

Existing static zero-exposure filtering applies to every Poisson observation block.

## Simulation

In-model simulation must use the same latent-channel construction and observation blocks
as deterministic likelihood evaluation and NumPyro inference.

A generic simulator replaces the current presence-only-specific internal assumption while
retaining `simulate_presence_only` as a compatibility wrapper.

For annotated streams the generated artifact records:

- counts by stream, species, context, and state;
- expected rates by the same keys;
- optionally the generating latent activity/state fields for benchmark auditing.

## Posterior-derived fields

v0.4 adds posterior extraction for:

- ecological record rates;
- activity probability;
- state probabilities;
- annotated state-count rates.

These are posterior-derived outputs. They must not be fed back as raw generative
covariates.

## Identification behaviour

v0.4 must preserve the v0.3.2 distinction between:

- structural identification;
- practical identification;
- posterior recovery;
- scientific support.

### Positive identification control

With known detection and sufficient annotated calibration coverage:

- activity parameters must be structurally identified;
- state parameters must be structurally identified;
- frozen practical-identification checks in the validation PR must not classify the
  target parameters as weak.

### Negative detection control

For an intercept-only activity process with unknown global detection and no independent
detection information:

- the activity intercept and detection parameter must be structurally
  `NotIdentified`;
- posterior contraction must not override that result;
- no `Supported` claim may be emitted.

This control is a required refusal test.

## Cross-stream transfer design

The full v0.4 promotion benchmark belongs in the subsequent validation PR.

Its architecture is fixed here:

- broad presence-only stream across the full training geometry informs ecological
  intensity;
- annotated state/activity stream covers only a deterministic subset of training
  contexts/spaces;
- ecological intensity, activity, and state processes share declared environmental
  covariates but remain separate latent channels;
- a held-out block receives no fitting annotations;
- state/activity predictions are evaluated on held-out annotations generated from known
  truth;
- full models are compared with explicit activity/state knockouts, not with ad hoc term
  deletion.

Numerical thresholds, seeds, replicate counts, and exact geometry are frozen in the
validation PR **before** outcome-producing runs.

## Compatibility

The following v0.3.2 behaviours are non-negotiable regression contracts:

- existing `LinearSuitability` numerical output;
- existing `PresenceOnly` rate semantics;
- explicit non-empty stream targets;
- static zero-exposure handling;
- exact/practical identification APIs;
- array-first JAX trace scaling;
- v0.3.1 and v0.3.2 frozen validation documents;
- Python 3.10 core compatibility;
- NumPyro execution on supported Python versions.

Existing v0.3 models must run without declaring activity or state processes.

## Error handling

New fail-closed conditions include:

- invalid/duplicate state labels;
- reference state absent from state space;
- inconsistent state labels across categorical contributions;
- state observation with no state process;
- annotated data missing declared states/species blocks;
- positive observation in statically zero-exposure cells;
- duplicate ecological parameter names;
- unsupported likelihood family;
- unsupported channel algebra.

Errors caused by design structure must occur before MCMC starts whenever they can be
known statically.

## Test strategy for the core PR

Implementation follows TDD.

### Domain/process unit tests

- valid and invalid reference-coded state parameterization;
- softmax probabilities finite, positive, and sum to one;
- activity probabilities in `(0, 1)`;
- activity knockout preserves baseline and removes slopes;
- state knockout preserves baseline composition and removes slopes.

### Composition tests

- v0.3 intensity-only model unchanged;
- activity/state channels compose in scalar and array paths;
- inconsistent state axes fail closed;
- streams without a process/channel path fail closed.

### Observation tests

- annotated rates equal the declared factorization exactly;
- sum of state-specific rates equals total active observed rate;
- known zero exposure yields zero generated counts;
- positive count at known zero exposure fails closed;
- presence-only rate is unaffected by merely adding activity/state processes.

### Inference tests

On supported Python versions:

- NumPyro sample sites include activity/state parameters but not reference-state
  parameters;
- a small known-detection world recovers finite activity/state posterior draws;
- unknown-detection refusal fixture is structurally rank deficient;
- posterior field extraction has correct shapes and normalization.

### Scaling tests

- JAXPR equation count remains approximately context-size invariant for the new
  activity/state array path;
- no context-scalar tracing regression at 2,880 contexts.

### Full regression

- all existing tests remain green on Python 3.10/3.11/3.12;
- NumPyro-specific tests execute on supported Python versions;
- frozen v0.3.1/v0.3.2 result files are unchanged.

## PR decomposition

### PR #9 — v0.4 state/activity core

Stacked from PR #8 / `feature/v032-identifiability-hardening`.

Contains:

- generic process contribution/channel layer;
- extended latent field containers;
- `LinearActivity`;
- `LinearState`;
- generic Poisson observation blocks;
- `StateAnnotatedCount`;
- simulation/NumPyro integration;
- structural-identification regression controls;
- array-scaling regression;
- compatibility tests.

It does not make a v0.4 promotion claim.

### PR #10 — v0.4 frozen validation

Stacked from PR #9.

Before outcome-producing runs it freezes:

- benchmark geometry;
- calibration coverage;
- known truths;
- priors;
- identification anchors;
- practical-identification thresholds;
- MCMC profile;
- recovery criteria;
- held-out transfer score;
- knockout comparisons;
- divergence limits;
- seeds and replicate counts.

Only after the gate document is committed are full outcomes executed.

## Success condition for the core PR

PR #9 is ready for review when:

1. the v0.4 channels are generated by one shared graph used by simulation,
   deterministic likelihood, and NumPyro;
2. existing v0.3 models are numerically unchanged;
3. known-detection state/activity smoke recovery works;
4. the unknown-detection negative control is structurally refused;
5. the array path preserves the v0.3.2 trace-scaling property;
6. the entire CI matrix is green.

Passing PR #9 does not mean v0.4 is promoted. Promotion requires the separate frozen
cross-stream validation gate in PR #10.
