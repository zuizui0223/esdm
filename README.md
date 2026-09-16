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
  process/       ecological contributions to latent intensity
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

Simulation calls the same latent-field construction and the same stream `expected_rates()` code used by the ordinary likelihood and by the optional NumPyro backend. The ecological equation is not duplicated inside the backend.

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

The backend translates backend-neutral `PriorSpec` declarations into NumPyro distributions, then calls the existing process graph and observation-rate code. `posterior_record_rates(...)` derives posterior record-rate fields through the same graph.

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
| v0.4 | ecological state + activity + annotation streams | state/activity recovery and frozen cross-stream transfer; unresolved detection leaves bounded/`NotIdentified` output |
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

Current v0.3 does **not** claim:

- completion of the v0.3 promotion gate from the current small SBC smoke test;
- identification from contraction alone;
- ecological robustness from in-model SBC alone;
- causal interaction from co-occurrence, residual association, predictive gain, or rewiring;
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
