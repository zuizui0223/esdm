# esdm

`esdm` develops a **process-based ecological state distribution model** for community ecology. Ordinary species-distribution modelling is treated as a low-resolution special case in which the only explicit state is occurrence and the only ecological process is environmental suitability.

The central object is a generative graph:

```text
ecological processes
    -> latent community fields
    -> observation processes
    -> data

posterior
    -> identification / validation / claims
    -> diversity / network / maps
```

The repository name is historical/convenient. The project does **not** claim `ESDM` as a new acronym.


## Current scientific status

The active empirical endpoint is now the separately named **E4 MICA exact-sparse
programme**. The underlying process/state model is still the frozen **v0.4-R5b**
generation; no new semi-synthetic rescue generation was introduced.

The empirical lineage is deliberately cumulative rather than rewritten:

```text
v0.4-R5b known-truth PASS
  -> first Snapshot Japan opening: terminal data-contract stop before fit
  -> E2 MICA: consumed zero-duration deployment stop before fit
  -> E3 MICA exploratory reduced endpoint: dense NUTS infrastructure timeout
  -> E4 MICA exact structural-exposure compaction
  -> same scientific model / same posterior target
  -> one-shot empirical fit completed
```

E4 changed **only the computational representation**. Contexts with zero structural
exposure in every retained observation stream contribute exactly zero likelihood for all
parameter values, so they were removed before latent fields were materialized. This
reduced the training domain from **615,020 to 11,531 contexts** and the east-heldout
domain from **560,012 to 10,168 contexts** without changing priors, covariates,
likelihoods, response mapping, training/heldout partition, MCMC settings, or the
posterior target.

The frozen E4 one-shot result completed all three NUTS fits with **0 divergences** and
serialized **733/733** east-heldout deployment scores:

| Model | mean heldout log score |
| --- | ---: |
| Full | -7.6929864071 |
| Activity knockout | -7.0539352267 |
| State knockout | -7.7013773321 |

Therefore:

- **activity gain = -0.6390511804**: activity information did **not** improve east-heldout
  prediction in this exploratory MICA endpoint;
- **state gain = +0.0083909250**: state information gave a **small descriptive
  exploratory improvement** without independent direct state calibration.

Neither result is confirmatory, causal, or a parameter-recovery claim. E4 is terminal:
there is no same-programme rerun, threshold/stream retuning, or within-E4 switch to
Laplace/INLA.

Frozen post-result audits show that the activity failure is **not uniformly negative
across all 733 deployments**, but the apparent majority of tiny positive gains comes
almost entirely from sites with no focal events. Of the **128 event-bearing heldout
deployments, 127 favor the activity knockout**; the 605 zero-event deployments contribute
only tiny positive gains. The worst 50 deployments account for about **90.8%** of total
negative activity-loss magnitude.

The transfer also combines geographic extrapolation with source-domain shift. The
east-heldout activity covariate range is entirely outside training eastness support
(training z about **-0.94 to 1.65**; heldout about **3.20 to 8.49**), and a D-prefixed
heldout source stratum absent from the training StateAnnotatedCount stratum contains
about **99.0% of focal events** and **99.6% of negative activity-loss magnitude**.
The raw night/day event-rate ratio drops from about **13.4** in the training annotated
stratum to about **3.0** in heldout exposure. At observed heldout muskrat event contexts,
posterior-mean activity probability is about **0.185**, versus the activity-knockout
baseline of **0.438**.

This supports a bounded working explanation: **a stationary process-specific activity
relationship did not transfer safely across the combined geographic/covariate/source
domain shift**. It does not establish a causal eastward behavioral change, a source or
camera-protocol effect, or that activity is generally irrelevant. The small positive
state gain is also localized and sign-mixed: among event-bearing deployments, **58 have
positive and 70 negative state gains**, with the positive total concentrated in
deployments containing group events.

See
`docs/replication/E4_MICA_SPARSE_FROZEN_RESULT.json`,
`docs/replication/E4_MICA_POSTRESULT_TRANSFER_TAIL_AUDIT.json`,
`docs/replication/E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json`, and
`docs/replication/E4_MICA_SPARSE_RESULT.md`.

The earlier Snapshot Japan, E2, and E3 endpoints remain frozen historical outcomes; E4
does not reopen or overwrite them.


### E4 MICA exact-sparse empirical endpoint — terminal exploratory result

E4 was created after the E3 dense-grid NUTS run hit its frozen 240-minute infrastructure
limit without producing a scientific result. Before any new empirical outcome was
opened, E4 froze and qualified an **exact structural-exposure compaction**. The same
captured MICA response, R5b process graph, three model comparisons, priors, seeds, MCMC
profile, and heldout score definition were then used once.

The exact compaction was the decisive computational change: the one-shot E4 workflow
completed successfully in roughly nine minutes instead of timing out. Because the
removed contexts were unexposed under every retained stream, this is not an approximate
posterior shortcut.

Frozen result:

```text
sampling gate: PASS
divergences: 0
heldout deployment rows: 733 / 733

full score              -7.6929864071241045
activity knockout       -7.053935226712387
activity gain            -0.6390511804117178

state knockout          -7.701377332147147
state gain               +0.008390925023042506
```

The appropriate ecological reading is asymmetric. The activity channel failed to
transfer safely across the strict east extrapolation. Post-result decomposition shows
that **127/128 event-bearing heldout deployments favor the activity knockout** and that
the response is dominated by a source stratum absent from the training annotated
stratum, so geographic extrapolation and source-domain transfer are entangled. The state
channel retained only a small, sign-mixed heldout advantage. These are empirical
predictive results for this endpoint, not evidence of causality, a country/protocol
effect, or universal process importance.

### E2 MICA empirical replication — consumed terminal stop

The separately named E2 replication selected the MICA muskrat dataset response-blind,
passed geometry/header, temporal-integrity, and frozen-climate qualification, and then
opened the biological response exactly once.

The frozen capture stopped **before model fitting** with
`ValueError: deploymentEnd must be after deploymentStart`.

```text
E2 MICA pre-response gates PASS
  -> one-shot full response opened
  -> CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY
  -> model fits = 0
  -> heldout scores = 0
```

This is a data-contract result, not evidence for or against transferred activity/state
information. The response is consumed; repair, candidate switching, response-conditioned
retuning, and a same-program rerun are not authorized.

See `docs/replication/E2_MICA_FULL_RESPONSE_TERMINAL_RESULT.json` and
`docs/replication/E2_MICA_FULL_RESPONSE_RESULT.md`.


### Archived post-R5b methodological lineage

The v0.5-v0.7 methodological branches are not part of the active empirical endpoint.
Their frozen scientific receipts are retained under `docs/validation/` without promoting
the branch runtime code into `main`: v0.5f = **FAIL**, v0.7l = **FAIL**, and v0.7m =
**FAIL**. The v0.7m one-shot authorization was consumed: all 64 replicates / 192 fits
completed with zero divergences, but the preregistered action-classification gate failed.
See `docs/validation/POST_R5B_LINEAGE_STATUS.json` for the machine-readable lineage.


### FIELD1 continuous-map programme — terminal FAIL

The separately named FIELD1 programme tested whether one coherent residual spatial field
could improve mapping, and whether geographic distance, environmental similarity, and
physical barriers could then be qualified as distinct dependence axes.

Its frozen Phase-A result is **FAIL** after 144/144 known-truth shards and 704/704 fits.

The narrow internal `FIELD_PRESENT` flag passed: the distance-structured field M1 beat
the environment-only model in its positive control and did not false-promote in the
no-field control. However, the environmental-similarity and barrier axes did not
separate reliably, the full M4 structure did not qualify, and the sampling guardrail
failed (360 divergences; 0.511 per fit versus a frozen maximum of 0.10).

A post-outcome diagnostic found that edge distance and environmental dissimilarity are
formally full-rank but practically near-collinear in the frozen fixture (edge
correlation about -0.95; projected-precision sensitivity for rho versus gamma about
0.90-0.96). The barrier failure remains only partly explained.

FIELD1 therefore does **not** authorize environmental/barrier mechanism claims, dispersal,
movement, gene-flow, or evolutionary IBD/IBE interpretations, and it is not rerun as a
rescue generation.

See `docs/field/FIELD1_PHASE_A_FROZEN_RESULTS.json`,
`docs/field/FIELD1_TERMINAL_STATUS.md`, and
`docs/field/FIELD1_POSTMORTEM.md`.


### MAP1 coherent-map programme — terminal FAIL

MAP1 asked a narrower question than FIELD1: whether one **fixed** geography-coherent
residual field improves held-out mapping beyond both an environment-only model and an
amplitude-matched exchangeable residual field, without estimating distance, environment,
or barrier covariance axes.

All **48/48** confirmatory replicates and **144/144** fits completed. The sampling
guardrail passed (12 divergences; 0.0833 per fit <= 0.10), and the coherent field was
strongly useful in the positive coherent world P1:

- BC - B0: positive-gain rate **0.8125**, mean gain **+1.3885**;
- BC - BX: positive-gain rate **0.8125**, mean gain **+0.07995**.

However, MAP1 failed its predeclared null-calibration controls. In N0, BC exceeded the
allowed material-gain frequency against B0 and BX; in N1, BC also exceeded the allowed
material-gain frequency against BX. Therefore **COHERENT_MAP_SUPPORTED = false**.

The result is not "coherent maps do not work." It is more specific: the frozen coherent
field detects a true coherence signal, but it does not suppress that preference reliably
enough when coherence is absent or exchangeable. MAP1 is terminal and is not eligible
for threshold retuning or a same-program rescue rerun.

See `docs/map/MAP1_FROZEN_RESULTS.json`, `docs/map/MAP1_TERMINAL_STATUS.json`, and
`docs/map/MAP1_RESULT.md`.



### AMAP1 adaptive-map programme — terminal FAIL

AMAP1 asked a different question from FIELD1 and MAP1: whether one residual field could
adapt continuously between exchangeable and fixed geographic coherence and stay close to
the truth-aligned oracle across structural uncertainty.

The frozen result is **FAIL** after **144/144** confirmatory replicates and **384/384**
fits. All six TX/TC oracle-detectability firewalls passed, and sampling was stable
(3 divergences; 0.0078 per fit <= 0.10). The failure was the primary low-regret target:
**all 9/9 geometry x truth worlds exceeded the frozen material-regret-rate maximum of
0.25**. The worst rate was 0.75 in G2_TX.

Therefore `LOW_REGRET_MAP_SUPPORTED = false`. AMAP1 does not authorize a claim that an
adaptive covariance mixture provides robust low-regret maps, and it does not support any
coherence, dispersal, connectivity, migration, or gene-flow interpretation.

See `docs/map/AMAP1_FROZEN_RESULTS.json`,
`docs/map/AMAP1_TERMINAL_STATUS.json`, and `docs/map/AMAP1_RESULT.md`.


### Frozen ODSP transfer evidence

The active empirical endpoint above is unchanged, but the already-frozen held-out
transfer evidence is now readable from `main` without checking out the historical
v0.6/v0.7 stack.

The machine-readable registry is `ODSP_TRANSFER_SOURCE_REGISTRY_V1.json`.
Its complete evidence ledger contains:

- **4 validated numeric transfer sources**: R5b activity, R5b state, v0.6a
  accessibility, and v0.7b dynamic occupancy;
- **10 explicit exclusions** for gain-only, identification-only, non-nested,
  different-estimand, or scientifically failed sources.

Excluded sources are **unsupported, not zero**. In particular, a scientific FAIL
cannot be silently promoted to a numeric transfer value, and alternative model
representations are not relabelled as nested information.

The transfer layer is archival/downstream only: it does not reopen the first
empirical endpoint, authorize a new model fit, create a global information ladder,
feed the frozen EOG mainline, or authorize N4 survey action.

See `docs/integration/ODSP_TRANSFER_SOURCE_REGISTRY.md` and
`docs/integration/ODSP_TRANSFER_EVIDENCE_LEDGER_V2.md`.


## Seven design principles

1. **One generative graph.** Simulation, likelihood evaluation, prediction, and posterior prediction use the same process and observation modules. In-model known-truth worlds are generated from this graph rather than a separate analysis formula.
2. **Every ecological process has a knockout.** The information ladder is a sequence of explicit process knockouts/additions, with a declared no-effect neutral element for each process.
3. **No data-free process is admitted silently.** `Model.check_design()` requires a declared information path and a computational path `process -> latent channel -> stream`. A process with no path fails closed as design-uninformed.
4. **Identification is measured, not assumed.** Design-path checks, prior-to-posterior contraction, and simulation-based calibration are separate diagnostics. If a data path exists but a target remains unresolved, the claim state is `NotIdentified`.
5. **Validation is process-specific and frozen before held-out outcomes.** Transfer designs belong under `validate/`; they are not post-hoc model-selection conveniences.
6. **Interactions act through partner latent fields.** Interaction processes may depend on another taxon's inferred intensity/state/activity field, not raw partner records used as ecological covariates.
7. **Diversity, networks, and maps are posterior-derived outputs.** They live under `summarize/` and are never generative inputs.

## Generative architecture

```text
esdm/
  domain/        space, time, ecological state declarations
  process/       ecological contributions to latent intensity, activity, and state
  observe/       observation effort and record-generation streams
  model/         composition, design checks, inference backends
  identify/      contraction and SBC diagnostics
  validate/      held-out/process-ladder validation
  claims/        typed claim states and bounded interpretation
  simulate/      in-model and deliberately misspecified worlds
  summarize/     posterior/downstream diversity and network summaries
```

The older Phase-1/2/3 implementation is retained, but its canonical role changes:

```text
old diversity/network primitives  -> summarize/
old transfer ceilings             -> validate/
old authorization/process/worlds  -> claims/
```

Compatibility imports remain temporarily while the architecture is migrated.

## v0.3 generative kernel

### Domain

```python
from esdm.domain import Grid

grid = Grid(
    space=("site_a", "site_b"),
    doy=(1, 8, 15),
    hour=(0, 12),
)
```

The first implementation uses an explicit discrete `Space × DayOfYear × Hour` domain. State declarations use `StateSpace`, `Partition`, and `RefinementChain` so occurrence can later be refined into phenological, behavioural, life-stage, resource-use, or other ecological states without changing the domain contract.

### Ecological process

```python
from esdm.process import LinearSuitability

suitability = LinearSuitability(
    covariates=("temperature",),
    intercept_parameter="alpha",
    coefficient_parameters={"temperature": "beta_temp"},
)
```

A process contributes additively to ecological log intensity. `LinearSuitability.knockout()` returns an explicit no-effect process with

```text
log contribution = 0
```

rather than deleting a term by convention.

### Observation process

```python
from esdm.observe import EffortField, PresenceOnly

effort = EffortField({
    ("site_a", 1, 0): 1.0,
    ("site_b", 1, 0): 4.0,
})

records = PresenceOnly(
    "community_records",
    effort=effort,
    informs=frozenset({"suitability"}),
    targets=frozenset({"taxon_a"}),
)
```

For the v0.3 presence-only stream,

```text
lambda_record
  = lambda_ecological
  × effort
  × detection
```

and counts are Poisson. Effort is observation-process information, not ecological suitability.

### Model composition and design checking

```python
from esdm.model import Model

model = Model(
    domain=grid,
    species={"taxon_a": (suitability,)},
    streams=(records,),
)

report = model.check_design()
```

`check_design()` does not treat `Stream.informs` as proof of identification. It verifies only that a declared process has a static path through a latent channel actually consumed by a stream. Posterior identification is assessed later.

The model also carries a latent-taxon dependency graph and rejects cycles. Directed interaction modules are not implemented in v0.3, but the DAG constraint is already part of the composition contract so unsupported reciprocal dependencies fail closed.

### Same graph for simulation, likelihood, and NumPyro

```python
from esdm.simulate import simulate_presence_only

generated = simulate_presence_only(
    model,
    theta={"taxon_a": {"alpha": 0.0, "beta_temp": 1.0}},
    covariates={...},
    seed=1,
)

log_lik = model.log_likelihood(
    generated.counts,
    theta={"taxon_a": {"alpha": 0.0, "beta_temp": 1.0}},
    covariates={...},
)
```

Simulation calls the same latent-field construction and observation-stream mathematics used by deterministic likelihoods and the optional NumPyro backend. In v0.4 these stream calculations are exposed as backend-neutral Poisson observation blocks, so simulation, inference, and identification do not maintain separate copies of the ecological/observation equations.

## v0.4 state/activity core — semi-synthetic promotion complete

The v0.4 core refines ecological availability into separate conditional activity and
categorical state channels:

```text
ecological intensity / availability
  -> activity probability | available
  -> state probabilities | active, available
  -> observation process
  -> data
```

The implementation is factorized rather than treating every record as the same latent
quantity. `LinearActivity` contributes an activity logit, while `LinearState` uses
reference-coded state logits followed by a softmax. A species with only
`LinearSuitability` retains the v0.3.2 intensity-only behavior.

`PresenceOnly` deliberately remains an intensity-only stream:

```text
lambda_presence
  = exp(log_intensity)
  × effort
  × detection
```

Adding an activity or state process to the same species does not silently alter this rate.

`StateAnnotatedCount` explicitly consumes all three ecological channels. For state
`s` in context `c`:

```text
lambda_annotated[c, s]
  = exp(log_intensity[c])
  × activity[c]
  × P(state=s | active, available, c)
  × effort[c]
  × detection
```

Known constant detection and an unknown global logit-detection intercept are represented
as observation-process objects, not ecological parameters. Exact JAX Jacobian diagnostics
therefore can refuse designs where activity and detection are structurally inseparable.
The required negative control is an intercept-only activity process observed through
unknown global detection; activity intercept and detection intercept are returned as
`NotIdentified`, rather than being separated by prior regularization.

Observation streams expose shared `PoissonObservationBlock` objects. The same blocks are
used by generic in-model simulation, NumPyro likelihood construction, posterior
observation-rate derivation, structural identification, and JAX trace-size diagnostics.
State/activity parameter-dependent arithmetic remains array-first, including the
2,880-context trace-scaling regression.

The v0.4 core has now passed its frozen semi-synthetic promotion programme. R5a passed
the hard identification gate after adding a direct conditional state-composition
calibration stream, and R5b then passed 16-replicate recovery and east-heldout transfer
with 48 total fits and zero divergences.

The promoted observation contract includes `StateCompositionCount`, which consumes only
the latent state-composition channel and has zero held-out exposure in the frozen R5b
benchmark. The promotion claim is therefore bounded: v0.4 is validated under its declared
semi-synthetic known-truth programme, not established as an empirically correct model for
any biological system.

## NumPyro inference backend

The optional NumPyro backend fits the current generative graph with NUTS/MCMC.

```bash
python -m pip install -e ".[inference]"
```

Core `esdm` remains importable on Python 3.10. The current NumPyro dependency requires Python 3.11+, so inference tests run only on supported Python versions while the rest of the package retains the broader core compatibility.

```python
from esdm.model.backend_numpyro import fit_numpyro

fit = fit_numpyro(
    model,
    data,
    covariates,
    rng_seed=1,
    num_warmup=500,
    num_samples=500,
)
```

The backend translates backend-neutral `PriorSpec` declarations into NumPyro distributions, then calls the existing latent-channel graph and stream observation blocks. `posterior_latent_fields(...)` derives intensity/activity/state fields, `posterior_observation_rates(...)` derives all observation-block rates, and `posterior_record_rates(...)` remains the PresenceOnly compatibility view.

## Identification and simulation-based calibration

`esdm.identify` keeps several questions separate:

- does a parameter have a design path to data?
- did its posterior contract relative to the prior?
- is Bayesian inference calibrated under the declared model?
- is the result robust to ecological or observation-process misspecification?

The first three do not imply the fourth.

`run_numpyro_sbc(...)` performs

```text
prior draw
 -> same generative graph
 -> in-model simulation
 -> NumPyro fit
 -> posterior rank of the true parameter
```

so SBC does not use a separate known-truth formula. `simulate/misspecified.py` is deliberately separate: misspecified effort, hidden drivers, omitted processes, and other out-of-model worlds must not be relabelled as SBC.

Claim status is typed separately from interaction evidence tier:

```text
DesignUninformed
Untested
NotIdentified
NotSupported
Supported
```

The evidence tier remains:

```text
COAVAILABLE
STATE_COMPATIBLE
PREDICTIVE_DEPENDENCE
REALIZED
FUNCTIONAL
CAUSAL
```

A target can therefore be `NotIdentified × REALIZED`, for example, instead of being forced into a numerical mechanism estimate.

## Application scope: community ecology, not one interaction system

No biological interaction family is privileged by the runtime model. The intended scope includes, among others:

- competition and resource partitioning;
- predator–prey and other consumer–resource systems;
- host–parasite, host–pathogen, and vector-mediated systems;
- herbivory;
- facilitation and nurse/benefactor effects;
- ecosystem engineering and habitat-mediated effects;
- mutualisms;
- seed dispersal and transport interactions;
- commensal, nesting, and structure-dependent associations;
- pollination as one example among these.

Domain labels never determine mechanism. The generic pattern is

```text
focal latent field
+ partner latent field
+ process/state compatibility
+ observation stream
 -> posterior process contribution
 -> evidence-tiered claim
```

Raw partner observations are not substituted for the partner latent ecological field when that latent field is the intended biological quantity.

See [`docs/APPLICATION_SCOPE.md`](docs/APPLICATION_SCOPE.md) for the broader benchmark universe.

## In-model versus misspecified worlds

`simulate/in_model.py` is reserved for SBC and other checks where the fitted model contains the data-generating process.

`simulate/misspecified.py` is explicitly separate. The first negative control shows that replacing heterogeneous sampling effort with an incorrect constant shifts the expected fitted ecological intercept. Passing SBC therefore cannot be used to hide observation-process misspecification.

Future generic benchmarks should cover measured and hidden shared-environment nulls, state/resource partitioning, antagonistic and beneficial directed effects, consumer-resource lags, host-parasite dependence with imperfect detection, habitat engineering, network rewiring, and intentionally unsupported reciprocal interactions.

## Downstream summaries

The earlier state-resolved diversity and interaction-network work remains available canonically from:

```python
from esdm.summarize import alpha_diversity_q1, network_beta_q1
```

These are downstream/posterior summary operators. `InteractionNetworkDistribution` is retained during migration but is no longer the conceptual entry point to the model.

Likewise, transfer ceilings are downstream validation:

```python
from esdm.validate import point_transfer_ceiling
```

and authorization / set-valued process explanations / finite-world contraction are claim-governance tools under:

```python
from esdm.claims import ...
```

## Version plan

| Version | New generative process | Promotion gate |
| --- | --- | --- |
| v0.3 | domain + suitability + effort-aware presence-only + NumPyro + simulate + identify + claims | shared generation/likelihood/inference code; large SBC calibration study; knockout recovery; effort-misspecification negative control; semi-synthetic real-geometry benchmark |
| v0.4 | ecological state + activity + annotation streams + direct state-composition calibration | **PROMOTED (semi-synthetic)**: hard identification, 13-target recovery, east-heldout activity/state transfer, refusal controls; unresolved detection remains bounded/`NotIdentified` |
| v0.5 | directed biotic interaction through partner latent fields + interaction-event streams | false interaction/kernel-shift control under state-only and hidden-common-driver worlds; evidence tier cannot rise without corresponding observed endpoint |
| v0.6 | movement/accessibility | distinguish unsuitable from inaccessible only when data support it; otherwise return `NotIdentified` |

## Existing research-programme provenance

The downstream claim/validation semantics remain bounded by their source projects:

- ODSP -> ordered information ladders and transfer semantics;
- SDMR -> set-valued process support and independent-evidence refinement;
- 284b -> authorization of negative evidence;
- EOG -> finite declared-world compatibility/contraction;
- ACSP -> bounded candidate-set semantics for follow-up observation.

See [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

## Explicit non-claims

The promoted v0.4 core does **not** claim:

- empirical correctness merely because the frozen semi-synthetic promotion gate passed;
- scientific support from structural identification or posterior contraction alone;
- empirical biological validity from in-model or semi-synthetic validation;
- causal interaction from co-occurrence, residual association, predictive gain, or rewiring;
- a directed biotic-interaction process yet;
- a bidirectional/fixed-point interaction model;
- movement/accessibility inference;
- a universal SDM/JSDM replacement;
- validation for any one interaction family merely because it appears as an example.

## Development

Core only:

```bash
python -m pip install -e .
python -m pytest -q
```

Development plus NumPyro where supported:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

CI runs the core suite on Python 3.10 and the NumPyro-enabled suite on Python 3.11 and 3.12.
