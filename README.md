# esdm

`esdm` develops a **process-based ecological state distribution model** for community ecology. Ordinary species-distribution modelling is treated as a low-resolution special case in which the only explicit state is occurrence and the only ecological process is environmental suitability.

The central object is now a generative graph:

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

1. **One generative graph.** Simulation, likelihood evaluation, prediction, and later posterior prediction use the same process and observation modules. Known-truth in-model worlds are generated from this graph rather than a separate analysis formula.
2. **Every ecological process has a knockout.** The information ladder is a sequence of explicit process knockouts/additions, with a declared no-effect neutral element for each process.
3. **No data-free process is admitted silently.** `Model.check_design()` requires a declared information path *and* a computational path `process -> latent channel -> stream`. A process with no path fails closed as design-uninformed.
4. **Identification is measured, not assumed.** Design-path checks, prior-to-posterior contraction, and simulation-based calibration are separate diagnostics. If the data path exists but the posterior does not identify a target, the claim state is `NotIdentified`.
5. **Validation is process-specific and frozen before held-out outcomes.** Transfer designs belong under `validate/`; they are not post-hoc model-selection conveniences.
6. **Interactions act through partner latent fields.** Later interaction processes may depend on another species' inferred intensity/state/activity field, not raw partner observation records as covariates.
7. **Diversity, networks, and maps are posterior-derived outputs.** They live under `summarize/` and are never generative inputs.

## Generative architecture

```text
esdm/
  domain/        space, time, ecological state declarations
  process/       ecological contributions to latent intensity
  observe/       observation effort and record-generation streams
  model/         composition, design checks, likelihood construction
  identify/      contraction and SBC diagnostics
  validate/      held-out/process-ladder validation
  claims/        typed claim states and bounded interpretation
  simulate/      in-model and deliberately misspecified worlds
  summarize/     posterior/downstream diversity and network summaries
```

The older Phase-1/2/3 implementation is retained, but its role changes:

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

The first implementation uses an explicit discrete `Space × DayOfYear × Hour` domain. State declarations use `StateSpace`, `Partition`, and `RefinementChain` so occurrence can later be refined into phenostage/activity states without changing the domain contract.

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
    "inat",
    effort=effort,
    informs=frozenset({"suitability"}),
)
```

For the v0.3 presence-only stream,

```text
log lambda_record
  = log lambda_ecological
  + log effort
  + log detection
```

and counts are Poisson. Effort is observation-process information, not ecological suitability.

### Model composition and design checking

```python
from esdm.model import Model

model = Model(
    domain=grid,
    species={"species_a": (suitability,)},
    streams=(records,),
)

report = model.check_design()
```

`check_design()` does not treat `Stream.informs` as proof of identification. It only verifies that a declared process has a static path through a latent channel actually consumed by a stream. Posterior identification is assessed later.

The model also carries a latent-species dependency graph and rejects cycles. Directed interaction modules are not implemented in v0.3, but the DAG constraint is already part of the composition contract so later mutual dependencies fail closed.

### Same graph for simulation and likelihood

```python
from esdm.simulate import simulate_presence_only

generated = simulate_presence_only(
    model,
    theta={"species_a": {"alpha": 0.0, "beta_temp": 1.0}},
    covariates={...},
    seed=1,
)

log_lik = model.log_likelihood(
    generated.counts,
    theta={"species_a": {"alpha": 0.0, "beta_temp": 1.0}},
    covariates={...},
)
```

Simulation calls the same latent-field construction and the same stream `expected_rates()` code used by the likelihood. This is the v0.3 implementation of the one-generative-graph principle.

## Identification

`esdm.identify` currently provides two intentionally separate diagnostics:

- prior-to-posterior contraction;
- SBC rank-histogram calibration.

Contraction can support an identification claim only relative to a declared threshold. SBC checks calibration **under the declared generative model**; it does not establish robustness to ecological misspecification.

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

A target can therefore be, for example, `NotIdentified × REALIZED` rather than being forced into a numeric estimate.

## In-model versus misspecified worlds

`simulate/in_model.py` is reserved for SBC and other checks where the fitted model contains the data-generating process.

`simulate/misspecified.py` is explicitly separate. The first negative control shows that replacing heterogeneous sampling effort with an incorrect constant shifts the expected fitted ecological intercept. Passing SBC therefore cannot be used to hide observation-process misspecification.

## Downstream summaries

The earlier state-resolved diversity and interaction-network work remains available canonically from:

```python
from esdm.summarize import alpha_diversity_q1, network_beta_q1
```

These are now interpreted as downstream/posterior summary operators. `InteractionNetworkDistribution` is retained during migration but is no longer the conceptual entry point to the model.

Likewise, transfer ceilings are downstream validation:

```python
from esdm.validate import point_transfer_ceiling
```

and Phase-3 authorization / set-valued process explanations / finite-world contraction are claim-governance tools under:

```python
from esdm.claims import ...
```

## Version plan

| Version | New generative process | Promotion gate |
| --- | --- | --- |
| v0.3 | domain + suitability + effort-aware presence-only + simulate + identify + claims | shared generation/likelihood code; knockout recovery; SBC calibration; effort-misspecification negative control |
| v0.4 | ecological state + activity + annotation streams | state/activity recovery and frozen cross-stream transfer; unresolved detection leaves bounded/NotIdentified output |
| v0.5 | directed biotic interaction through partner latent fields + camera events | false interaction/kernel-shift control under state-only and hidden-common-driver worlds; evidence tier cannot rise without realized stream |
| v0.6 | movement/accessibility | distinguish unsuitable from inaccessible only when data support it; otherwise return `NotIdentified` |

## Pollination and other interactions

Pollination remains **one example only**. The core model is intended for generic community ecology: competition, mutualism, predation, host-parasite association, facilitation, pollination, and other directed biotic dependencies all use the same process/stream contracts.

The v0.5 interaction design will act through partner latent fields rather than partner records.

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

- a completed NumPyro fitting backend;
- identification from contraction alone;
- ecological robustness from in-model SBC alone;
- causal interaction from co-occurrence, residual association, predictive gain, or rewiring;
- a bidirectional/fixed-point interaction model;
- movement/accessibility inference;
- a universal SDM/JSDM replacement;
- pollination-specific validation.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

CI runs the full suite on Python 3.10, 3.11, and 3.12.
