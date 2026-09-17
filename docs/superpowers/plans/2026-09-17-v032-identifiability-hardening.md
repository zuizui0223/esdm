# v0.3.2 Identifiability Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the v0.3 ecological/observation foundation scalable and diagnostically honest before adding v0.4 state/activity processes.

**Architecture:** Keep the frozen v0.3.1 record unchanged. Add an array-first backend path for JAX/NumPyro, separate structural from practical identifiability, require explicit observation targets, expose reusable evidence primitives, and freeze a harder Gate F-prime with unknown effort, partial calibration and real extrapolation.

**Tech Stack:** Python 3.10+, optional JAX/NumPyro under the existing `inference` extra, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-v032-identifiability-hardening-design.md`

## Global Constraints

- `feature/v031-identification-fixes` frozen Gate A–F documents/results must not be rewritten.
- JAX remains optional for base-package users.
- Structural identification must not imply scientific support.
- No new state/activity ecological process is added in this plan.
- `targets=None` must not silently mean all species.
- Gate F-prime criteria must be committed before outcome-producing full runs.

---

### Task 1: Explicit observation targets

**Files:**
- Modify: `src/esdm/observe/presence_only.py`
- Modify: `src/esdm/model/compose.py`
- Modify: fixtures/tests that still construct `PresenceOnly(..., targets=None)`
- Test: `tests/test_v032_explicit_targets.py`

**Interfaces:**
- Produces: `PresenceOnly.targets: frozenset[str]` as a required non-empty declaration.
- Produces: `Model.stream_targets(stream) -> tuple[str, ...]` with no `None -> all species` behavior.

- [ ] **Step 1: Write the failing target-contract tests**

```python
import pytest
from esdm.observe import EffortField, PresenceOnly


def test_presence_only_rejects_missing_target_declaration():
    with pytest.raises(ValueError, match="targets must be declared explicitly"):
        PresenceOnly(
            name="opportunistic",
            effort=EffortField({("a", 1, 0): 1.0}),
            informs=frozenset({"suitability"}),
            targets=None,
        )
```

Also add a multi-species regression proving that an explicitly targeted stream cannot interpret an omitted species block as zero-history data.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `pytest tests/test_v032_explicit_targets.py -q`
Expected: failure because `targets=None` is currently accepted.

- [ ] **Step 3: Make `targets` explicit and fail fast**

In `PresenceOnly.__post_init__`, replace the current nullable normalization with:

```python
if self.targets is None:
    raise ValueError("targets must be declared explicitly")
targets = frozenset(str(value).strip() for value in self.targets)
if not targets or any(not value for value in targets):
    raise ValueError("targets must be a non-empty set of species names")
```

In `Model.stream_targets`, remove the `None` fallback and raise if a nonconforming stream reaches the model.

- [ ] **Step 4: Migrate every repository fixture to explicit targets**

Search constructions of `PresenceOnly(` and add the intended species set wherever omitted.

- [ ] **Step 5: Run observation/model regressions**

Run: `pytest tests/test_v031_core_contracts.py tests/test_v031_observation_effort.py tests/test_v031_effort_inference.py tests/test_v032_explicit_targets.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git commit -am "fix: require explicit observation targets"
```

---

### Task 2: Array-first ecological and observation path

**Files:**
- Create: `src/esdm/model/arrays.py`
- Modify: `src/esdm/model/compose.py`
- Modify: `src/esdm/process/suitability.py`
- Modify: `src/esdm/observe/effort.py`
- Modify: `src/esdm/observe/presence_only.py`
- Modify: `src/esdm/model/backend_numpyro.py`
- Modify: `src/esdm/model/__init__.py`
- Test: `tests/test_v032_array_backend.py`

**Interfaces:**
- Produces: `ContextArray(keys, values)`.
- Produces: `LatentFieldArrays(log_intensity)`.
- Produces: `Model.latent_field_arrays(theta, covariates, *, array_module)`.
- Produces: `LinearSuitability.log_intensity_array(...)` and `NeutralSuitability.log_intensity_array(...)`.
- Produces: `EffortField.array(...)`, `LogLinearEffort.array(...)`.
- Produces: `PresenceOnly.expected_rate_array(...)`.

- [ ] **Step 1: Write scalar-vs-array equivalence tests**

Use a small grid with two covariates and assert array values equal the existing mapping results in `grid.keys` order for suitability, effort and expected rates.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_v032_array_backend.py -q`
Expected: missing array APIs.

- [ ] **Step 3: Implement immutable ordered array containers**

```python
@dataclass(frozen=True, slots=True)
class ContextArray:
    keys: tuple[tuple[str, int, int], ...]
    values: object

@dataclass(frozen=True, slots=True)
class LatentFieldArrays:
    log_intensity: Mapping[str, ContextArray]
```

Validate that each species uses exactly `domain.keys` ordering.

- [ ] **Step 4: Vectorize current suitability processes**

For `LinearSuitability`, build one vector per required covariate and compute:

```python
value = xp.full((n_context,), theta[self.intercept_parameter])
for covariate in self.covariates:
    value = value + theta[self.coefficient_parameters[covariate]] * covariate_arrays[covariate]
return value
```

`NeutralSuitability` returns `xp.full((n_context,), intercept)`.

- [ ] **Step 5: Vectorize effort and presence-only rates**

Known effort is a vector in domain order. Log-linear effort computes `baseline * xp.exp(gamma * x)` in one expression. Presence-only rates compute `xp.exp(log_ecological) * effort * detection_probability`.

- [ ] **Step 6: Route NumPyro through arrays**

Replace mapping construction + `jnp.stack` in `make_numpyro_model` with `model.latent_field_arrays(..., array_module=jnp)` and `stream.expected_rate_array(...)`.

- [ ] **Step 7: Run focused tests**

Run: `pytest tests/test_v032_array_backend.py tests/test_generative_model_v03.py tests/test_v031_observation_effort.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git commit -am "refactor: add array-first generative path"
```

---

### Task 3: Deterministic large-context JAX smoke

**Files:**
- Create: `tests/test_v032_jax_scaling.py`
- Create: `src/esdm/benchmarks/v032_array_trace.py`
- Modify: `src/esdm/benchmarks/__init__.py`

**Interfaces:**
- Produces: `array_trace_equation_count(model, covariates, theta, theta_obs) -> int`.

- [ ] **Step 1: Write a 2,880-context scaling test**

Construct 120 spaces × 6 DOY bins × 4 hour bins, then make a JAXPR for the array rate function. Assert the graph builds successfully and the equation count stays below a frozen ceiling chosen from the first array implementation, rather than scaling linearly with all 2,880 contexts.

- [ ] **Step 2: Verify the old scalar path would violate the intended shape contract**

Keep this as a diagnostic comparison if feasible; do not make unstable wall time/RSS a normative assertion.

- [ ] **Step 3: Implement the JAXPR inspection helper**

Use `jax.make_jaxpr` around the pure array-rate function and return `len(jaxpr.jaxpr.eqns)`.

- [ ] **Step 4: Run**

Run: `pytest tests/test_v032_jax_scaling.py -q`
Expected: PASS with inference dependencies installed; otherwise the test is skipped with an explicit reason.

- [ ] **Step 5: Commit**

```bash
git commit -am "test: freeze array-trace scaling contract"
```

---

### Task 4: Exact structural and practical identifiability

**Files:**
- Replace implementation in: `src/esdm/identify/design_rank.py`
- Create: `src/esdm/identify/practical.py`
- Modify: `src/esdm/identify/__init__.py`
- Test: `tests/test_v032_identifiability.py`

**Interfaces:**
- Keeps: `identify_parameter_from_design(...) -> IdentificationResult`.
- Adds: `DesignJacobianDiagnostic` with site order, singular values, ranks and thresholds.
- Adds: `PracticalIdentificationDiagnostic`.
- Adds: `diagnose_practical_identification(...)`.

- [ ] **Step 1: Add failing exact/near-confounding tests**

Cases:

```python
# exact: h == x
assert structural.status is IdentificationStatus.NOT_IDENTIFIED

# near: h == x + 1e-6 * noise
assert structural.status is IdentificationStatus.IDENTIFIED
assert practical.weak is True

# calibrated second stream
assert structural.status is IdentificationStatus.IDENTIFIED
assert practical.weak is False
```

Add a nonlinear toy observation-rate function whose redundant sensitivity is exactly captured by autodiff.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_v032_identifiability.py -q`.

- [ ] **Step 3: Flatten declared parameters in stable site order**

Create helpers that convert nested ecological/observation parameter mappings to/from one vector following `_parameter_sites(model)`.

- [ ] **Step 4: Build pure log-rate array function and use `jax.jacfwd`**

The function must use the Task-2 array path only. Do not call `float()` or Python `math.log` on tracer values.

- [ ] **Step 5: Use relative SVD rank**

```python
cutoff = max(atol, rtol * singular_values[0])
rank = int((singular_values > cutoff).sum())
```

Zero sensitivity remains `DESIGN_UNINFORMED`; redundant nonzero sensitivity remains `NOT_IDENTIFIED`.

- [ ] **Step 6: Add multiple explicit anchors**

Accept either the existing single `theta/theta_obs` pair or a sequence of explicit anchors. Multiple-anchor classification is conservative: the target is `IDENTIFIED` only when identified at every requested anchor; evidence records each anchor result.

- [ ] **Step 7: Implement practical diagnostics**

Compute singular-value condition metrics and a regularized Fisher-like inverse. Mark weak when frozen thresholds for relative minimum singular value, condition number, or target variance proxy are crossed. Return reasons, never a scientific claim.

- [ ] **Step 8: Run old and new identification tests**

Run: `pytest tests/test_v031_structural_identification.py tests/test_v032_identifiability.py tests/test_identify_v03.py -q`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git commit -am "feat: separate structural and practical identification"
```

---

### Task 5: Reusable evidence ladder

**Files:**
- Create: `src/esdm/validate/evidence.py`
- Modify: `src/esdm/validate/ladder.py`
- Modify: `src/esdm/validate/__init__.py`
- Refactor: `src/esdm/validate/v031_knockout.py`
- Refactor: `src/esdm/validate/v031_semisynthetic_gate.py`
- Test: `tests/test_v032_evidence_api.py`

**Interfaces:**
- Produces: `IdentificationEvidence`, `KnockoutEvidence`, `TransferEvidence`, `EvidenceBundle` dataclasses.
- Produces: `diagnose_identification(...)`, `compare_knockout(...)`, `evaluate_transfer(...)`.

- [ ] **Step 1: Write tests proving evidence APIs contain no support status**

Assert the result types have no `ClaimStatus` field and that the modules do not construct `ClaimStatus.SUPPORTED`.

- [ ] **Step 2: Extract generic held-out score comparison from v0.3.1 gate code**

Move reusable calculation into `compare_knockout` while leaving frozen v0.3.1 wrappers/thresholds unchanged.

- [ ] **Step 3: Add transfer and identification bundles**

Package parameter-recovery summaries, structural results and practical diagnostics without promotion semantics.

- [ ] **Step 4: Run**

Run: `pytest tests/test_v031_knockout_gate.py tests/test_v031_semisynthetic_gate.py tests/test_v032_evidence_api.py -q`.

- [ ] **Step 5: Commit**

```bash
git commit -am "refactor: expose reusable validation evidence"
```

---

### Task 6: Freeze Gate F-prime before running it

**Files:**
- Create: `docs/validation/V032_PROMOTION_GATE.md`
- Create: `src/esdm/validate/v032_semisynthetic.py`
- Create: `src/esdm/validate/v032_semisynthetic_gate.py`
- Create: `scripts/run_v032_semisynthetic.py`
- Create: `tests/test_v032_semisynthetic_fixture.py`
- Create: `tests/test_v032_semisynthetic_gate.py`

**Interfaces:**
- Produces: a positive-control profile and a negative-control profile.
- Produces: a machine-readable gate decision with separate checks for structural identification, practical identification, parameter recovery, extrapolation integrity and held-out knockout gain.

- [ ] **Step 1: Commit `V032_PROMOTION_GATE.md` with all thresholds before full outcomes exist**

The document must freeze the sample geography, training/held-out split, partial calibrated-stream footprint, true ecological/effort coefficients, replicate count, inference profile, practical-identification thresholds, parameter-recovery thresholds, extrapolation check, predictive-gain rule and integrity checks.

- [ ] **Step 2: Write fixture geometry tests**

Assert:
- unknown effort is actually free;
- calibrated stream covers only a subset of training contexts;
- at least one held-out ecological covariate is outside training min/max;
- positive and negative profiles differ only in the predeclared calibration geometry/strength needed to change practical identification.

- [ ] **Step 3: Implement fixture and gate evaluator**

Reuse Task-5 evidence APIs and the current `NeutralSuitability` knockout.

- [ ] **Step 4: Add lightweight deterministic tests**

Gate evaluator tests consume fabricated summaries to prove every conjunction term can independently fail.

- [ ] **Step 5: Commit before full benchmark execution**

```bash
git commit -am "test: freeze v0.3.2 separation gate"
```

---

### Task 7: Run Gate F-prime and record results without rewriting v0.3.1

**Files:**
- Create after the frozen run: `docs/validation/V032_RESULTS.md`
- Create after the frozen run: `docs/validation/V032_FROZEN_RESULTS.json`
- Add/update one-shot workflow under `.github/workflows/` if hosted execution is required.

**Interfaces:**
- Consumes the frozen Task-6 gate/profile only.
- Produces an auditable PASS/FAIL/INFRASTRUCTURE-BLOCKED record for v0.3.2 hardening.

- [ ] **Step 1: Run non-inference unit suites in fresh process groups**

Run at minimum the v0.3.1 core regression suites plus every `test_v032_*` non-inference suite.

- [ ] **Step 2: Run inference-heavy suites separately**

Record exact Git SHA, workflow/run identifiers, artifacts and digests. If memory interrupts the run, record infrastructure-blocked and do not change thresholds.

- [ ] **Step 3: Execute positive and negative F-prime controls**

Positive control must meet every frozen conjunction. Negative control must be refused/flagged by the frozen identification criterion.

- [ ] **Step 4: Write result artifacts**

Record all mechanical checks and raw summaries needed to reproduce the decision.

- [ ] **Step 5: Final regression**

Verify old `V031_*` files are byte-for-byte unchanged relative to `ea00493c`.

- [ ] **Step 6: Commit**

```bash
git commit -am "docs: record v0.3.2 hardening results"
```

---

### Task 8: Open stacked PR and state the v0.4 entry condition

**Files:**
- PR metadata only; no scientific-result changes.

- [ ] **Step 1: Open PR from `feature/v032-identifiability-hardening` to `feature/v031-identification-fixes`**

Title: `Harden identifiability and vectorization before v0.4`

- [ ] **Step 2: PR body must separate historical and new claims**

State explicitly that v0.3.1 remains a frozen historical promotion record, while v0.3.2 adds stricter pre-v0.4 engineering/methodological conditions.

- [ ] **Step 3: Verification-before-completion review**

Confirm targeted tests/workflows, frozen-before-run ordering, unchanged v0.3.1 artifacts, and remaining risks before calling the hardening complete.
