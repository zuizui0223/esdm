# v0.4 Gate R1 invalidation record

Status: **INVALIDATED BEFORE RESULTS INSPECTION**

The first v0.4 promotion gate was frozen at
`551ed43c9d602f39ee37e54e1f4ea230338d749d` and an outcome workflow was
authorized. During execution, but before any outcome log, replicate value, summary,
artifact, PASS/FAIL result, or fitted parameter result was inspected, the gate design was
found to be insufficient for the intended v0.4 claim.

The R1 outcome is therefore excluded from scientific evaluation and must not be used to
set, tune, justify, or relax any later threshold.

## Design defects discovered before result inspection

1. The positive profile treated observation effort and detection as known. This did not
   carry forward the v0.3.2 requirement that ecological and observation processes be
   separated under unknown observation effort plus partial calibration. In particular,
   activity and detection enter the annotated rate multiplicatively, so a known-detection
   positive profile did not test the main new activity/observation separation problem.

2. Activity and state truth used only spatial covariates. Observation effort was constant.
   DOY and hour therefore contributed repeated counts but no distinct ecological or
   observation-process signal.

## Consequence

R1 remains in git history for auditability but is superseded. Its workflow output is not
to be inspected or cited as evidence.

R2 must be frozen before any R2 outcome-producing run and must:

- include unknown observation-process parameters in the positive profile;
- use partial calibrated streams to resolve those parameters;
- include explicit DOY and hour effects in activity and state truth;
- include temporal variation in observation effort;
- include negative controls showing that removal of calibration restores the intended
  non-identification or weak-separation behavior.
