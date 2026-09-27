# v0.4 Frozen Validation R2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frozen R2 gate that tests unknown observation effort/detection, partial calibration, explicit DOY/hour activity/state effects, spatial held-out transfer, and refusal when calibration is removed.

**Architecture:** Build one four-stream positive fixture and two negative-control fixtures from the frozen R2 document. Reuse the shared v0.4 observation-block graph for simulation, NumPyro, posterior scoring, and exact identification. Keep all R2 outcome execution behind an explicit authorization marker added only after normal CI and prechecks are green.

**Tech Stack:** Python 3.10+ core, JAX/NumPyro on supported Python versions, pytest, GitHub Actions.

**Spec:** `docs/validation/V04_PROMOTION_GATE_R2.md`

## Global Constraints

- R1 outputs are excluded from scientific evaluation and must not be inspected.
- R2 freeze commit is `082bfe7be854f6952b7483ff74e886ba761dedec`.
- Do not edit `docs/validation/V04_PROMOTION_GATE_R2.md` after freeze.
- Reuse PR #9 head `f0b269c026e944e922fef539505be450a0a72122` as the core base.
- Positive profile uses four streams: opportunistic/calibrated presence and opportunistic/calibrated state annotations.
- Opportunistic presence has unknown seasonal effort; calibrated presence is partial and known.
- Opportunistic annotations have unknown diurnal effort and unknown global detection; calibrated annotations are partial and known.
- Activity and state each contain explicit DOY and hour terms.
- East is held out from fitting and calibration.
- R2 scientific constants and thresholds are not CLI-configurable.
- Infrastructure interruption is `INFRASTRUCTURE_BLOCKED`, not scientific PASS/FAIL.
- No runtime `Supported` claim is emitted.

---

### Task 1: R2 four-stream fixture and negative controls

**Files:**
- Create: `src/esdm/validate/v04_state_activity_r2.py`
- Create: `tests/test_v04_r2_fixture.py`

**Produces:**
- `V04R2Fixture`
- `build_v04_r2_fixture(source_csv_text, profile="positive")`
- `v04_r2_positive_anchors(fixture)`
- `v04_r2_detection_refusal_anchors(fixture)`

- [ ] RED test exact temporal covariates, truth values, four stream types, partial calibration exposures, and train-only standardization.
- [ ] RED test no-presence-calibration profile removes only the calibrated presence stream.
- [ ] RED test activity/detection-refusal profile removes calibrated annotations and uses intercept-only activity.
- [ ] Implement exact frozen geometry/truth and anchors.
- [ ] GREEN focused tests; commit.

### Task 2: R2 identification profiles and mechanical evaluator

**Files:**
- Create: `src/esdm/validate/v04_state_activity_r2_gate.py`
- Create: `tests/test_v04_r2_identification.py`
- Create: `tests/test_v04_r2_gate.py`

**Produces:**
- positive structural/practical evidence for 11 targets;
- no-presence-calibration exact refusal;
- activity/detection exact refusal;
- pure R2 summary/gate decision with all frozen thresholds.

- [ ] RED config and conjunction tests.
- [ ] RED JAX profile tests.
- [ ] Implement exact JAX/practical diagnostics using the frozen thresholds.
- [ ] GREEN all tests; commit.

### Task 3: State-block predictive score

**Files:**
- Modify: `src/esdm/validate/evidence.py`
- Create: `tests/test_v04_r2_predictive_score.py`

- [ ] RED deterministic two-state block LPD test.
- [ ] Implement through `posterior_observation_rates` only.
- [ ] GREEN old/new evidence tests; commit.

### Task 4: R2 replicated runner

**Files:**
- Create: `src/esdm/validate/v04_state_activity_r2_run.py`
- Create: `tests/test_v04_r2_run.py`

- [ ] RED summary arithmetic for all 11 recovery targets, gains, fit count, divergences.
- [ ] RED train/heldout nested-data slicing test.
- [ ] Implement full/activity-knockout/state-knockout fitting on identical train data.
- [ ] Score east `annotated_opportunistic` state blocks only.
- [ ] GREEN non-MCMC runner tests; commit.

### Task 5: Frozen R2 coordinator and worker isolation

**Files:**
- Create: `scripts/run_v04_state_activity_r2.py`
- Create: `tests/test_v04_r2_script.py`

Frozen execution:
- replicates 16;
- base seed 20260926;
- stride 47;
- warmup 300;
- retained 350;
- chains 2;
- credible mass 0.90;
- target accept 0.92.

- [ ] RED constant/no-override CLI tests.
- [ ] Implement fresh-process workers and fail-closed coordinator.
- [ ] GREEN script tests; commit.

### Task 6: Guarded one-shot workflow

**Files:**
- Create: `.github/workflows/v04-state-activity-r2-full-once.yml`
- Create: `tests/test_v04_r2_workflow.py`

- [ ] RED workflow text contract.
- [ ] Implement precheck job plus authorization-gated outcome job.
- [ ] Outcome job always initializes and uploads fail-closed audit artifact.
- [ ] GREEN workflow test; commit.

### Task 7: Pre-outcome audit and R2 execution

- [ ] Require normal Python 3.10/3.11/3.12 CI green.
- [ ] Require R2 workflow precheck green with outcome job skipped while unauthorized.
- [ ] Verify `V04_PROMOTION_GATE_R2.md` blob is byte-identical to freeze commit.
- [ ] Verify no V031/V032 frozen file changed.
- [ ] Add R2 authorization marker only after all checks pass.
- [ ] Execute R2 outcome workflow.
- [ ] Never inspect R1 artifacts/results.

### Task 8: R2 results and PR #10

- [ ] Verify final R2 artifact digest.
- [ ] Recompute every summary metric from replicate records.
- [ ] Record PASS/FAIL without threshold changes.
- [ ] Create `V04_R2_RESULTS.md` and `V04_R2_FROZEN_RESULTS.json`.
- [ ] Exact-head normal CI green.
- [ ] Open stacked PR #10 to `feature/v04-state-activity-core`, Ready for review, no merge.
