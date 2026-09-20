# v0.4 Frozen State/Activity Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the already-frozen v0.4 promotion gate without changing any scientific threshold, seed, geometry, truth, or claim boundary after freeze commit `551ed43c9d602f39ee37e54e1f4ea230338d749d`.

**Architecture:** Reuse the pinned v0.3.1/v0.3.2 real station geometry and the v0.4 shared generative graph. A fixture defines positive, sparse, and unknown-detection profiles; a pure evaluator implements the mechanical conjunction; a replicated runner fits full/activity-knockout/state-knockout models in isolated worker processes and writes a fail-closed audit artifact.

**Tech Stack:** Python 3.10+ core, optional JAX/NumPyro on supported Python versions, pytest, GitHub Actions.

**Spec:** `docs/validation/V04_PROMOTION_GATE.md`

## Global Constraints

- Freeze commit is `551ed43c9d602f39ee37e54e1f4ea230338d749d`; do not edit `docs/validation/V04_PROMOTION_GATE.md`.
- Reuse source repository `the-pudding/data`, commit `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`, path `rain/annual_precipitation.csv`, blob SHA1 `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`.
- Domain is 120 stations × 6 DOY × 4 hours = 2,880 contexts.
- Training is west + central; east is held out from every fit.
- Positive annotation geometry is exactly 18 eastness-rank-quantile training stations.
- Sparse annotation geometry is exactly 6 training stations minimizing `precip_z_train^2 + eastness_z_train^2`.
- Positive/sparse detection is known 0.85; annotation effort is 8.0; broad PresenceOnly effort is 5.0.
- Unknown-detection profile uses intercept-only activity and `detection_intercept` truth 0.40.
- Positive outcome profile is 16 replicates, base seed 20260924, stride 43, 2 chains, 250 warmup, 300 retained, target_accept 0.90, 90% intervals.
- Run three fits per replicate: full, activity knockout, state knockout.
- Recovery thresholds: absolute mean bias <= 0.15 and 90% coverage >= 0.75 for the four frozen activity/state slopes.
- Transfer thresholds: positive held-out gain rate >= 0.75 and mean gain >= 0.005 separately for activity and state knockouts.
- Mean divergences per fit <= 0.10 across exactly 48 fits.
- Infrastructure interruption produces `INFRASTRUCTURE_BLOCKED`, never scientific PASS/FAIL.
- Do not change any V031/V032 frozen validation file.
- Do not emit a scientific `Supported` claim.

## Review Focus

- Held-out east annotation counts must be generated but never passed into fitting.
- Training annotation exposure must be zero outside the frozen calibration spaces.
- Knockout models must preserve intercept/baseline composition and differ only by environmental activity/state slopes.
- State-specific held-out score must average over all state-context observations, not collapse states first.
- Unknown-detection structural refusal must use intercept-only activity at all three frozen anchors.

---

### Task 1: Frozen v0.4 fixture

**Files:**
- Create: `src/esdm/validate/v04_state_activity.py`
- Create: `tests/test_v04_validation_fixture.py`

**Interfaces:**
- Produces `V04StateActivityFixture`.
- Produces `build_v04_state_activity_fixture(source_csv_text, profile="positive")`.
- Produces `v04_identification_anchors(fixture)`.
- Produces `build_v04_unknown_detection_fixture(source_csv_text)`.
- Produces `v04_unknown_detection_anchors(fixture)`.

- [ ] Write a failing fixture test that asserts the frozen source geometry, training/heldout split, exact positive/sparse space counts, exact truths, annotation exposure, and true eastness extrapolation.
- [ ] Run `python -m pytest tests/test_v04_validation_fixture.py -q` and verify RED.
- [ ] Implement training-only standardization, deterministic profile selection, the three-process species graph, broad PresenceOnly stream, and StateAnnotatedCount stream.
- [ ] For positive/sparse fixtures, give annotated effort 8.0 on calibration spaces plus all east heldout spaces; for training-subset models, east contexts are absent and therefore cannot leak.
- [ ] Implement the unknown-detection fixture with positive 18-space geometry, intercept-only activity, and `LogitDetection("detection_intercept")`.
- [ ] Implement the exact three positive/sparse anchors and three unknown-detection anchors from the frozen gate.
- [ ] Run the fixture tests and existing v0.4 core tests.
- [ ] Commit as `feat: add frozen v0.4 validation fixture`.

### Task 2: Identification profiles and mechanical gate evaluator

**Files:**
- Create: `src/esdm/validate/v04_state_activity_gate.py`
- Create: `tests/test_v04_validation_gate.py`
- Create: `tests/test_v04_validation_identification.py`

**Interfaces:**
- Produces `V04IdentificationProfileResult`.
- Produces `evaluate_v04_identification_profiles(source_csv_text)`.
- Produces `V04SemiSyntheticSummary`, `V04GateConfig`, `V04GateDecision`.
- Produces `evaluate_v04_gate(summary)`.

- [ ] Write RED tests asserting exact config constants from the frozen document.
- [ ] Write a pure passing-summary fixture and one-failure-at-a-time conjunction tests for all boolean, recovery, transfer, replicate-count, fit-count, and divergence checks.
- [ ] Write JAX-gated identification tests asserting positive structural/practical pass, sparse structural pass plus practical refusal, and unknown-detection structural refusal.
- [ ] Implement training-subset profile evaluation with exact JAX rtol 1e-8 / atol 1e-10 and practical thresholds 1e-3 / 1e3 / 0.25 / ridge 1e-10.
- [ ] Implement the mechanical gate evaluator with no claim-promotion semantics.
- [ ] Run focused tests and commit as `feat: evaluate frozen v0.4 validation gate`.

### Task 3: State-specific posterior predictive scoring

**Files:**
- Modify: `src/esdm/validate/evidence.py`
- Create: `tests/test_v04_state_predictive_score.py`

**Interfaces:**
- Produces `poisson_block_log_predictive_density(model, samples, covariates, data, *, block_names)`.
- Existing `poisson_log_predictive_density` and `compare_knockout` remain unchanged.

- [ ] Write RED tests using deterministic fake posterior block rates and two state blocks, checking exact mean state-context log predictive density.
- [ ] Implement scoring via `posterior_observation_rates(...)`, validating block names, context lengths, non-negative counts, and exact state block data lookup.
- [ ] Do not reimplement ecological or stream rate equations.
- [ ] Run old evidence tests plus the new test and commit as `feat: score heldout state observation blocks`.

### Task 4: Replicated v0.4 outcome runner

**Files:**
- Create: `src/esdm/validate/v04_state_activity_run.py`
- Create: `tests/test_v04_validation_run.py`

**Interfaces:**
- Produces `V04Replicate`, `V04Result`, `run_v04_state_activity_benchmark(...)`.
- Produces `summarize_v04_state_activity(...)`.

- [ ] Write RED tests for summary arithmetic using fabricated replicate records only; do not run MCMC in unit tests.
- [ ] Implement model subsetting for train/heldout domains while preserving frozen streams and effort maps.
- [ ] Implement nested data subsetting for PresenceOnly and StateAnnotatedCount without heldout leakage.
- [ ] For each replicate, generate once from the full fixture using `simulate_observations`; fit full, activity-knockout, and state-knockout train models to the same train data.
- [ ] Extract posterior means/90% intervals for the four frozen slope targets.
- [ ] Score heldout annotated state blocks for full vs activity knockout and full vs state knockout using Task 3.
- [ ] Summarize bias, coverage, gain rates, mean gains, divergences, replicate count, and fit count.
- [ ] Run focused non-MCMC tests and commit as `feat: add replicated v0.4 validation runner`.

### Task 5: Frozen CLI coordinator and worker isolation

**Files:**
- Create: `scripts/run_v04_state_activity.py`
- Create: `tests/test_v04_validation_script.py`

**Interfaces:**
- Frozen constants: 16, 20260924, 43, 250, 300, 2, 0.90, 0.90.
- Public CLI exposes only output/progress controls; scientific controls are not CLI options.
- Internal worker arguments are prefixed `--_worker-`.

- [ ] Write RED tests asserting every frozen execution constant and absence of scientific override flags.
- [ ] Implement one-replicate worker mode and coordinator mode.
- [ ] Coordinator downloads the pinned raw source, verifies source blob/content audit metadata, evaluates identification profiles, checks extrapolation, then launches each replicate in a fresh Python process.
- [ ] Initialize/write an audit payload whose default scientific status is not PASS.
- [ ] On worker launch/return/artifact failure, write `INFRASTRUCTURE_BLOCKED` plus completed replicate shards and return a distinct nonzero code.
- [ ] On complete scientific execution, evaluate the frozen gate and write PASS/FAIL plus all replicate records/checks.
- [ ] Run script contract tests and commit as `feat: add frozen v0.4 validation coordinator`.

### Task 6: One-shot GitHub workflow

**Files:**
- Create: `.github/workflows/v04-state-activity-full-once.yml`
- Create: `tests/test_v04_validation_workflow.py`

**Interfaces:**
- Runs only on `feature/v04-frozen-validation` pushes touching the workflow/runner or relevant v0.4 model/stream/validation files.
- Python 3.12, `.[dev,inference]`, timeout 360 minutes.
- Always uploads `artifacts/v04_state_activity_gate.json`.

- [ ] Write a RED text-level workflow test checking branch, timeout, dependency extra, precheck tests, runner command, fail-closed artifact initialization, and `if: always()` upload.
- [ ] Implement workflow with a precheck suite covering v0.4 process, observation, simulation, NumPyro, identification, scaling, fixture, gate, script, and workflow tests.
- [ ] Commit as `ci: add one-shot frozen v0.4 validation workflow`.

### Task 7: Pre-outcome full verification and freeze audit

**Files:**
- No scientific threshold files may change.

- [ ] Run the normal CI matrix and require Python 3.10/3.11/3.12 GREEN.
- [ ] Compare PR #9 head to the current validation branch and assert `docs/validation/V031_*` and `V032_*` are unchanged.
- [ ] Assert `docs/validation/V04_PROMOTION_GATE.md` is byte-identical to freeze commit `551ed43c9d602f39ee37e54e1f4ea230338d749d`.
- [ ] Inspect CLI help and workflow to confirm no scientific overrides.
- [ ] Only after these checks are GREEN may Task 8 trigger the full outcome workflow.

### Task 8: Execute frozen gate, verify artifact, record results, open PR #10

**Files:**
- Create after outcome only: `docs/validation/V04_RESULTS.md`.
- Create after outcome only: `docs/validation/V04_FROZEN_RESULTS.json`.

- [ ] Trigger the frozen one-shot workflow by an allowed branch push after Task 7.
- [ ] If infrastructure blocks, preserve `INFRASTRUCTURE_BLOCKED`; repair infrastructure only without changing frozen scientific controls, then rerun.
- [ ] Download the final artifact and verify its GitHub artifact digest independently.
- [ ] Recompute all summary statistics from replicate rows and confirm exact equality with the artifact summary.
- [ ] Record PASS or FAIL exactly as produced; do not change thresholds in response.
- [ ] Commit human-readable and machine-readable frozen results, rerun ordinary CI, and confirm the gate document is still byte-identical to the freeze commit.
- [ ] Open stacked PR #10 from `feature/v04-frozen-validation` to `feature/v04-state-activity-core`, mark Ready only after exact-head CI is GREEN, and do not merge.
