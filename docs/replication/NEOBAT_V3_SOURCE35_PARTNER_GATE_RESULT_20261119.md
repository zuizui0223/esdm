# NeoBat v3 source-disjoint 35-plant literature/N1 input feasibility result

Date: 2026-11-19. Frozen design before result:
`docs/replication/NEOBAT_V3_SOURCE35_PARTNER_FEASIBILITY_FROZEN_20261119.md`.

## Verified original-source execution

- Source-free original 1,802-row selection and 84-fold regression [Actions #44544468114](https://github.com/zuizui0223/esdm/actions/runs/44544468114): **PASS**.
- Original pinned author NeoBat RECORDS/SITES source and full 84-fold publication embargo [Actions #44544712542](https://github.com/zuizui0223/esdm/actions/runs/44544712542): **PASS**.
- Output: `docs/replication/neobat/v3_source_disjoint35_partner_gate.json`. Source-only. No GBIF occurrence rows, source dataset IDs, fine-scale cell IDs/coordinates, model predictions or per-fold ecological AUC exported.

## Fixed source eligibility without biological AUC

| Frozen source quantity / network requirement | Original 84 bat × country folds |
|---|---:|
| Original bat-country candidate accounting | 84 |
| A globally fixed 35-plant subset source-trainable in all 17 countries with heldout country GBIF datasetKey globally excluded | 35 plants (NOT 35 bat folds) |
| >=3 source-literature documented partner plants with >=5 original heldout-country known-precision plant cells and >=2 training original NeoBat references, after the COMPLETE 200-site reference embargo | **66 / 84** |
| Above AND at least one legal focal-identity degree-preserving N1 2-edge swap | **66 / 84** |
| Above AND bat 25km presence/background source quantity qualifies | **63 / 84** |
| Above AND the *older*, **non-source-disjoint full106** raster input gate passes (only a diagnostic intersection, **not** true 35-plant raster source qualification) | **40 / 84** |

The globally fixed source-disjoint35 plant-name list has SHA-256
`5f6ee54473b074b2b5329b1ddd9cc966e739f4f12b93db75154ce59a9f7b92ee`.
The list was defined solely by previously frozen full-DOI source trainability across all 17 countries, with **no selection by plant AUC, trait, local bat records, overlap or M1/M3 results**.

Eighteen bat×country folds lack the fixed >=3 partners / >=2 references under this smaller plant pool; they remain explicitly recorded, not discarded after outcomes. Particularly, *Carollia brevicauda* and *Uroderma bilobatum* lose multiple country folds. This is a fixed-source candidate restriction, not evidence of absence of real food plants.

## What this establishes—and what it does not

**An operationally source-disjoint botanical subpool and a substantial original fruit-link network still exist** despite removing shared GBIF source datasets. That makes an exploratory research program possible, but the 63/84 are **input candidates, not 63 measured successful transfer effects**. A mathematically possible 2-edge swap does not prove a well-mixed N1 null or that N1 loses predictive ability.

Next execution gate: with the same 35 fixed names and all original 17 countries, re-stream original plant source and sample the original verified WorldClim BIO1/BIO12/ELEV at 25km source-matched train cells *after* country+dataset embargo. Require >=20 strict positive and background cells **after raster nodata** for every one of 35×17 predictor folds, and preserve all 595 original pair outcomes. This must be a separate source-only gate and cannot reuse the earlier full106 raster pass as a substitute. Then source-disjoint plant SDM scores at bat/background cells require fixed forest/effort and leakage checks before any M1–M3 ecological claim.

DatasetKey-disjointness is not survey-team/provider independence or actual plant abundance/fruit availability; the same original GBIF source has been repeatedly inspected. The frozen original 255-plant model and primary bat M3–M1/N1 remain unestimated and `main` unchanged.
