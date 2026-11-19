# NeoBat prefit empirical source gates — 25km overlap and 255-plant crossfit trainability

Date: 2026-11-19. Child research branch `analysis/neobat-25km-colocation-gate-20261119`, derived from unmerged PR #244. This document compares **input feasibility**, not ecological held-out model performance.

## Executed original ZIP same-cell source audit

Source-free test [Actions #44527414488](https://github.com/zuizui0223/esdm/actions/runs/44527414488) succeeded. One-shot original-source [Actions #44527705905](https://github.com/zuizui0223/esdm/actions/runs/44527705905) succeeded. The original GBIF bat/plant ZIP SHA-256s and all strict species×country 25km cell counts were replayed exactly; the entire original 84/754 eligibility roster was reproduced with no change to thresholds.

Output: `docs/replication/neobat/same_cell_source_support.json`.

- 82/84 frozen bat×country folds include >=1 known-precision **published linked** plant occurrence in the **same EPSG:6933 25km cell** as some bat occurrence.
- 66/84 folds include a bat cell with >=3 distinct source-linked plant species recorded in the same cell.
- 81/84 folds include linked-plant cell co-observation with a **different GBIF datasetKey**. Different dataset keys are not independent sampling or direct feeding evidence.
- Among 2,545 species×country bat recorded cell entries, 1,682 cells had >=1 linked plant record; 2,202 had any eligible generic plant; 2,009 had an eligible nonpartner plant; 928 had >=3 linked plant names. These counts share geography between species and are **not independent observations** or a null-model comparison.
- Two zero-overlap source pairs were *Carollia castanea* × Peru and *Uroderma bilobatum* × Brazil. Retain both; zero GBIF overlap is not absence of the actual fruit plant. No retroactive fold selection is allowed.

**Interpretation ceiling:** This supports geographic *observability* of many potential predictors and refutes only a claim of no documented same-cell co-recording. Generic plants were also recorded in all 84 folds. Co-occurrence is not feeding, within-cell contact, abundance or proof that source-linked identities outperform degree-rewired controls.

## Separate full-cohort outcountry plant training feasibility

[Actions #44528434955](https://github.com/zuizui0223/esdm/actions/runs/44528434955) parsed **only the already archived full original GBIF QC country-cell summaries** (no raw occurrences, new GBIF download, bat response, plant SDM or AUC).

Output: `docs/replication/neobat/plant_crossfit_source_trainability.json`.

The original design requires the **same 255 named plant species**, scored for every cell of every 17-country outer holdout. With the conservative rule of >=20 known-precision 25km plant-training cells **outside** the heldout country:

- Only **106/255** fixed plants have >=20 outside-country cells in **every** one of 17 heldout countries.
- The number of trainable plants within each country ranges from **138 to 158**.
- **19/255** plants have zero strict-quality 25km recorded cells across all sampled countries (four have zero indexed-quality cells, including unknown uncertainty).
- Thus **0/84 folds** can independently fit full 255 distinct plant SDMs under this training denominator. A predictor for a plant with no training data must **not** be silently set to zero and then interpreted as observed unsuitability.

This is a genuine prefit identifiability constraint; it is not a negative test of the bat fruit-resource hypothesis.

## Scientific decision

1. **Keep the frozen v1 255-plant M0/M1/M3/N1 primary benchmark unestimated.** No positive or negative ecological effect can be extracted from source-support counts.
2. For a separately labeled **exploratory v2**, consider the **same 106 globally crossfit-trainable plants**, fixed for all 17 holdouts without inspecting any heldout bat AUC. First verify that the full publication-reference embargo still leaves >=3 true linked plants from >=2 original independent NeoBat references per selected bat×country fold. Report all 84 gate outcomes, including failures.
3. Even v2 requires independent climate, topography, forest, effort and plant cross-fits, plus bat presence–target-group background heldouts. Only then may exploratory heldout comparisons be estimated. Confirmatory validation needs another unopened source or period.

No changes to `main`, frozen boids/batter results, raw protected locations, or prior ecological evidence are authorized by these source-input audits.
