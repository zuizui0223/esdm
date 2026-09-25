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

## v0.5 directed interaction evidence core — bounded semi-synthetic promotion complete

The v0.5 core adds directed biotic dependence through partner latent ecological fields.

`PartnerIntensityEffect` contributes a signed effect to focal log intensity from a
source species latent field. Species are evaluated in topological order of the declared
latent-species dependency DAG, so unsupported reciprocal cycles still fail closed.

The validation programme deliberately separated four questions:

1. is the directed partner coefficient identifiable and recoverable when the declared
   model is correct?
2. can measured shared environmental response be distinguished from a partner effect?
3. can an omitted common driver create a false partner coefficient and false predictive
   gain?
4. can claim authorization remain correct even when that coefficient is wrong?

The answer sequence was:

- **v0.5a PASS**: true `beta_partner=+0.75` was recovered with negligible mean bias and
  positive held-out knockout gain in 16/16 fresh replicates; a measured-shared-environment
  `beta=0` null met the frozen refusal gate.
- **v0.5b FAIL**: an omitted common driver produced a large false partner coefficient
  (mean fitted beta about +0.985), nonzero intervals in 16/16 replicates, and strong
  held-out predictive gain in 16/16 replicates.
- **v0.5c** therefore hard-caps model-only interaction evidence at
  `PREDICTIVE_DEPENDENCE`. REALIZED requires an independently authorized pair-specific
  event; FUNCTIONAL and CAUSAL require additional endpoint/intervention evidence.
- **v0.5d** adds `PairEventCount`, a generative pair-specific realized-event observation
  stream over source/target latent availability.
- **v0.5e PASS** validates the separation: hidden-driver false beta + no events stayed
  PREDICTIVE_DEPENDENCE in 16/16; beta=0 + observed events reached REALIZED in 16/16;
  beta>0 + observed events also reached REALIZED in 16/16; no replicate self-promoted to
  FUNCTIONAL or CAUSAL.

The promoted v0.5 contract is therefore **bounded interaction evidence**, not causal
interaction identification. Strong model dependence and predictive gain may still be
wrong under hidden confounding; the runtime claim layer must respect the independent
evidence tier.

## v0.6 static accessibility core — bounded semi-synthetic promotion complete

The v0.6 core separates potential ecological intensity from accessibility.

`LinearAccessibility` contributes a bounded accessibility probability through
`log_accessibility = log(sigmoid(eta))`. Its explicit knockout sets
`accessibility = 1`, representing no accessibility limitation.

Two new observation contracts keep the distinction explicit:

`AccessiblePresenceOnly`

```text
lambda_joint
  = exp(log_intensity)
  × accessibility
  × effort
  × detection
```

and direct `AccessibilityCount`

```text
lambda_access
  = accessibility
  × effort
  × detection
```

The existing `PresenceOnly` stream remains intensity-only.

The frozen v0.6a and v0.6b programmes establish a more precise identification boundary.

With only an intercept-only joint occurrence endpoint, suitability and accessibility were
both returned as `NotIdentified`: the full Jacobian rank remained 1 when either target
was removed, and target-SD proxies exceeded 4,000.

However, v0.6b showed that joint occurrence is not universally structurally
non-identifying. With distinct non-collinear habitat/distance predictors and the declared
linear-intensity/logistic-accessibility forms, all four parameters were locally
structurally identified from the joint occurrence stream alone (rank **4 -> 3** for each
target). That separation was mostly **practically weak**: target-SD proxies were **0.495**
for the suitability intercept, **1.475** for the accessibility intercept, and **0.910**
for the accessibility slope; only the habitat slope passed the frozen 0.25 practical
threshold (**0.110**).

Direct accessibility calibration in the 24 training contexts changed that picture. All
four targets became both structurally and practically identified, with target-SD proxies
**0.106–0.198**. Across 16 fresh replicates, absolute mean bias stayed below **0.056**,
90% coverage was at least **0.875**, and there were zero divergences.

Direct accessibility exposure was exactly zero in all 12 held-out contexts. Even so, the
full model beat the accessibility knockout in **16/16** replicates on held-out joint
occurrence, with mean log predictive gain **+0.36244** and minimum gain **+0.03242**.

The promoted v0.6 claim is therefore bounded:

> joint occurrence may mathematically separate suitability and accessibility when strong
> covariate/link-function structure supplies the separation, but that structural
> identification can be assumption-driven and practically weak. Independent
> accessibility observations provide a separate information channel that made the frozen
> decomposition practically estimable, recoverable, and transferable.

Structural identification from a joint endpoint is not itself independent ecological
evidence of accessibility. This remains a static accessibility layer, not a
movement-kernel or dynamic colonization model.

## v0.7 marginal colonization-extinction core — bounded semi-synthetic promotion complete

v0.7 adds a dynamic occupancy layer rather than stretching static accessibility into a
temporal claim. `ColonizationExtinctionOccupancy` emits a marginal occupancy probability
`psi` for each declared context. Within each spatial unit, contexts are ordered by
`(doy, hour)` and updated by

```text
psi_t
  = psi_(t-1) × (1 - epsilon_t)
  + (1 - psi_(t-1)) × gamma_t
```

where colonization `gamma` and extinction `epsilon` are logistic functions of declared
destination-context covariates. The explicit knockout sets `occupancy = 1`.

`OccupiedPresenceOnly` consumes the new channel without changing the older streams:

```text
lambda_occupied
  = exp(log_intensity)
  × occupancy
  × effort
  × detection
```

v0.7a established the first identification boundary. In the frozen intercept-only system,
eight joint-occurrence time points still supplied only rank **3** for four free quantities
(`alpha`, initial occupancy, colonization, extinction), so every target remained
`NotIdentified`. Adding direct `OccupancyCount` at only the first four contexts restored
rank **4 -> 3** for every target. Practical target-SD proxies were **0.0415**, **0.0869**,
**0.1032**, and **0.2325** for alpha, initial occupancy, colonization, and extinction,
respectively.

v0.7b then passed the frozen replicated recovery/transfer programme. The model was trained
with joint occurrence at contexts 1–8 and direct occupancy only at contexts 1–4, then
scored on joint occurrence at contexts 9–12 with zero held-out occupancy calibration.
Across **16 fresh replicates / 32 fits**, absolute mean bias was at most **0.0279**, 90%
coverage was at least **0.875**, and there were **0 divergences**. The full dynamic model
beat its explicit occupancy knockout in **16/16** held-out replicates, with mean gain
**+8.3118 nats/context** and minimum gain **+5.1125**.

v0.7c then tested the main alternative explanation directly. The recursive model was
compared against a lower-dimensional, fully identifiable memoryless occupancy model with
an intercept plus frozen linear time trend. Both candidates received exactly the same
joint occurrence and direct occupancy calibration. The static comparator itself passed
the exact-JAX structural/practical gate (rank **3/3**, condition number **6.89**, target-SD
proxies **0.067–0.114**).

Across **16 fresh paired replicates / 32 fits**, the recursive dynamic model beat the
matched static occupancy model in **15/16 = 0.9375** replicates. Mean held-out gain was
**+3.3212 nats/context**, the single negative replicate was only **−0.1168**, and there
were **0 divergences**.

The promoted v0.7 claim is therefore bounded but stronger:

> Repeated joint occurrence through time does not by itself guarantee identification of
> colonization/extinction dynamics. A small amount of process-specific occupancy-scale
> evidence can anchor the missing scale. Under the frozen dynamic world, the recovered
> recursive occupancy representation then predicts later occurrence better than a
> simpler, fully estimable memoryless occupancy trend receiving the same observations.

Thus the v0.7b late-time gain is not explained merely by adding any occupancy layer;
temporal dependence carries predictive information in the frozen recursive world.

`psi` remains a **marginal occupancy probability**, not a realized binary occupancy
history. The current core applies one transition per adjacent declared sampling context
regardless of the physical time gap. It does not identify realized transition events,
movement paths, dispersal kernels, connectivity, source-sink dynamics, rescue effects, or
causal movement limitation. Empirical biological validation remains outside the current
promotion.

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
| v0.5 | directed partner-latent effects + pair-event streams + evidence-tier guard | **PROMOTED (bounded semi-synthetic)**: true directed effect recovery; measured-shared null refusal; hidden-driver failure establishes claim ceiling; pair-event evidence separates PREDICTIVE_DEPENDENCE from REALIZED; FUNCTIONAL/CAUSAL remain gated |
| v0.6 | static accessibility + accessibility-aware occurrence + direct accessibility calibration | **PROMOTED (bounded semi-synthetic)**: intercept-only joint product is `NotIdentified`; structured joint-only can be locally identified but was practically weak for 3/4 targets; direct accessibility information yielded practical four-target recovery and 16/16 held-out transfer with zero held-out accessibility exposure |
| v0.7 | marginal colonization/extinction occupancy + direct occupancy calibration + occupancy-conditioned occurrence | **PROMOTED (bounded semi-synthetic)**: joint-only temporal trajectory remains rank-deficient (3/4); four-context direct occupancy calibration restores four-target identification; 16-replicate recovery passes and late joint-occurrence transfer beats the occupancy knockout 16/16 with zero held-out occupancy calibration |

## Existing research-programme provenance

The downstream claim/validation semantics remain bounded by their source projects:

- ODSP -> ordered information ladders and transfer semantics;
- SDMR -> set-valued process support and independent-evidence refinement;
- 284b -> authorization of negative evidence;
- EOG -> finite declared-world compatibility/contraction;
- ACSP -> bounded candidate-set semantics for follow-up observation.

See [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

## Explicit non-claims

The promoted v0.4/v0.5/v0.6/v0.7 core does **not** claim:

- empirical correctness merely because the frozen semi-synthetic promotion gate passed;
- scientific support from structural identification or posterior contraction alone;
- empirical biological validity from in-model or semi-synthetic validation;
- causal interaction from co-occurrence, residual association, predictive gain, partner coefficients, or knockout gain;
- robustness of partner coefficients to arbitrary hidden common drivers;
- FUNCTIONAL interaction from realized pair events alone;
- CAUSAL interaction without explicit intervention evidence;
- a bidirectional/fixed-point interaction model;
- movement kernels, path connectivity, resistance surfaces, dynamic colonization/extinction, or source-sink inference from the static v0.6 accessibility layer;
- realized occupancy histories, observed transition events, movement kernels, path connectivity, source-sink dynamics, or causal movement limitation from the marginal v0.7 occupancy recursion;
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
