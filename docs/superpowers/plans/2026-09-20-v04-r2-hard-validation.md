# v0.4-R2 Hard Separation Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frozen v0.4-R2 gate at `docs/validation/V04_R2_PROMOTION_GATE.md`, preserving v0.3.2 observation-process separation while adding temporal activity/state truth.

**Architecture:** Extend the observation layer minimally so PresenceOnly can use an explicit detection model and effort can depend on multiple covariates. Then build a three-stream semi-synthetic fixture: broad opportunistic PresenceOnly with unknown effort+detection, partial calibrated PresenceOnly with known observation process, and partial StateAnnotatedCount with known observation process. Reuse shared observation blocks, exact identification, NumPyro, and held-out state-block scoring.

**Tech Stack:** Python 3.10+ core, JAX/NumPyro on supported Python versions, pytest, GitHub Actions.

**Spec:** `docs/validation/V04_R2_PROMOTION_GATE.md`

## Global Constraints

- Freeze commit: `9e6db6fbe8336c6eb8bbe354713d2863fc40033f`.
- Do not edit `docs/validation/V04_R2_PROMOTION_GATE.md`.
- Do not inspect or use any earlier v0.4-R1 outcome artifact.
- Preserve all PR #9 v0.4 core behavior and all V031/V032 frozen files.
- PresenceOnly without an explicit detection model must remain numerically unchanged.
- Unknown observation parameters remain stream-qualified observation parameters.
- Temporal covariates are deterministic domain covariates; no observed outcome enters them.
- Outcome execution is unauthorized until the R2 pre-outcome verification task passes.

## Review Focus

- PresenceOnly's backward-compatible `detection_probability` and new detection object cannot be simultaneously ambiguous.
- Multi-covariate effort must be array-first under JAX and keep structural exposure always true.
- Partial calibrated/annotated streams must have zero training exposure outside selected spaces.
- East annotations must never enter fitting.
- R2 positive identification targets include ecological, effort, detection, activity, and state layers.

---

### Task 1: Multi-covariate unknown effort

**Files:**
- Modify: `src/esdm/observe/effort.py`
- Modify: `src/esdm/observe/__init__.py`
- Create: `tests/test_v04_r2_effort.py`

**Interfaces:**
- Add `MultiLogLinearEffort(baseline, covariates, coefficient_parameters)`.
- `priors()` returns one Normal prior per coefficient.
- `at()` and `array()` compute baseline × exp(sum(beta_k x_k)).
- `structural_exposure_mask()` is all True.

- [ ] Write RED scalar/array/prior/validation tests.
- [ ] Verify RED.
- [ ] Implement minimal class with exact covariate/parameter matching and unique names.
- [ ] Run new tests plus existing effort/array scaling tests.
- [ ] Commit.

### Task 2: PresenceOnly explicit detection model

**Files:**
- Modify: `src/esdm/observe/presence_only.py`
- Create: `tests/test_v04_r2_presence_detection.py`

**Interfaces:**
- Add optional `detection: object | None = None`.
- If omitted, current `detection_probability` behavior is unchanged.
- If supplied, `detection_probability` must remain at its default 1.0; otherwise fail closed.
- `priors()` merges effort and detection priors and rejects name collisions.
- `requires` merges effort and detection requirements.
- Rates multiply by `detection.probability(theta_obs)`.
- Structural exposure incorporates explicit detection's structural exposure.

- [ ] Write RED compatibility, unknown-detection, collision, and zero-exposure tests.
- [ ] Verify RED.
- [ ] Implement detection object path while preserving legacy path.
- [ ] Run PresenceOnly, NumPyro, identification, and v0.3.2 regression tests.
- [ ] Commit.

### Task 3: R2 fixture with spatial + temporal truth

**Files:**
- Create: `src/esdm/validate/v04_r2_state_activity.py`
- Create: `tests/test_v04_r2_fixture.py`

**Interfaces:**
- Build temporal covariates season_sin/cos and hour_sin/cos.
- Build positive maximin-18 and sparse-center-4 calibration profiles.
- Build three streams O/C/A exactly as frozen.
- Build positive and unknown-detection refusal fixtures and frozen anchors.

- [ ] Write RED tests for exact truths, stream classes, temporal covariates, exposure maps, maximin determinism, and anchors.
- [ ] Verify RED.
- [ ] Implement fixture.
- [ ] Run fixture tests and all v0.4 core model checks.
- [ ] Commit.

### Task 4: R2 identification and mechanical gate

**Files:**
- Create: `src/esdm/validate/v04_r2_gate.py`
- Create: `tests/test_v04_r2_gate.py`
- Create: `tests/test_v04_r2_identification.py`

**Interfaces:**
- Positive/sparse target set is the frozen 13 targets.
- Unknown-detection refusal target set is the frozen 2 targets.
- Gate summary contains 13 bias + 13 coverage metrics, transfer metrics, refusal booleans, counts, divergences.

- [ ] Write RED config/conjunction tests from frozen thresholds.
- [ ] Write JAX-gated RED profile tests.
- [ ] Implement profile evaluation and gate decision.
- [ ] Run focused tests.
- [ ] Commit.

### Task 5: R2 replicated runner

**Files:**
- Create: `src/esdm/validate/v04_r2_run.py`
- Create: `tests/test_v04_r2_run.py`

**Interfaces:**
- Generate once per replicate.
- Fit full/activity-knockout/state-knockout to identical west+central data.
- Recover 13 frozen targets.
- Score held-out Stream A state blocks.
- Summarize exactly 16 replicates / 48 fits.

- [ ] Write RED summary/data-slicing tests without MCMC.
- [ ] Verify RED.
- [ ] Implement runner using shared simulation, NumPyro, and block scoring.
- [ ] Run focused tests.
- [ ] Commit.

### Task 6: R2 coordinator and guarded workflow

**Files:**
- Create: `scripts/run_v04_r2_state_activity.py`
- Create: `.github/workflows/v04-r2-state-activity-full-once.yml`
- Create: `tests/test_v04_r2_script.py`
- Create: `tests/test_v04_r2_workflow.py`

**Interfaces:**
- Frozen profile: 16 reps, seed 20260926, stride 47, warmup 300, samples 350, chains 2, mass 0.90, target_accept 0.90.
- Scientific controls not exposed on public CLI.
- Outcome workflow requires explicit `docs/validation/V04_R2_RUN_AUTHORIZED`.
- Artifact defaults to `INFRASTRUCTURE_BLOCKED`.

- [ ] Write RED script/workflow contract tests.
- [ ] Implement fresh-process coordinator with source digest audit.
- [ ] Implement guarded one-shot workflow.
- [ ] Run focused tests.
- [ ] Commit.

### Task 7: Pre-outcome verification and authorization

- [ ] Require ordinary CI GREEN on Python 3.10/3.11/3.12.
- [ ] Require R2 workflow precheck GREEN with gate job skipped before authorization.
- [ ] Confirm R2 gate file is byte-identical to freeze commit.
- [ ] Confirm no V031/V032 file changed.
- [ ] Confirm no earlier R1 artifact/result is referenced by R2 code or docs.
- [ ] Only then create `docs/validation/V04_R2_RUN_AUTHORIZED`.

### Task 8: Frozen R2 outcome run and results

- [ ] Execute the guarded R2 workflow.
- [ ] If infrastructure blocks, repair infrastructure only; never alter frozen scientific controls.
- [ ] Verify artifact digest independently.
- [ ] Recompute every summary metric from replicate rows.
- [ ] Record exact PASS/FAIL in `V04_R2_RESULTS.md` and `V04_R2_FROZEN_RESULTS.json`.
- [ ] Open PR #10 stacked on PR #9 only after exact-head CI is GREEN.
