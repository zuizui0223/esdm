# E5: pass-referenced detection calibration exists, but geographic transfer is still missing

**Evidence:** Findlay, Briers & White (2020), *Mammal Research*,
[doi:10.1007/s13364-020-00478-y](https://doi.org/10.1007/s13364-020-00478-y).
The article explicitly links a [public GitHub data/code repository](https://github.com/melaniefindlay/CT-Detection). At pinned commit
`abc72f535bb59ebed202fb7acca852fc1647e97a` it contains separate
`TRIGGER_*.csv` and `REGISTRATION_*.csv` data files and an R analysis script.
The script fits binary `TRIGGER` conditional on independently identified passes,
and `CAPTURE` conditional on `TRIGGER=1`, grouping by `CT.POS`.
These variable-level statements are based on source code, **not on reading CSV
data rows**.

## Correct observational denominator

CCTV continuously monitors the site. It documents animal passages even when the
motion-triggered camera misses them:

`P(recorded | pass)=P(trigger | CCTV-confirmed pass)*P(registered | trigger, pass)`.

This is a direct independent measurement of *conditional* camera detection
given an observed animal pass. It resolves an important piece of the E5
activity-detection product that two ordinary nearby camera traps cannot resolve.
This is an actual empirical calibration design, not a new synthetic gate.

However, the method does **not** make broad ecological encounters fully
observable. `P(pass | animal present in surrounding landscape)` is a
separate ecological/placement problem, as the paper distinguishes.

## Why it does not qualify for the frozen geographic E5 test

The paper studied two contexts: a wild fox/badger run in southeast Scotland
(21 February–14 April 2017), and a captive otter enclosure in southwest England
(14 November–5 December 2017). Each used **four camera-trap positions** under
continuous CCTV reference. The sites differ in geography, species, wild versus
captive condition, and study season. Thus even if some camera detection parameters
can be estimated within each site, the two sites do not provide a properly
crossed, replicated geographic comparison.

- **G4 component:** independent known-pass denominator demonstrated for trigger
  and registration.
- **G3:** cross-geographic activity versus detection effects are confounded with
  species and study context; no valid shared transfer claim.
- **G5:** four camera positions per area, versus required 20 train / 10 heldout.
- **G6:** fewer than two months at each site, versus six months per split.
- **Diel G4:** event timestamp column is unverified from the source-only review;
  do not claim diel calibration or fit a time-of-day detection curve.
- **E5 original qualification:** **not passed**; do not increment the 17 screened
  discovery candidates or treat this as an eighteenth candidate.

**Concrete next data requirement:** continuous-reference or known-pass records
with physical camera and event/occasion identity, timestamps including *misses*,
concurrent trigger/registration data, real geography×source crossing, and
>=20/10 physical locations and six months per geographic split.

There is no authorization to open this donor's observation rows, fit new
models, recalibrate wild-pig/Rhode Island data, or rerun earlier one-shot results.
Do not transport a sensor calibration between incompatible camera models,
taxa, exposure contexts or deployment geometries without independent evidence.

For source provenance and machine-readable no-claim boundaries see
`E5_INDEPENDENT_DETECTION_CALIBRATION_DONOR.json`.
