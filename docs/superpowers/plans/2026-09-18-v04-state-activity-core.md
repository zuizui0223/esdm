# v0.4 State and Activity Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add factorized ecological intensity, conditional activity, and categorical state channels plus state-annotated count observations while preserving v0.3.2 semantics and identifiability safeguards.

**Architecture:** Keep `log_intensity` as the existing ecological channel, add additive activity-logit and reference-coded state-logit channels, and derive probabilities only after process contributions are combined. Observation streams expose generic Poisson observation blocks so deterministic likelihoods, simulation, NumPyro, and structural-identification diagnostics all consume the same stream mathematics.

**Tech Stack:** Python 3.10+ core, dataclasses, standard library, pytest, optional JAX/NumPyro on Python 3.11+, GitHub Actions matrix 3.10/3.11/3.12.

**Spec:** `docs/superpowers/specs/2026-09-18-v04-state-activity-core-design.md`

## Global Constraints

- Preserve exact v0.3.2 `PresenceOnly` rate semantics: `exp(log_intensity) * effort * detection`.
- Existing v0.3 models run without activity or state process declarations.
- v0.4 supports exactly one categorical state axis per species and uses the single semantic channel name `state`.
- Activity is conditional on ecological availability and is represented by an additive logit predictor.
- State is conditional on active/available ecological units and is represented by reference-coded logits followed by softmax.
- Reference-state parameters are not free parameters and must not appear as NumPyro sample sites.
- Unknown global detection remains an observation-process parameter and must not be promoted to ecological activity.
- Simulation, deterministic likelihood, NumPyro inference, and structural-identification diagnostics reuse the same latent-channel and observation-block code.
- Parameter-dependent JAX arithmetic remains array-first; no Python loop over contexts may be introduced into a traced computation.
- Explicit non-empty stream targets and static zero-exposure fail-closed semantics remain unchanged.
- Python 3.10 remains core-compatible; NumPyro execution is required only where the optional backend is supported.
- Do not modify `docs/validation/V031_*` or `docs/validation/V032_*`.
- This PR does not make a v0.4 promotion claim.

---

## File map

### New files

- `src/esdm/process/activity.py` — activity-logit process and knockout.
- `src/esdm/process/state.py` — reference-coded categorical state process and knockout.
- `src/esdm/observe/blocks.py` — backend-neutral Poisson observation block.
- `src/esdm/observe/detection.py` — known and unknown global detection models.
- `src/esdm/observe/state_annotated.py` — state-labelled count observation stream.
- `tests/test_v04_process_contract.py` — generic process contribution compatibility.
- `tests/test_v04_activity_process.py` — activity process and knockout.
- `tests/test_v04_state_process.py` — state parameterization and knockout.
- `tests/test_v04_latent_channels.py` — scalar/array channel composition and design checks.
- `tests/test_v04_observation_blocks.py` — generic Poisson block and PresenceOnly compatibility.
- `tests/test_v04_state_annotated.py` — annotated-rate semantics and fail-closed behavior.
- `tests/test_v04_simulation.py` — generic simulation and compatibility wrapper.
- `tests/test_v04_numpyro.py` — annotated NumPyro path and posterior fields.
- `tests/test_v04_identifiability.py` — positive known-detection and negative unknown-detection structural controls.
- `tests/test_v04_jax_scaling.py` — trace-scaling regression with activity/state channels.

### Modified files

- `src/esdm/process/base.py` — generic contribution container/protocol.
- `src/esdm/process/suitability.py` — contribution API compatibility shims.
- `src/esdm/process/__init__.py` — public activity/state exports.
- `src/esdm/model/arrays.py` — categorical context arrays and multi-channel latent arrays.
- `src/esdm/model/compose.py` — channel aggregation and channel-path design checks.
- `src/esdm/model/__init__.py` — public latent container exports if needed.
- `src/esdm/observe/presence_only.py` — expose the generic Poisson block without changing public rates.
- `src/esdm/observe/__init__.py` — public block/detection/annotated-stream exports.
- `src/esdm/simulate/in_model.py` — generic stream simulation plus `simulate_presence_only` wrapper.
- `src/esdm/simulate/__init__.py` — generic simulator export.
- `src/esdm/model/backend_numpyro.py` — consume generic observation blocks and expose posterior latent fields/rates.
- `src/esdm/identify/design_rank.py` — obtain observation vectors from stream blocks rather than PresenceOnly-specific rate calls.
- `src/esdm/benchmarks/v032_array_trace.py` — generalize trace helper if required by the v0.4 scaling test.
- `src/esdm/benchmarks/__init__.py` — export any generalized trace helper.
- `README.md` — document implemented v0.4 core without claiming promotion.

---

### Task 1: Generic process-contribution contract with unchanged suitability behavior

**Files:**
- Create: `tests/test_v04_process_contract.py`
- Modify: `src/esdm/process/base.py`
- Modify: `src/esdm/process/suitability.py`
- Modify: `src/esdm/process/__init__.py`

**Interfaces:**
- Consumes: existing `Context`, `PriorSpec`, `LinearSuitability`, `NeutralSuitability`.
- Produces:
  - `ProcessContribution(channel: str, values: object, labels: tuple[str, ...] = ())`
  - `Process.contribution(ctx, theta, covariates, latent_fields=None) -> ProcessContribution`
  - `Process.contribution_array(keys, theta, covariates, *, array_module, latent_fields=None) -> ProcessContribution`
  - Existing `log_intensity(...)` and `log_intensity_array(...)` remain callable on suitability classes.

- [ ] **Step 1: Write the failing process-contract tests**

Create `tests/test_v04_process_contract.py`:

```python
import math

from esdm.domain import Context
from esdm.process import LinearSuitability, ProcessContribution


def test_suitability_exposes_generic_contribution_without_changing_value():
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    ctx = Context("s1", 1, 0)
    theta = {"intercept": math.log(2.0), "beta_x": math.log(3.0)}
    covariates = {"x": 1.0}

    contribution = process.contribution(ctx, theta, covariates)

    assert isinstance(contribution, ProcessContribution)
    assert contribution.channel == "log_intensity"
    assert contribution.labels == ()
    assert contribution.values == process.log_intensity(ctx, theta, covariates)


def test_suitability_array_contribution_preserves_context_axis():
    import numpy as np

    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    keys = (("a", 1, 0), ("b", 1, 0))
    theta = {"intercept": 0.2, "beta_x": 0.5}
    covariates = {"x": np.asarray([-1.0, 2.0])}

    contribution = process.contribution_array(
        keys,
        theta,
        covariates,
        array_module=np,
    )

    assert contribution.channel == "log_intensity"
    assert contribution.labels == ()
    np.testing.assert_allclose(contribution.values, [-0.3, 1.2])
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m pytest tests/test_v04_process_contract.py -q
```

Expected: collection/import failure because `ProcessContribution` and generic contribution methods do not exist.

- [ ] **Step 3: Add the generic contribution type and protocol methods**

In `src/esdm/process/base.py`, add:

```python
@dataclass(frozen=True, slots=True)
class ProcessContribution:
    channel: str
    values: object
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        channel = str(self.channel).strip()
        labels = tuple(str(label).strip() for label in self.labels)
        if not channel:
            raise ValueError("contribution channel must be non-empty")
        if any(not label for label in labels) or len(set(labels)) != len(labels):
            raise ValueError("contribution labels must be unique non-empty strings")
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "labels", labels)
```

Extend the `Process` protocol with `contribution` and `contribution_array`. Keep the existing suitability-specific methods during v0.4 compatibility.

In `LinearSuitability` and `NeutralSuitability`, implement:

```python
def contribution(self, ctx, theta, covariates, latent_fields=None):
    return ProcessContribution(
        self.output_channel,
        self.log_intensity(ctx, theta, covariates, latent_fields=latent_fields),
    )

def contribution_array(
    self,
    keys,
    theta,
    covariates,
    *,
    array_module,
    latent_fields=None,
):
    return ProcessContribution(
        self.output_channel,
        self.log_intensity_array(
            keys,
            theta,
            covariates,
            array_module=array_module,
            latent_fields=latent_fields,
        ),
    )
```

Export `ProcessContribution` from `esdm.process`.

- [ ] **Step 4: Run focused plus existing suitability/model tests**

Run:

```bash
python -m pytest tests/test_v04_process_contract.py tests/test_generative_model_v03.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/esdm/process/base.py src/esdm/process/suitability.py src/esdm/process/__init__.py tests/test_v04_process_contract.py
git commit -m "refactor: add generic ecological process contributions"
```

---

### Task 2: Add the activity-logit ecological process

**Files:**
- Create: `src/esdm/process/activity.py`
- Create: `tests/test_v04_activity_process.py`
- Modify: `src/esdm/process/__init__.py`

**Interfaces:**
- Consumes: `ProcessContribution`, `PriorSpec`.
- Produces:
  - `LinearActivity(covariates, intercept_parameter, coefficient_parameters, name="activity")`
  - `NeutralActivity(intercept_parameter, name="activity")`
  - Both emit channel `activity` on the logit scale.
  - `LinearActivity.knockout() -> NeutralActivity`.

- [ ] **Step 1: Write RED tests for activity values, priors, and knockout semantics**

Create `tests/test_v04_activity_process.py`:

```python
import math

import pytest

from esdm.domain import Context
from esdm.process import LinearActivity, NeutralActivity


def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def test_linear_activity_emits_additive_logit_contribution():
    process = LinearActivity(
        covariates=("temp",),
        intercept_parameter="activity_intercept",
        coefficient_parameters={"temp": "activity_beta_temp"},
    )
    contribution = process.contribution(
        Context("s1", 1, 0),
        {"activity_intercept": -0.4, "activity_beta_temp": 0.8},
        {"temp": 1.5},
    )

    assert contribution.channel == "activity"
    assert contribution.values == pytest.approx(0.8)
    assert _sigmoid(contribution.values) == pytest.approx(_sigmoid(0.8))


def test_activity_knockout_preserves_intercept_and_removes_slopes():
    process = LinearActivity(
        covariates=("temp",),
        intercept_parameter="activity_intercept",
        coefficient_parameters={"temp": "activity_beta_temp"},
    )
    knockout = process.knockout()

    assert isinstance(knockout, NeutralActivity)
    assert knockout.knockout_semantics == "preserve_baseline_neutralize_environmental_slopes"
    assert set(knockout.priors()) == {"activity_intercept"}
    assert knockout.requires == frozenset()
    assert knockout.contribution(
        Context("s1", 1, 0),
        {"activity_intercept": -0.4},
        {"temp": 99.0},
    ).values == pytest.approx(-0.4)
```

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_activity_process.py -q
```

Expected: import failure for `LinearActivity`.

- [ ] **Step 3: Implement `LinearActivity` and `NeutralActivity`**

Use the validation pattern already used by `LinearSuitability`:

```python
@dataclass(frozen=True, slots=True)
class LinearActivity:
    covariates: tuple[str, ...]
    intercept_parameter: str
    coefficient_parameters: Mapping[str, str]
    name: str = "activity"
    output_channel: str = "activity"
    latent_species_dependencies: frozenset[str] = frozenset()
    knockout_semantics: str = "preserve_baseline_neutralize_environmental_slopes"

    @property
    def requires(self) -> frozenset[str]:
        return frozenset(self.covariates)

    def priors(self) -> dict[str, PriorSpec]:
        priors = {
            self.intercept_parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 2.0})
        }
        for parameter in self.coefficient_parameters.values():
            priors[parameter] = PriorSpec("Normal", {"loc": 0.0, "scale": 1.0})
        return priors

    def contribution(self, ctx, theta, covariates, latent_fields=None):
        value = theta[self.intercept_parameter]
        for covariate in self.covariates:
            value = value + theta[self.coefficient_parameters[covariate]] * covariates[covariate]
        return ProcessContribution(self.output_channel, value)

    def contribution_array(self, keys, theta, covariates, *, array_module, latent_fields=None):
        value = array_module.broadcast_to(
            array_module.asarray(theta[self.intercept_parameter]),
            (len(keys),),
        )
        for covariate in self.covariates:
            value = value + theta[self.coefficient_parameters[covariate]] * covariates[covariate]
        return ProcessContribution(self.output_channel, value)

    def knockout(self):
        return NeutralActivity(intercept_parameter=self.intercept_parameter, name=self.name)
```

`NeutralActivity` returns the broadcast intercept and only declares its intercept prior.

- [ ] **Step 4: Run activity and process-contract tests**

```bash
python -m pytest tests/test_v04_activity_process.py tests/test_v04_process_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/esdm/process/activity.py src/esdm/process/__init__.py tests/test_v04_activity_process.py
git commit -m "feat: add ecological activity process"
```

---

### Task 3: Add the reference-coded categorical state process

**Files:**
- Create: `src/esdm/process/state.py`
- Create: `tests/test_v04_state_process.py`
- Modify: `src/esdm/process/__init__.py`

**Interfaces:**
- Consumes: `StateSpace`, `ProcessContribution`, `PriorSpec`.
- Produces:
  - `LinearState(state_space, reference_state, covariates, intercept_parameters, coefficient_parameters, name="state")`
  - `NeutralState(state_space, reference_state, intercept_parameters, name="state")`
  - contribution labels are exactly `state_space.states`;
  - returned values are logits in declared state order with reference-state logit exactly zero;
  - only non-reference states have free parameters.

- [ ] **Step 1: Write RED tests for reference coding and knockout**

Create `tests/test_v04_state_process.py`:

```python
import numpy as np
import pytest

from esdm.domain import Context, StateSpace
from esdm.process import LinearState, NeutralState


def _state_process():
    return LinearState(
        state_space=StateSpace(("resting", "foraging", "moving")),
        reference_state="resting",
        covariates=("temp",),
        intercept_parameters={
            "foraging": "alpha_foraging",
            "moving": "alpha_moving",
        },
        coefficient_parameters={
            "foraging": {"temp": "beta_foraging_temp"},
            "moving": {"temp": "beta_moving_temp"},
        },
    )


def test_reference_state_has_no_free_parameter_and_zero_logit():
    process = _state_process()

    assert "resting" not in process.intercept_parameters
    assert set(process.priors()) == {
        "alpha_foraging",
        "alpha_moving",
        "beta_foraging_temp",
        "beta_moving_temp",
    }

    contribution = process.contribution(
        Context("s1", 1, 0),
        {
            "alpha_foraging": 0.2,
            "alpha_moving": -0.3,
            "beta_foraging_temp": 0.5,
            "beta_moving_temp": -0.2,
        },
        {"temp": 2.0},
    )
    assert contribution.channel == "state"
    assert contribution.labels == ("resting", "foraging", "moving")
    np.testing.assert_allclose(contribution.values, [0.0, 1.2, -0.7])


def test_state_knockout_preserves_baseline_composition_and_removes_slopes():
    process = _state_process()
    knockout = process.knockout()

    assert isinstance(knockout, NeutralState)
    assert set(knockout.priors()) == {"alpha_foraging", "alpha_moving"}
    contribution = knockout.contribution(
        Context("s1", 1, 0),
        {"alpha_foraging": 0.2, "alpha_moving": -0.3},
        {"temp": 100.0},
    )
    np.testing.assert_allclose(contribution.values, [0.0, 0.2, -0.3])


def test_state_process_rejects_reference_or_parameter_mismatch():
    states = StateSpace(("resting", "foraging"))
    with pytest.raises(ValueError):
        LinearState(
            state_space=states,
            reference_state="missing",
            covariates=(),
            intercept_parameters={"foraging": "alpha_foraging"},
            coefficient_parameters={"foraging": {}},
        )
    with pytest.raises(ValueError):
        LinearState(
            state_space=states,
            reference_state="resting",
            covariates=(),
            intercept_parameters={"resting": "alpha_resting"},
            coefficient_parameters={"foraging": {}},
        )
```

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_state_process.py -q
```

Expected: import failure for `LinearState`.

- [ ] **Step 3: Implement state-process validation and scalar/array contributions**

Implement the constructor invariants:

```python
non_reference = tuple(
    state for state in self.state_space.states if state != self.reference_state
)
if set(self.intercept_parameters) != set(non_reference):
    raise ValueError("intercept_parameters must match non-reference states exactly")
if set(self.coefficient_parameters) != set(non_reference):
    raise ValueError("coefficient_parameters must match non-reference states exactly")
for state in non_reference:
    if set(self.coefficient_parameters[state]) != set(self.covariates):
        raise ValueError("state coefficient parameters must match covariates exactly")
```

Scalar contribution returns an ordinary tuple in state order. Array contribution returns shape `(n_context, n_state)` via `array_module.stack(..., axis=1)`; the reference column is zeros.

- [ ] **Step 4: Run state-process tests**

```bash
python -m pytest tests/test_v04_state_process.py tests/test_generative_domain_v03.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/esdm/process/state.py src/esdm/process/__init__.py tests/test_v04_state_process.py
git commit -m "feat: add reference-coded ecological state process"
```

---

### Task 4: Extend latent-field containers and model composition to multiple channels

**Files:**
- Create: `tests/test_v04_latent_channels.py`
- Modify: `src/esdm/model/arrays.py`
- Modify: `src/esdm/model/compose.py`
- Modify: `src/esdm/model/__init__.py`

**Interfaces:**
- Consumes: process `contribution` / `contribution_array`.
- Produces:
  - `ContextStateArray(keys, states, values)`, requiring shape `(len(keys), len(states))`;
  - `LatentFields.log_intensity`;
  - `LatentFields.activity_logit`;
  - `LatentFields.activity`;
  - `LatentFields.state_logits`;
  - `LatentFields.state_probabilities`;
  - array equivalents in `LatentFieldArrays`.
- Derived transforms:
  - sigmoid `1 / (1 + exp(-x))`;
  - stable softmax `exp(z - max(z)) / sum(exp(z - max(z)))`.

- [ ] **Step 1: Write RED composition tests**

Create `tests/test_v04_latent_channels.py` with a model containing one suitability, one activity, and one state process. Assert:

```python
def test_scalar_and_array_latent_channels_match():
    import numpy as np

    from esdm.domain import Grid, StateSpace
    from esdm.model import Model
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearActivity, LinearState, LinearSuitability

    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    processes = (
        LinearSuitability(("x",), "intercept", {"x": "beta_x"}),
        LinearActivity(("x",), "activity_intercept", {"x": "activity_beta_x"}),
        LinearState(
            states,
            "resting",
            ("x",),
            {"foraging": "alpha_foraging"},
            {"foraging": {"x": "beta_foraging_x"}},
        ),
    )
    stream = PresenceOnly(
        "records",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": processes}, (stream,))
    theta = {
        "sp": {
            "intercept": 0.1,
            "beta_x": 0.2,
            "activity_intercept": -0.4,
            "activity_beta_x": 0.5,
            "alpha_foraging": 0.3,
            "beta_foraging_x": 0.6,
        }
    }
    covariates = {
        grid.keys[0]: {"x": -1.0},
        grid.keys[1]: {"x": 2.0},
    }

    scalar = model.latent_fields(theta, covariates)
    array = model.latent_field_arrays(theta, covariates, array_module=np)

    np.testing.assert_allclose(
        array.log_intensity["sp"].values,
        [scalar.log_intensity["sp"][key] for key in grid.keys],
    )
    np.testing.assert_allclose(
        array.activity["sp"].values,
        [scalar.activity["sp"][key] for key in grid.keys],
    )
    assert array.state_probabilities["sp"].states == ("resting", "foraging")
    np.testing.assert_allclose(
        array.state_probabilities["sp"].values.sum(axis=1),
        [1.0, 1.0],
    )
```

Add two more tests:

```python
def test_presence_only_design_does_not_require_activity_or_state_stream_paths():
    # Model.check_design() succeeds because the PresenceOnly stream consumes only log_intensity.
    ...


def test_state_or_activity_process_without_a_consuming_stream_fails_closed():
    # Model.check_design() raises DesignUninformedError for each declared process lacking a path.
    ...
```

Use full concrete fixtures identical in shape to the first test; for the failure fixture set `informs` to include only `suitability`.

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_latent_channels.py -q
```

Expected: failure because multi-channel latent fields do not exist.

- [ ] **Step 3: Add `ContextStateArray`**

In `src/esdm/model/arrays.py`:

```python
@dataclass(frozen=True, slots=True)
class ContextStateArray:
    keys: tuple[ContextKey, ...]
    states: tuple[str, ...]
    values: object

    def __post_init__(self) -> None:
        states = tuple(str(state).strip() for state in self.states)
        if not states or any(not state for state in states) or len(set(states)) != len(states):
            raise ValueError("state labels must be unique non-empty strings")
        shape = getattr(self.values, "shape", None)
        if shape is not None and tuple(int(x) for x in shape[:2]) != (
            len(self.keys),
            len(states),
        ):
            raise ValueError("state-array shape must be context x state")
        object.__setattr__(self, "states", states)
```

Extend `LatentFieldArrays` with mappings for activity logits/probabilities and state logits/probabilities.

- [ ] **Step 4: Refactor scalar and array composition by `output_channel`**

In `Model.latent_fields` and `Model.latent_field_arrays`:

1. collect process contributions per species;
2. add all `log_intensity` values;
3. add all `activity` logits, then apply sigmoid;
4. require all `state` contributions to share identical ordered labels;
5. add state logits and apply stable softmax;
6. if no activity process exists, derived activity is exactly one for every context;
7. do not synthesize a state probability field when no state process exists.

The scalar path may loop over contexts. The array path may loop over processes/states but must not loop over contexts inside parameter arithmetic.

- [ ] **Step 5: Add channel-aware design validation**

Keep the existing per-process path rule and ensure each declared process has a targeted stream for which:

```python
process.name in stream.informs
and process.output_channel in stream.consumes
```

For state contributions, reject mismatched labels before inference.

- [ ] **Step 6: Run v0.4 latent tests and v0.3 model regressions**

```bash
python -m pytest tests/test_v04_latent_channels.py tests/test_generative_model_v03.py tests/test_v032_array_backend.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/esdm/model/arrays.py src/esdm/model/compose.py src/esdm/model/__init__.py tests/test_v04_latent_channels.py
git commit -m "feat: compose intensity activity and state latent channels"
```

---

### Task 5: Introduce generic Poisson observation blocks and adapt PresenceOnly

**Files:**
- Create: `src/esdm/observe/blocks.py`
- Create: `tests/test_v04_observation_blocks.py`
- Modify: `src/esdm/observe/presence_only.py`
- Modify: `src/esdm/observe/__init__.py`

**Interfaces:**
- Produces:
  - `PoissonObservationBlock(name, keys, rates, observed=None, structural_exposure_mask=())`
  - `PresenceOnly.observation_blocks(species, fields, *, data=None, theta_obs=None, covariates=None, array_module=None)`
- `rates` may be tuple/list/NumPy/JAX array.
- `observed` is `None` for simulation/prediction and an ordered integer vector for likelihood/inference.
- Block names are deterministic and unique within `stream × species`.

- [ ] **Step 1: Write RED tests for the block abstraction**

Create `tests/test_v04_observation_blocks.py`:

```python
def test_presence_only_block_matches_existing_expected_rates():
    import numpy as np
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 2.0, grid.keys[1]: 4.0}),
        detection_probability=0.5,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": (LinearSuitability((), "intercept", {}),)},
        (stream,),
    )
    theta = {"sp": {"intercept": 0.0}}
    covariates = {key: {} for key in grid.keys}
    fields = model.latent_field_arrays(theta, covariates, array_module=np)

    block, = stream.observation_blocks(
        "sp",
        fields,
        data={grid.keys[0]: 1, grid.keys[1]: 2},
        covariates=covariates,
        array_module=np,
    )

    assert block.name == "records.sp"
    np.testing.assert_allclose(block.rates, [1.0, 2.0])
    assert tuple(block.observed) == (1, 2)
    assert block.structural_exposure_mask == (True, True)
```

Add validation tests that block key/mask/observed lengths must match.

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_observation_blocks.py -q
```

Expected: import/method failure.

- [ ] **Step 3: Implement `PoissonObservationBlock`**

The dataclass validates:

```python
if not name:
    raise ValueError("observation block name must be non-empty")
if len(mask) != len(keys):
    raise ValueError("structural exposure mask must match context count")
if observed is not None and len(observed) != len(keys):
    raise ValueError("observed vector must match context count")
```

Do not coerce JAX rates to Python floats.

- [ ] **Step 4: Implement `PresenceOnly.observation_blocks` via existing rate code**

For an array path, call `expected_rate_array`; for scalar compatibility, pack `expected_rates` in domain order. Bind counts in key order when `data` is supplied. Reuse `structural_exposure_mask`.

Keep `expected_rates`, `expected_rate_array`, and `log_lik` unchanged at their public surface.

- [ ] **Step 5: Run observation and v0.3 PresenceOnly regressions**

```bash
python -m pytest tests/test_v04_observation_blocks.py tests/test_presence_only_v03.py tests/test_v032_partial_effort_numpyro.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/esdm/observe/blocks.py src/esdm/observe/presence_only.py src/esdm/observe/__init__.py tests/test_v04_observation_blocks.py
git commit -m "refactor: expose generic Poisson observation blocks"
```

---

### Task 6: Add detection models and the StateAnnotatedCount stream

**Files:**
- Create: `src/esdm/observe/detection.py`
- Create: `src/esdm/observe/state_annotated.py`
- Create: `tests/test_v04_state_annotated.py`
- Modify: `src/esdm/observe/__init__.py`

**Interfaces:**
- Produces:
  - `KnownDetection(probability: float)`
  - `LogitDetection(intercept_parameter: str = "detection_intercept")`
  - `StateAnnotatedCount(name, state_space, effort, detection, informs, targets)`
- Detection API:
  - `priors() -> dict[str, PriorSpec]`
  - `probability(theta, *, array_module=None) -> object`
- Data shape for annotated streams is fixed as:
  - `data[stream_name][species][state][context_key] -> int`.
- `StateAnnotatedCount.observation_blocks(...)` returns one Poisson block per state in `state_space.states` order.

- [ ] **Step 1: Write RED tests for exact annotated-rate factorization**

Create `tests/test_v04_state_annotated.py` with:

```python
def test_annotated_rates_factor_intensity_activity_state_effort_detection():
    import numpy as np

    from esdm.domain import Grid, StateSpace
    from esdm.model import Model
    from esdm.observe import EffortField, KnownDetection, StateAnnotatedCount
    from esdm.process import LinearActivity, LinearState, LinearSuitability

    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    stream = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({grid.keys[0]: 4.0}),
        detection=KnownDetection(0.5),
        informs=frozenset({"suitability", "activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability((), "intercept", {}),
                LinearActivity((), "activity_intercept", {}),
                LinearState(
                    states,
                    "resting",
                    (),
                    {"foraging": "alpha_foraging"},
                    {"foraging": {}},
                ),
            )
        },
        (stream,),
    )
    theta = {
        "sp": {
            "intercept": np.log(3.0),
            "activity_intercept": 0.0,
            "alpha_foraging": np.log(3.0),
        }
    }
    covariates = {grid.keys[0]: {}}
    fields = model.latent_field_arrays(theta, covariates, array_module=np)

    blocks = stream.observation_blocks(
        "sp",
        fields,
        covariates=covariates,
        array_module=np,
    )

    # intensity=3, activity=0.5, state=(0.25,0.75), effort=4, detection=0.5
    np.testing.assert_allclose(blocks[0].rates, [0.75])
    np.testing.assert_allclose(blocks[1].rates, [2.25])
    assert sum(float(block.rates[0]) for block in blocks) == pytest.approx(3.0)
```

Add tests for:
- missing/unknown state labels in data;
- negative counts;
- positive count under static zero effort;
- state stream targeting a species with no `state` or no `activity` process fails `Model.check_design()`;
- adding activity/state processes does not change `PresenceOnly.expected_rates`.

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_state_annotated.py -q
```

Expected: imports fail.

- [ ] **Step 3: Implement known and unknown detection**

`KnownDetection` validates `0 <= p <= 1`, has no priors, and returns the stored probability.

`LogitDetection` declares:

```python
def priors(self):
    return {
        self.intercept_parameter: PriorSpec(
            "Normal",
            {"loc": 0.0, "scale": 2.0},
        )
    }

def probability(self, theta, *, array_module=None):
    value = theta[self.intercept_parameter]
    if array_module is None:
        return 1.0 / (1.0 + math.exp(-value))
    return 1.0 / (1.0 + array_module.exp(-value))
```

- [ ] **Step 4: Implement `StateAnnotatedCount`**

Use:

```python
consumes = frozenset({"log_intensity", "activity", "state"})
```

For each state index `j`:

```python
rates = (
    exp(log_intensity)
    * activity
    * state_probabilities[:, j]
    * effort
    * detection
)
```

Use the same static exposure mask as the effort model, with all-False when known detection is exactly zero.

Validate annotated data contains exactly the declared state keys.

- [ ] **Step 5: Run annotated-stream and PresenceOnly compatibility tests**

```bash
python -m pytest tests/test_v04_state_annotated.py tests/test_presence_only_v03.py tests/test_v04_latent_channels.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/esdm/observe/detection.py src/esdm/observe/state_annotated.py src/esdm/observe/__init__.py tests/test_v04_state_annotated.py
git commit -m "feat: add state-annotated count observations"
```

---

### Task 7: Generalize in-model simulation over observation blocks

**Files:**
- Create: `tests/test_v04_simulation.py`
- Modify: `src/esdm/simulate/in_model.py`
- Modify: `src/esdm/simulate/__init__.py`

**Interfaces:**
- Produces:
  - `GeneratedObservations(counts, expected_rates)`
  - `simulate_observations(model, theta, covariates, *, seed, theta_obs=None) -> GeneratedObservations`
- Preserves:
  - `GeneratedPresenceOnly`
  - `simulate_presence_only(...)`.

- [ ] **Step 1: Write RED simulation tests**

Create a two-state annotated fixture and assert deterministic structure:

```python
def test_generic_simulator_generates_all_declared_state_blocks():
    from esdm.simulate import simulate_observations

    model, theta, covariates = build_annotated_fixture()
    generated = simulate_observations(
        model,
        theta,
        covariates,
        theta_obs={"annotated": {}},
        seed=7,
    )

    assert set(generated.counts["annotated"]["sp"]) == {"resting", "foraging"}
    assert set(generated.expected_rates["annotated"]["sp"]) == {"resting", "foraging"}
    assert all(
        count >= 0
        for by_context in generated.counts["annotated"]["sp"].values()
        for count in by_context.values()
    )
```

Also assert existing `simulate_presence_only` output matches the generic simulator for a PresenceOnly-only model at the same seed and preserves its old nested shape.

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_simulation.py -q
```

Expected: missing `simulate_observations`.

- [ ] **Step 3: Implement generic simulation**

Algorithm:

```python
fields = model.latent_fields(theta, covariates)
for stream in model.streams:
    for species in model.stream_targets(stream):
        blocks = stream.observation_blocks(
            species,
            fields,
            theta_obs=stream_theta,
            covariates=covariates,
        )
        for block in blocks:
            sample Poisson from each block rate in key order
            store according to stream.data_shape contract
```

For `PresenceOnly`, store `counts[stream][species][key]`.

For `StateAnnotatedCount`, store `counts[stream][species][state][key]`.

Do not duplicate stream rate equations in the simulator.

- [ ] **Step 4: Make `simulate_presence_only` a compatibility wrapper**

The wrapper calls `simulate_observations`, rejects non-PresenceOnly streams if necessary for its legacy return type, and returns the existing `GeneratedPresenceOnly` shape.

- [ ] **Step 5: Run simulation, SBC, and v0.3 regression tests**

```bash
python -m pytest tests/test_v04_simulation.py tests/test_presence_only_v03.py tests/test_numpyro_sbc_v03.py -q
```

Expected: PASS or NumPyro skips only where the backend is unavailable.

- [ ] **Step 6: Commit**

```bash
git add src/esdm/simulate/in_model.py src/esdm/simulate/__init__.py tests/test_v04_simulation.py
git commit -m "refactor: simulate all observation streams from shared blocks"
```

---

### Task 8: Route NumPyro through generic observation blocks

**Files:**
- Create: `tests/test_v04_numpyro.py`
- Modify: `src/esdm/model/backend_numpyro.py`

**Interfaces:**
- Consumes: `stream.observation_blocks(...)`.
- Produces:
  - generic likelihood construction for PresenceOnly and StateAnnotatedCount;
  - `posterior_latent_fields(model, samples, covariates)`;
  - `posterior_observation_rates(model, samples, covariates)`;
  - existing `posterior_record_rates` remains a PresenceOnly-compatible wrapper.

- [ ] **Step 1: Write RED NumPyro sample-site and posterior-field tests**

In `tests/test_v04_numpyro.py`, skip when NumPyro is unavailable. Build a small known-detection annotated model and assert:

```python
fit = fit_numpyro(
    model,
    data,
    covariates,
    rng_seed=11,
    num_warmup=100,
    num_samples=120,
    num_chains=1,
    progress_bar=False,
)

assert "sp.activity.activity_intercept" in fit.samples
assert "sp.state.alpha_foraging" in fit.samples
assert "sp.state.alpha_resting" not in fit.samples

posterior = posterior_latent_fields(model, fit.samples, covariates)
assert posterior.activity["sp"].shape == (120, len(model.domain.keys))
assert posterior.state_probabilities["sp"].shape == (
    120,
    len(model.domain.keys),
    2,
)
```

Use modest synthetic counts that produce finite fits; the test is a smoke test, not a promotion recovery threshold.

- [ ] **Step 2: Run and verify RED**

```bash
python -m pytest tests/test_v04_numpyro.py -q
```

Expected on NumPyro environments: failure because annotated generic block likelihood/posterior extraction is missing.

- [ ] **Step 3: Generalize data validation**

Move stream-specific nested-data validation behind stream methods:

```python
stream.validate_species_data(species, data[stream.name][species], model.domain.keys)
```

Keep explicit missing-target and unexpected-target checks in the backend.

`PresenceOnly.validate_species_data` accepts `context -> count`.
`StateAnnotatedCount.validate_species_data` accepts `state -> context -> count`.

- [ ] **Step 4: Replace hard-coded `expected_rate_array` likelihood construction**

Inside the NumPyro program:

```python
blocks = stream.observation_blocks(
    species,
    fields,
    data=data[stream.name][species],
    theta_obs=stream_theta,
    covariates=covariates,
    array_module=jnp,
)
for block in blocks:
    indices = tuple(i for i, exposed in enumerate(block.structural_exposure_mask) if exposed)
    rates = block.rates[jnp.asarray(indices, dtype=jnp.int32)]
    counts = jnp.asarray([block.observed[i] for i in indices], dtype=jnp.int32)
    numpyro.sample(
        f"obs.{block.name}",
        dist.Poisson(rates).to_event(1),
        obs=counts,
    )
```

Before building the program, fail closed if a non-exposed position has a positive observed count or if a block has no structurally exposed positions.

- [ ] **Step 5: Implement posterior field extraction**

Create a frozen return container, for example:

```python
@dataclass(frozen=True, slots=True)
class PosteriorLatentFields:
    log_intensity: Mapping[str, object]
    activity: Mapping[str, object]
    state_probabilities: Mapping[str, object]
    state_labels: Mapping[str, tuple[str, ...]]
```

Pack draws with leading `draw` axis and preserve context/state order.

`posterior_observation_rates` returns block-name keyed draw arrays. `posterior_record_rates` converts PresenceOnly blocks back to the current `(stream, species) -> tuple(draw tuples)` surface.

- [ ] **Step 6: Run NumPyro regression tests**

```bash
python -m pytest tests/test_v04_numpyro.py tests/test_numpyro_backend_v03.py tests/test_v032_partial_effort_numpyro.py -q
```

Expected: PASS on supported Python/NumPyro; optional-backend skip behavior remains valid elsewhere.

- [ ] **Step 7: Commit**

```bash
git add src/esdm/model/backend_numpyro.py tests/test_v04_numpyro.py
git commit -m "feat: infer activity and state through generic observation blocks"
```

---

### Task 9: Generalize exact structural-identification vectors and add the detection-refusal control

**Files:**
- Create: `tests/test_v04_identifiability.py`
- Modify: `src/esdm/identify/design_rank.py`

**Interfaces:**
- Consumes: array-first `stream.observation_blocks(...)`.
- Preserves:
  - `design_jacobian_diagnostic`;
  - `identify_parameter_from_design`;
  - `diagnose_practical_identification`.
- New required target names include:
  - `sp.activity.activity_intercept`;
  - `sp.state.alpha_foraging`;
  - `stream.annotated.detection_intercept`.

- [ ] **Step 1: Write the negative unknown-detection RED test**

Create `tests/test_v04_identifiability.py`:

```python
import importlib.util

import pytest

from esdm.identify import IdentificationStatus

JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_unknown_global_detection_and_activity_intercept_are_structurally_not_identified():
    from esdm.identify import identify_parameter_from_design

    model, covariates, theta, theta_obs = build_unknown_detection_fixture()

    activity = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.activity.activity_intercept",
        method="jax",
    )
    detection = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="stream.annotated.detection_intercept",
        method="jax",
    )

    assert activity.status is IdentificationStatus.NOT_IDENTIFIED
    assert detection.status is IdentificationStatus.NOT_IDENTIFIED
```

The fixture uses:
- constant ecological intensity;
- intercept-only activity;
- two-state state process with fixed nominal non-reference intercept;
- one annotated stream;
- `LogitDetection`;
- no independent detection stream.

- [ ] **Step 2: Write the positive known-detection structural test**

Using the same geometry but `KnownDetection(0.8)`, include a varying activity covariate and state covariate. Assert activity slope and state slope are `IDENTIFIED`.

- [ ] **Step 3: Run and verify RED**

```bash
python -m pytest tests/test_v04_identifiability.py -q
```

Expected: identification code cannot yet obtain generic annotated observation vectors.

- [ ] **Step 4: Replace stream-specific rate-vector construction**

In the JAX exact diagnostic:

```python
fields = model.latent_field_arrays(ecological, covariates, array_module=jnp)
vectors = []
for stream in model.streams:
    stream_theta = observation.get(stream.name, {})
    for species in model.stream_targets(stream):
        blocks = stream.observation_blocks(
            species,
            fields,
            theta_obs=stream_theta,
            covariates=covariates,
            array_module=jnp,
        )
        for block in blocks:
            mask = block.structural_exposure_mask
            active = jnp.asarray(
                [i for i, exposed in enumerate(mask) if exposed],
                dtype=jnp.int32,
            )
            vectors.append(block.rates[active])
return jnp.concatenate(vectors)
```

Do not filter based on nominal parameter-dependent rate. Filter by the static structural-exposure mask, aligning identification semantics with the NumPyro backend.

- [ ] **Step 5: Keep the legacy finite-difference path compatible**

For environments without JAX, obtain scalar block rates from the same observation-block interface. Do not add v0.4 promotion claims to the fallback.

- [ ] **Step 6: Run v0.4 and v0.3.2 identification suites**

```bash
python -m pytest tests/test_v04_identifiability.py tests/test_v032_identifiability.py tests/test_v032_identification_profiles.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/esdm/identify/design_rank.py tests/test_v04_identifiability.py
git commit -m "feat: identify state activity and detection from generic blocks"
```

---

### Task 10: Preserve array-first JAX scaling for activity/state

**Files:**
- Create: `tests/test_v04_jax_scaling.py`
- Modify: `src/esdm/benchmarks/v032_array_trace.py` only if its helper is PresenceOnly-specific.
- Modify: `src/esdm/benchmarks/__init__.py` only if a new generic helper name is required.

**Interfaces:**
- Produces either:
  - existing `array_trace_equation_count(model, covariates, theta, theta_obs)` generalized to all Poisson observation blocks; or
  - `observation_trace_equation_count(...)` with the old name retained as a compatibility alias.

- [ ] **Step 1: Write the 48-context versus 2,880-context activity/state scaling test**

Create `tests/test_v04_jax_scaling.py` and build the same `2 × 6 × 4 = 48` versus `120 × 6 × 4 = 2,880` grids used by v0.3.2, but with:
- suitability slope;
- activity slope;
- two-state state slope;
- StateAnnotatedCount stream.

Test:

```python
small_count = array_trace_equation_count(*small_fixture)
large_count = array_trace_equation_count(*large_fixture)

assert small_count > 0
assert large_count <= small_count + 10
assert large_count < 100
```

The exact ceiling may be tightened after implementation only if it is independent of benchmark outcomes; it must never be loosened in response to a scientific validation result.

- [ ] **Step 2: Run and verify RED or regression status**

```bash
python -m pytest tests/test_v04_jax_scaling.py tests/test_v032_jax_scaling.py -q
```

Expected: the new fixture fails until the trace helper follows generic observation blocks.

- [ ] **Step 3: Generalize the trace helper without context-scalar parameter arithmetic**

The helper must trace:
1. `model.latent_field_arrays(...)`;
2. stream observation blocks;
3. concatenated block-rate arrays.

Do not build parameter-dependent values with a Python loop over `model.domain.keys`.

- [ ] **Step 4: Run both scaling tests**

```bash
python -m pytest tests/test_v04_jax_scaling.py tests/test_v032_jax_scaling.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/esdm/benchmarks/v032_array_trace.py src/esdm/benchmarks/__init__.py tests/test_v04_jax_scaling.py
git commit -m "test: guard v0.4 state activity JAX trace scaling"
```

---

### Task 11: Full compatibility verification and README boundary update

**Files:**
- Modify: `README.md`
- Test: complete `tests/` suite.

**Interfaces:**
- No new runtime interfaces.
- Documentation must distinguish “v0.4 core implemented” from “v0.4 promotion validated”.

- [ ] **Step 1: Update README v0.4 status**

Document:
- factorized intensity/activity/state graph;
- PresenceOnly remains intensity-only;
- StateAnnotatedCount consumes intensity + activity + state;
- exact refusal under activity/detection confounding;
- full promotion still requires the separate frozen validation PR.

Replace any wording implying v0.4 is wholly unimplemented, but do not mark the v0.4 promotion gate PASS.

- [ ] **Step 2: Run targeted core suite locally/current runner**

```bash
python -m pytest -q
```

Expected: all available tests pass; optional NumPyro tests skip only where unsupported.

- [ ] **Step 3: Verify frozen validation records are unchanged**

Run:

```bash
git diff feature/v032-identifiability-hardening -- docs/validation/V031_PROMOTION_GATE.md docs/validation/V031_RESULTS.md docs/validation/V031_FROZEN_RESULTS.json docs/validation/V032_PROMOTION_GATE.md docs/validation/V032_RESULTS.md docs/validation/V032_FROZEN_RESULTS.json
```

Expected: no output.

- [ ] **Step 4: Verify no context-scalar regression by running both scaling tests**

```bash
python -m pytest tests/test_v032_jax_scaling.py tests/test_v04_jax_scaling.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md
git commit -m "docs: describe v0.4 state activity core boundary"
```

---

### Task 12: CI verification, review gate, and stacked PR #9

**Files:**
- No runtime file is required unless CI exposes a genuine compatibility defect.
- PR base: `feature/v032-identifiability-hardening`.
- PR head: `feature/v04-state-activity-core`.

**Interfaces:**
- Produces a reviewable PR #9 with no merge action.

- [ ] **Step 1: Push/verify the branch head and inspect CI matrix**

Require:
- Python 3.10 success;
- Python 3.11 success;
- Python 3.12 success;
- actual NumPyro v0.4 tests execute on supported Python versions.

- [ ] **Step 2: If any test fails, use systematic debugging before changing code**

For every failure:
1. reproduce the smallest failing test;
2. determine whether the cause is implementation, test assumption, or environment;
3. fix the root cause;
4. rerun the smallest test;
5. rerun the affected test group;
6. rerun full CI.

Do not change scientific validation thresholds because PR #9 contains no promotion benchmark.

- [ ] **Step 3: Perform code-review checks**

Inspect the diff from PR #8 head and verify:
- no v0.3.1/v0.3.2 frozen validation file changed;
- PresenceOnly public semantics are unchanged;
- no duplicated activity/state equations appear separately in simulator, NumPyro, and identification code;
- unknown detection remains under observation parameters;
- reference-state sample sites are absent;
- no state/activity result is converted to scientific `Supported`.

- [ ] **Step 4: Create stacked PR #9**

Use title:

```text
Add factorized ecological state and activity core v0.4
```

PR body must include:
- base/head refs;
- design-spec path and commits;
- process/channel architecture;
- observation-block architecture;
- known-detection positive smoke evidence;
- unknown-detection structural refusal evidence;
- JAX scaling evidence;
- full CI evidence;
- explicit statement that v0.4 promotion remains pending PR #10 frozen validation.

- [ ] **Step 5: Mark PR ready only after exact-head CI is green**

Do not merge PR #9. The next development branch for PR #10 must be stacked from the exact reviewed PR #9 head.

---

## Plan self-review result

### Spec coverage

Every approved design requirement maps to a task:

- generic contribution/channel layer — Tasks 1, 4;
- LinearActivity — Task 2;
- LinearState/reference coding — Task 3;
- multi-channel latent fields — Task 4;
- generic observation blocks — Task 5;
- known/unknown detection — Task 6;
- StateAnnotatedCount — Task 6;
- shared simulation path — Task 7;
- shared NumPyro path/posterior fields — Task 8;
- structural identification/refusal — Task 9;
- array-first JAX scaling — Task 10;
- v0.3.2 compatibility/frozen-record preservation — Tasks 4, 5, 7, 8, 9, 10, 11;
- documentation/claim boundary — Task 11;
- exact-head review/CI/stacked PR — Task 12.

### Placeholder scan

The plan contains no `TBD`, `TODO`, `FIXME`, or unspecified “write tests for this” steps. Every task has explicit interfaces, test intent, commands, and commit boundary.

### Type and naming consistency

The plan consistently uses:
- semantic channels `log_intensity`, `activity`, `state`;
- `ProcessContribution`;
- `ContextStateArray`;
- `PoissonObservationBlock`;
- `KnownDetection` / `LogitDetection`;
- `StateAnnotatedCount`;
- `simulate_observations`;
- `posterior_latent_fields`;
- `posterior_observation_rates`;
- compatibility wrappers `simulate_presence_only` and `posterior_record_rates`.

No named-state-axis channel is introduced; v0.4 remains single-axis per species as specified.
