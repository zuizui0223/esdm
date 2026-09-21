# v0.4-R3a Budget-Neutral Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and prospectively qualify the fixed-budget R3a observation design that redistributes StateAnnotatedCount training exposure from 18 sites × 24 times to 36 sites × 12 times while preserving the R2 observation-separation design and all R2 identification thresholds.

**Architecture:** Build deterministic spatial and temporal maximin selectors first, then construct an R3a positive fixture that reuses R2 truth while changing only StateAnnotatedCount positive training exposure. Freeze a separate R3a qualification gate before any R3a identification outcome is run; only after that freeze is byte-stable may the exact R2 structural/practical identification machinery evaluate the 13 targets and refusal controls.

**Tech Stack:** Python 3.10+ core, dataclasses, pytest, optional JAX on supported Python versions, GitHub Actions.

**Spec:** docs/superpowers/specs/2026-09-21-v04-r3-budget-neutral-design.md

## Global Constraints

- Base branch: feature/v04-r3-budget-neutral-design, stacked from PR #10 head 946451a69b79739de9564fb9a3eb6fbca6203e7c.
- R2 remains a frozen FAIL; do not modify V04_R2_PROMOTION_GATE.md, V04_R2_RESULTS.md, or V04_R2_FROZEN_RESULTS.json.
- Do not modify any V031_* or V032_* validation file.
- Positive R3a StateAnnotatedCount training exposure is exactly 36 sites × 12 temporal contexts = 432 context opportunities.
- Positive calibrated PresenceOnly remains exactly the first 18 spatial maximin sites × all 24 temporal contexts.
- Opportunistic PresenceOnly is unchanged from R2.
- The first 18 sites of the R3a 36-site spatial sequence must equal the frozen R2 positive calibration sequence.
- Spatial selection uses only precip_z_train and eastness_z_train with station-ID tie breaks.
- Temporal selection uses only season_sin, season_cos, hour_sin, hour_cos, starts at (15, 0), and uses lexicographic (doy, hour) tie breaks.
- R3a reuses the exact R2 13-target set, R2 A/B/C anchors, structural thresholds, practical thresholds, sparse refusal profile, and unknown annotated-detection refusal profile.
- R3a contains no MCMC recovery, posterior coverage, held-out transfer, or divergence benchmark.
- R3a identification outcomes must not run until docs/validation/V04_R3A_QUALIFICATION_GATE.md is frozen and verified byte-stable.
- If R3a FAILS, record it and stop. Do not create R3b.
- If R3a PASSES, only then design and freeze a separate R3b gate.
- No R3a code or result may emit scientific Supported.

## Review Focus

- Tie-heavy spatial geometry must resolve only by station ID and be deterministic.
- Tie-heavy temporal geometry must resolve lexicographically and always start at (15, 0).
- Annotated training exposure must be exactly 432 contexts and never silently inflate.
- Calibrated PresenceOnly must stay at 18 × 24 and must not inherit the 36 × 12 geometry.
- Outcome execution must remain impossible until the R3a gate is frozen and an explicit authorization marker is added after precheck.

---

## File map

New files:
- src/esdm/validate/v04_r3a_design.py — selectors and R3a positive fixture.
- src/esdm/validate/v04_r3a_gate.py — pure qualification types and post-freeze identification evaluator.
- tests/test_v04_r3a_selectors.py
- tests/test_v04_r3a_fixture.py
- tests/test_v04_r3a_gate.py
- tests/test_v04_r3a_gate_freeze.py
- tests/test_v04_r3a_identification.py
- scripts/run_v04_r3a_qualification.py
- tests/test_v04_r3a_script.py
- .github/workflows/v04-r3a-qualification-once.yml
- tests/test_v04_r3a_workflow.py
- docs/validation/V04_R3A_QUALIFICATION_GATE.md
- after outcome only: docs/validation/V04_R3A_RESULTS.md
- after outcome only: docs/validation/V04_R3A_FROZEN_RESULTS.json

Existing files intentionally reused without modification:
- src/esdm/validate/v04_r2_state_activity.py
- src/esdm/validate/v04_r2_gate.py
- src/esdm/identify/design_rank.py
- src/esdm/identify/practical.py
- docs/validation/V04_R2_* result/gate files

---

### Task 1: Deterministic budget-neutral selectors

**Files:**
- Create: src/esdm/validate/v04_r3a_design.py
- Create: tests/test_v04_r3a_selectors.py

**Interfaces:**
- Produces spatial_maximin_sequence(train_spaces, covariates, *, count) -> tuple[str, ...].
- Produces temporal_maximin_sequence(doy_values, hour_values, *, count) -> tuple[tuple[int, int], ...].

- [ ] **Step 1: Write the failing spatial selector tests**

Use a tiny geometry where a and b tie for maximum radius:

    def test_spatial_maximin_starts_farthest_and_breaks_ties_by_id():
        from esdm.validate.v04_r3a_design import spatial_maximin_sequence

        spaces = ("b", "a", "c", "d")
        covariates = {
            ("a", 15, 0): {"precip_z_train": 2.0, "eastness_z_train": 0.0},
            ("b", 15, 0): {"precip_z_train": -2.0, "eastness_z_train": 0.0},
            ("c", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": 1.0},
            ("d", 15, 0): {"precip_z_train": 0.0, "eastness_z_train": -1.0},
        }

        selected = spatial_maximin_sequence(spaces, covariates, count=4)

        assert selected[0] == "a"
        assert set(selected) == set(spaces)
        assert len(selected) == len(set(selected)) == 4

Also test count 0, count > len(spaces), duplicate spaces, missing precip_z_train, missing eastness_z_train, and non-finite coordinates.

- [ ] **Step 2: Write the failing temporal selector tests**

    def test_temporal_maximin_is_deterministic_and_starts_at_15_0():
        from esdm.validate.v04_r3a_design import temporal_maximin_sequence

        selected = temporal_maximin_sequence(
            (15, 75, 135, 195, 255, 315),
            (0, 6, 12, 18),
            count=12,
        )

        assert selected[0] == (15, 0)
        assert len(selected) == 12
        assert len(set(selected)) == 12

Also call the selector twice and assert exact tuple equality. Test count 0 and count 25 as errors.

- [ ] **Step 3: Run and verify RED**

Run:
    python -m pytest tests/test_v04_r3a_selectors.py -q

Expected: import failure because v04_r3a_design does not exist.

- [ ] **Step 4: Implement spatial_maximin_sequence**

Implementation:

    def _spatial_point(space, covariates):
        key = (str(space), 15, 0)
        if key not in covariates:
            raise KeyError(f"missing selector covariates for {key!r}")
        values = covariates[key]
        point = (
            float(values["precip_z_train"]),
            float(values["eastness_z_train"]),
        )
        if any(not math.isfinite(value) for value in point):
            raise ValueError("spatial selector coordinates must be finite")
        return point


    def spatial_maximin_sequence(train_spaces, covariates, *, count):
        spaces = tuple(str(space) for space in train_spaces)
        requested = int(count)
        if requested < 1 or requested > len(spaces):
            raise ValueError("invalid spatial maximin request")
        if len(set(spaces)) != len(spaces):
            raise ValueError("training spaces must be unique")
        points = {space: _spatial_point(space, covariates) for space in spaces}
        first = min(
            (-(p * p + e * e), space)
            for space, (p, e) in points.items()
        )[1]
        selected = [first]
        remaining = set(spaces) - {first}
        while len(selected) < requested:
            scored = []
            for space in remaining:
                p, e = points[space]
                min_d2 = min(
                    (p - points[other][0]) ** 2
                    + (e - points[other][1]) ** 2
                    for other in selected
                )
                scored.append((-min_d2, space))
            chosen = min(scored)[1]
            selected.append(chosen)
            remaining.remove(chosen)
        return tuple(selected)

- [ ] **Step 5: Implement temporal_maximin_sequence**

Implementation:

    def _temporal_point(doy, hour):
        season = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
        daily = 2.0 * math.pi * float(hour) / 24.0
        return (
            math.sin(season),
            math.cos(season),
            math.sin(daily),
            math.cos(daily),
        )


    def temporal_maximin_sequence(doy_values, hour_values, *, count):
        candidates = tuple(sorted(
            (int(doy), int(hour))
            for doy in doy_values
            for hour in hour_values
        ))
        requested = int(count)
        if requested < 1 or requested > len(candidates):
            raise ValueError("invalid temporal maximin request")
        points = {key: _temporal_point(*key) for key in candidates}
        selected = [candidates[0]]
        remaining = set(candidates) - {candidates[0]}
        while len(selected) < requested:
            scored = []
            for candidate in remaining:
                point = points[candidate]
                min_d2 = min(
                    sum(
                        (value - points[other][index]) ** 2
                        for index, value in enumerate(point)
                    )
                    for other in selected
                )
                scored.append((-min_d2, candidate))
            chosen = min(scored)[1]
            selected.append(chosen)
            remaining.remove(chosen)
        return tuple(selected)

- [ ] **Step 6: Run selector and R2 regression tests**

Run:
    python -m pytest tests/test_v04_r3a_selectors.py tests/test_v04_r2_fixture.py -q

Expected: PASS.

- [ ] **Step 7: Commit**

    git add src/esdm/validate/v04_r3a_design.py tests/test_v04_r3a_selectors.py
    git commit -m "feat: add deterministic R3a budget selectors"

---

### Task 2: Exact R3a positive fixture

**Files:**
- Modify: src/esdm/validate/v04_r3a_design.py
- Create: tests/test_v04_r3a_fixture.py

**Interfaces:**
- Produces V04R3AFixture.
- Produces build_v04_r3a_fixture(source_csv_text) -> V04R3AFixture.
- Fixture exposes model, covariates, train_spaces, heldout_spaces, calibrated_spaces, annotated_spaces, annotated_times, generating_theta, generating_theta_obs.

- [ ] **Step 1: Write the failing exact-budget test**

    def test_r3a_positive_budget_is_exactly_36_by_12():
        from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

        fixture = build_v04_r3a_fixture(_sample_csv())

        assert len(fixture.annotated_spaces) == 36
        assert len(fixture.annotated_times) == 12
        annotated = fixture.model.streams[2]
        train = set(fixture.train_spaces)
        exposed = {
            key
            for key in fixture.model.domain.keys
            if key[0] in train and annotated.effort.at(key) > 0.0
        }
        expected = {
            (space, doy, hour)
            for space in fixture.annotated_spaces
            for doy, hour in fixture.annotated_times
        }
        assert exposed == expected
        assert len(exposed) == 432

- [ ] **Step 2: Write the calibrated PresenceOnly preservation test**

    def test_r3a_calibrated_presence_only_remains_r2_18_by_24():
        from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture
        from esdm.validate.v04_r3a_design import build_v04_r3a_fixture

        text = _sample_csv()
        r2 = build_v04_r2_fixture(text, profile="positive")
        r3 = build_v04_r3a_fixture(text)

        assert r3.calibrated_spaces == r2.calibration_spaces
        assert r3.annotated_spaces[:18] == r2.calibration_spaces

        calibrated = r3.model.streams[1]
        exposed = {
            key
            for key in r3.model.domain.keys
            if calibrated.effort.at(key) > 0.0
        }
        expected = {
            (space, doy, hour)
            for space in r3.calibrated_spaces
            for doy in r3.model.domain.doy
            for hour in r3.model.domain.hour
        }
        assert exposed == expected
        assert len(exposed) == 432

- [ ] **Step 3: Write truth and stream invariance tests**

Assert train/heldout spaces, covariates, generating_theta, generating_theta_obs, opportunistic priors, calibrated priors, annotated known detection 0.85, and full east held-out annotation exposure are unchanged from R2.

- [ ] **Step 4: Run and verify RED**

Run:
    python -m pytest tests/test_v04_r3a_fixture.py -q

Expected: fixture attributes/functions missing.

- [ ] **Step 5: Implement V04R3AFixture**

Use a frozen slots dataclass. Wrap covariate/theta dictionaries in MappingProxyType exactly as R2 does.

- [ ] **Step 6: Implement build_v04_r3a_fixture**

Pseudo-code:

    r2 = build_v04_r2_fixture(source_csv_text, profile="positive")
    spatial = spatial_maximin_sequence(
        r2.train_spaces,
        r2.covariates,
        count=36,
    )
    temporal = temporal_maximin_sequence(
        r2.model.domain.doy,
        r2.model.domain.hour,
        count=12,
    )
    if spatial[:18] != r2.calibration_spaces:
        raise RuntimeError("R3a first 18 sites must equal R2 calibration sequence")

    train_exposed = {
        (space, doy, hour)
        for space in spatial
        for doy, hour in temporal
    }
    heldout_exposed = {
        key
        for key in r2.model.domain.keys
        if key[0] in set(r2.heldout_spaces)
    }
    annotated = StateAnnotatedCount(
        name="annotated",
        state_space=r2.model.streams[2].state_space,
        effort=EffortField({
            key: 8.0
            for key in train_exposed | heldout_exposed
        }),
        detection=KnownDetection(probability=0.85),
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=r2.model.domain,
        species=r2.model.species,
        streams=(r2.model.streams[0], r2.model.streams[1], annotated),
    )
    model.check_design()

Return the immutable R3a fixture using unchanged R2 truth.

- [ ] **Step 7: Run fixture/regression tests**

Run:
    python -m pytest tests/test_v04_r3a_selectors.py tests/test_v04_r3a_fixture.py tests/test_v04_r2_fixture.py tests/test_v04_r2_gate.py -q

Expected: PASS.

- [ ] **Step 8: Commit**

    git add src/esdm/validate/v04_r3a_design.py tests/test_v04_r3a_fixture.py
    git commit -m "feat: add budget-neutral R3a positive fixture"

---

### Task 3: Pure R3a qualification conjunction

**Files:**
- Create: src/esdm/validate/v04_r3a_gate.py
- Create: tests/test_v04_r3a_gate.py

**Interfaces:**
- Produces V04R3AQualificationSummary.
- Produces V04R3ACheck and V04R3ADecision.
- Produces evaluate_v04_r3a_qualification(summary).
- Contains no JAX call and no R3a identification outcome.

- [ ] **Step 1: Write the failing pure conjunction test**

Passing fixture:

    V04R3AQualificationSummary(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        annotated_context_count=432,
        annotated_space_count=36,
        annotated_time_count=12,
        calibrated_context_count=432,
        r2_prefix_preserved=True,
    )

Assert exactly 12 checks pass. Then mutate each field independently to a failing value and assert the corresponding named check fails.

- [ ] **Step 2: Run and verify RED**

Run:
    python -m pytest tests/test_v04_r3a_gate.py -q

Expected: import failure because v04_r3a_gate does not exist.

- [ ] **Step 3: Implement the pure gate**

Implement frozen dataclasses and checks:
- five identification/refusal booleans must be true;
- annotated_context_count == 432;
- annotated_space_count == 36;
- annotated_time_count == 12;
- calibrated_context_count == 432;
- calibrated_space_count == 18;
- calibrated_time_count == 24;
- r2_prefix_preserved is true.

Return passed = all(check.passed for check in checks).

- [ ] **Step 4: Run and commit**

Run:
    python -m pytest tests/test_v04_r3a_gate.py -q

Then:
    git add src/esdm/validate/v04_r3a_gate.py tests/test_v04_r3a_gate.py
    git commit -m "feat: define pure R3a qualification conjunction"

---

### Task 4: Freeze R3a qualification before any identification outcome

**Files:**
- Create: docs/validation/V04_R3A_QUALIFICATION_GATE.md
- Create: tests/test_v04_r3a_gate_freeze.py

**Interfaces:**
- Produces the immutable R3a gate artifact.
- No post-freeze evaluator is implemented here.

- [ ] **Step 1: Write the failing gate-document contract test**

Read docs/validation/V04_R3A_QUALIFICATION_GATE.md and assert it contains:
- 36 spatial sites × 12 temporal contexts;
- 432 state-annotation context opportunities;
- 18 sites × 24 contexts calibrated PresenceOnly;
- exact 13 R2 targets;
- exact R2 A/B/C anchors by reference;
- structural rtol 1e-8 and atol 1e-10;
- practical relative minimum singular value 1e-3;
- condition number 1e3;
- target SD proxy 0.25;
- Fisher ridge 1e-10;
- unchanged R2 sparse refusal;
- unchanged R2 unknown annotated-detection refusal;
- no MCMC in R3a;
- PASS/FAIL no-retuning rule.

- [ ] **Step 2: Run and verify RED**

Run:
    python -m pytest tests/test_v04_r3a_gate_freeze.py -q

Expected: FileNotFoundError.

- [ ] **Step 3: Create the frozen gate document**

Translate the approved design into an executable qualification gate. Include exact selector algorithms, exact counts, exact thresholds, exact refusal profiles, and the 12-term mechanical PASS rule.

The first line of status must be:
    Status: FROZEN BEFORE R3a IDENTIFICATION OUTCOME

- [ ] **Step 4: Run all non-outcome R3a tests**

Run:
    python -m pytest tests/test_v04_r3a_selectors.py tests/test_v04_r3a_fixture.py tests/test_v04_r3a_gate.py tests/test_v04_r3a_gate_freeze.py -q

Expected: PASS.

- [ ] **Step 5: Commit the freeze separately and record its SHA**

    git add docs/validation/V04_R3A_QUALIFICATION_GATE.md tests/test_v04_r3a_gate_freeze.py
    git commit -m "docs: freeze v0.4-R3a qualification gate"

No R3a identification outcome may be run before this commit exists.

---

### Task 5: Post-freeze identification evaluator and guarded one-shot workflow

**Files:**
- Modify: src/esdm/validate/v04_r3a_gate.py
- Create: tests/test_v04_r3a_identification.py
- Create: scripts/run_v04_r3a_qualification.py
- Create: tests/test_v04_r3a_script.py
- Create: .github/workflows/v04-r3a-qualification-once.yml
- Create: tests/test_v04_r3a_workflow.py

**Interfaces:**
- Produces V04R3AIdentificationResult.
- Produces evaluate_v04_r3a_identification(source_csv_text).
- Produces qualification_summary(source_csv_text, identification).
- Produces one fail-closed JSON audit artifact.

- [ ] **Step 1: Write the post-freeze JAX evaluator shape test**

Do not assert PASS. Assert only evidence structure:
- positive: 3 anchors × 13 targets;
- sparse: 3 anchors × 13 targets;
- unknown detection: 3 anchors × 2 targets.

- [ ] **Step 2: Implement positive R3a evidence with unchanged R2 thresholds**

Reuse R2_IDENTIFICATION_TARGETS and v04_r2_identification_anchors on the R3a fixture because truth values are unchanged.

Use exactly:

    STRUCTURAL = {
        "method": "jax",
        "rtol": 1e-8,
        "atol": 1e-10,
    }

    PRACTICAL = {
        "rtol": 1e-8,
        "atol": 1e-10,
        "relative_singular_value_threshold": 1e-3,
        "condition_number_threshold": 1e3,
        "target_sd_threshold": 0.25,
        "fisher_ridge": 1e-10,
    }

Evaluate sparse and unknown profiles using the exact R2 sparse/unknown fixtures, not R3a variants.

- [ ] **Step 3: Implement qualification_summary**

Count actual positive training exposures from stream effort objects and populate the pure 12-term summary. Compute prefix equality from annotated_spaces[:18] == calibrated_spaces.

- [ ] **Step 4: Write script contract tests**

The public script must expose only --output and harmless audit/display options. It must not expose site count, time count, target-SD, singular-value, condition-number, anchor, or refusal controls.

Constants:
- ANNOTATED_SITE_COUNT = 36
- ANNOTATED_TIME_COUNT = 12
- ANNOTATED_CONTEXT_COUNT = 432
- CALIBRATED_SITE_COUNT = 18
- CALIBRATED_CONTEXT_COUNT = 432
- FROZEN_GATE_COMMIT = Task 4 freeze SHA

- [ ] **Step 5: Implement scripts/run_v04_r3a_qualification.py**

The coordinator:
1. writes INFRASTRUCTURE_BLOCKED before work;
2. downloads/verifies pinned source;
3. runs evaluate_v04_r3a_identification;
4. builds qualification_summary;
5. runs evaluate_v04_r3a_qualification;
6. serializes anchor-level evidence and selected site/time identities;
7. writes status PASS or FAIL;
8. contains no MCMC call.

- [ ] **Step 6: Write workflow contract tests**

The workflow must:
- run only on feature/v04-r3-budget-neutral-design;
- require docs/validation/V04_R3A_RUN_AUTHORIZED;
- run a precheck without authorization;
- run qualification only when authorized;
- upload artifact with if: always();
- contain no fit_numpyro, num_warmup, num_samples, or replicate loop.

- [ ] **Step 7: Implement the workflow**

Use Python 3.12 and install .[dev,inference] for JAX availability. Timeout 90 minutes.

Precheck must include all R3a tests plus the relevant R2 sparse/refusal tests.

- [ ] **Step 8: Run exact-head CI without authorization**

Require:
- ordinary Python 3.10/3.11/3.12 CI green;
- R3a precheck green;
- qualification job skipped.

- [ ] **Step 9: Verify gate immutability**

Diff only docs/validation/V04_R3A_QUALIFICATION_GATE.md from its freeze commit; expected no output.

Also verify all R2/V031/V032 frozen files unchanged.

- [ ] **Step 10: Commit post-freeze evaluator/workflow**

    git add src/esdm/validate/v04_r3a_gate.py tests/test_v04_r3a_identification.py scripts/run_v04_r3a_qualification.py tests/test_v04_r3a_script.py .github/workflows/v04-r3a-qualification-once.yml tests/test_v04_r3a_workflow.py
    git commit -m "feat: add frozen R3a qualification evaluator"

---

### Task 6: Execute R3a exactly once and freeze PASS or FAIL

**Files:**
- Create before run: docs/validation/V04_R3A_RUN_AUTHORIZED
- Create after run: docs/validation/V04_R3A_RESULTS.md
- Create after run: docs/validation/V04_R3A_FROZEN_RESULTS.json

**Interfaces:**
- Produces the final auditable R3a qualification result.
- Does not create R3b unless result is PASS.

- [ ] **Step 1: Add authorization only after Task 5 pre-outcome verification**

Marker text must state the Task 4 freeze SHA and explicitly say it does not alter 36 × 12, 18 × 24, thresholds, anchors, refusal profiles, truth, or PASS rule.

- [ ] **Step 2: Run the guarded workflow once**

Do not edit the gate or selectors while it runs.

- [ ] **Step 3: Independently verify artifact provenance**

Verify GitHub artifact digest, independently downloaded ZIP SHA256, source Git blob SHA1, exact head SHA, and exact gate freeze SHA.

- [ ] **Step 4: Recompute the 12-term decision**

Confirm:
- five identification/refusal booleans;
- 432 annotated contexts;
- 36 annotated sites;
- 12 annotated times;
- 432 calibrated contexts;
- first-18 prefix preservation.

- [ ] **Step 5: Freeze PASS or FAIL without retuning**

If FAIL:
- name failing targets/anchors/diagnostic reasons;
- state that R3b is not created.

If PASS:
- state only that the exact 36 × 12 design qualifies for a separately frozen R3b;
- do not claim v0.4 promotion.

Machine-readable result must also record selected site IDs and temporal contexts in order plus all anchor-level evidence.

- [ ] **Step 6: Remove authorization and re-run exact-head verification**

Require ordinary CI green, R3a precheck green, qualification job skipped, gate byte-identical, and all R2/V031/V032 frozen records unchanged.

- [ ] **Step 7: Open the stacked R3a PR**

Base: feature/v04-frozen-validation-r2
Head: feature/v04-r3-budget-neutral-design

Title:
- PASS: Qualify budget-neutral v0.4-R3a state design
- FAIL: Record budget-neutral v0.4-R3a qualification FAIL

Do not merge.

---

## Plan self-review result

### Spec coverage

- deterministic 36-site spatial selection — Task 1.
- deterministic 12-context temporal selection — Task 1.
- exact 432 annotated budget — Task 2.
- unchanged 18 × 24 calibrated PresenceOnly — Task 2.
- first-18 equality to R2 — Tasks 2 and 3.
- unchanged R2 truth/streams except positive annotated geometry — Task 2.
- unchanged 13 targets, A/B/C thresholds — Task 5.
- unchanged sparse refusal — Task 5.
- unchanged unknown-detection refusal — Task 5.
- no outcome before freeze — Tasks 4 and 5.
- no MCMC in R3a — Tasks 4–6.
- FAIL prevents R3b; PASS only qualifies R3b — Task 6.
- R2/V031/V032 immutability — Global Constraints and Tasks 5–6.

### Type consistency

The plan uses one naming surface:
- spatial_maximin_sequence
- temporal_maximin_sequence
- V04R3AFixture
- build_v04_r3a_fixture
- V04R3AQualificationSummary
- V04R3ADecision
- V04R3AIdentificationResult
- evaluate_v04_r3a_identification
- evaluate_v04_r3a_qualification

### Review-focus coverage

All five review-focus risks have an explicit owning test in Tasks 1, 2, 4, or 5.

### Placeholder scan

The plan contains no unresolved implementation markers, unspecified test steps, or undefined later-task interfaces.
