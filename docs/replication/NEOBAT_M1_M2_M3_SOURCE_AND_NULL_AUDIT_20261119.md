# NeoBat M1–M3 verification addendum: corrected source workflow and M2 decomposition

Date: 2026-11-19. Branch: `analysis/neobat-m1-m3-and-source-gate-audit-20261119`.
Target: research PR #244 branch, **not main**. This is a software/input
audit, not an ecology result. The original preregistered
`NEOBAT_M0_M1_M3_PREDICTIVE_BENCHMARK_CONTRACT_20261119.md` remains unchanged.

## Definitions and protected primary inference

- **M0:** abiotic, forest, topography and effort.
- **M1:** M0 + generic cross-fitted all-plant relative suitability B(x).
- **M2 (new exploratory decomposition only):** M0 + outcountry
  literature-documented focal fruit-partner suitability R_s(x).
- **M3:** M1 + R_s(x).
- **N1:** M1 + degree-preserving rewired-partner R_s^swap(x).

M2 reports only `M2−M0` and `M3−M2` as diagnostics. It does **not**
replace the frozen ecological `M3−M1` and `M3−N1` tests or change
fold eligibility, fitted transforms, training labels, geographic
holdouts or model-selection rules. If M2 appears useful, it remains
exploratory until separately frozen and validated.

## Actual source verification and failing workflow

Workflow [run 44520696299](https://github.com/zuizui0223/esdm/actions/runs/44520696299),
job 135548213969, evaluated the SHA-pinned official WorldClim v2.1
archive on 2026-11-19. The unit checks completed (3/3). The source
step logged `WORLDCLIM_SOURCE_PREFLIGHT SOURCE_GEOHEADER_QUALIFIED`
and `NEOBAT_WORLDCLIM_SOURCE_PREFLIGHT_EXIT=0`. Its immutable artifact
is [14527584620](https://github.com/zuizui0223/esdm/actions/runs/44520696299/artifacts/14527584620)
(artifact ZIP SHA-256 `540c7f859a0e4218845430b4401167f67c2eb97a2ea93bc8ff449c382bb300d9`).

The *overall* job nevertheless failed because the runner wrote
`worldclim_bio1_bio12_corrected_source_preflight.{json,txt}` but the
subsequent artifact/commit/gate steps accidentally addressed
`worldclim_bio1_bio12_source_preflight.{json,txt}`.
That older prefix pointed at a historic source STOP. GitHub Actions
`conclusion=failure` is therefore an **artifact/receipt wiring error**,
not evidence that the corrected raster source failed.

This patch makes all three downstream consumers use the **exact**
corrected prefix, treats a missing archive input as an error, and adds
a source-free regression test. The already completed one-shot source
request need not be repeated merely to correct file-path wiring.
The workflow run remains recorded as failed; the precise source success
is evidenced in its log/artifact, and future corrected execution
cannot promote an older STOP receipt.

## Null model identifiability

The earlier synthetic receipt had held-out AUCs M0=0.5, M1=0.5,
M3=1.0 and mean N1=1.0: the *specific toy fixture* demonstrates
M3−M1 signal retrieval but **not** evidence that actual partner
identities beat a rewired network. The comparator now also reports
the number of distinct focal-bat partner sets in N1 draws and the
number of draws retaining original partners. If the entire network
can rewire but **the focal bat's partners cannot change**, it fails
closed with `NULL_FOCAL_LINK_IDENTITIES_INVARIANT`. This avoids
mistaking unrelated-species edge swaps for a valid focal null.

## Actual field-result ceiling

The DOI-backed bat and plant downloads and strict 84/754 input roster
from PR #244 qualify candidate folds. They do not supply complete
plant cross-fitted suitability surfaces, spatial source-independent
target-group background or bat model evaluation. **M2 or M3
ecological predictive gain: not estimated**. No source-only result
is merged into a manuscript as feeding mechanism, social information,
individual specialization or causal evidence.

## Reproducible source-free checks

```bash
python -m unittest discover -s tests -p 'test_neobat_model_comparison_core.py' -v
python -m unittest discover -s tests -p 'test_neobat_worldclim_corrected_workflow_paths.py' -v
```

No raw protected animal locations or original GBIF row-level source
were added by this patch.
