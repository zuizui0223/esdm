# NeoBat full 106-plant raster-screened trainability: practical 51-fold source gate

Date: 2026-11-19. Source-only aggregate gate derived from the **already completed** [106×17 original DOI source-rank diagnostic](https://github.com/zuizui0223/esdm/actions/runs/44538948274), without downloading GBIF archives, re-reading original coordinates, refitting plant or bat models or using heldout source rank performance for selection.

Frozen before this new outcome:
`docs/replication/NEOBAT_FULL106_RASTER_TRAINABILITY_FROZEN_20261119.md`.

Actual [GitHub Actions #44542532349](https://github.com/zuizui0223/esdm/actions/runs/44542532349) source-free regression and aggregate evaluation **PASS**. Authoritative record:
`docs/replication/neobat/full106_raster_trainability_gate.json`.

## All 17 original countries, fixed 106-plant universe

For every plant in the fixed 106 names, test whether original **outside-country training-only**, same-GBIF-`datasetKey` focal and other-plant background retain **at least 20 unique cells per class after the original BIO1/BIO12/ELEV source no-data screen**.

- **15/17** original country holdouts retain all 106 distinct plant-species training fits.
- Colombia: **103/106**, missing only *Cecropia ficifolia*, *Solanum asperolanatum* and *Stenocereus griseus* at the fixed >=20 training-cell gate.
- Mexico: **104/106**, missing *Ficus crocata* and *Sideroxylon foetidissimum*.
- For both Colombia and Mexico, the fixed full-106 predictor collection is **unavailable under the frozen fitting threshold**. The missing species must not be filled with zero predicted suitability nor silently removed after inspecting outcomes.

## Intersection with the complete original 84 bat-fold source roster

The previously qualified **79/84** bat×country folds with both fixed-106 published source-link input and strict target-group bat background drop to **51/84** after requiring complete-106 *outside-country plant training*.

The 51 are distributed across **15 bat species and 11 heldout countries** (not 51 independently replicated studies):

| Country | Remaining bat×country pairs |
|---|---:|
| Costa Rica (CR) | 10 |
| Panama (PA) | 7 |
| Ecuador (EC) | 6 |
| French Guiana (GF) | 6 |
| Peru (PE) | 5 |
| Brazil (BR) | 4 |
| Honduras (HN) | 4 |
| Guatemala (GT) | 3 |
| Belize (BZ) | 2 |
| Nicaragua (NI) | 2 |
| El Salvador (SV) | 2 |
| **Total** | **51** |

No other original 84 bat folds pass all three *input-quantity* conditions. This is **not** an M1–M3 effect size or a post-hoc positive/negative biological result; the original 84-fold denominator remains visible.

## What remains genuinely unresolved before ecology

Even a 51-fold country pilot would require the **actual full 106 relative plant-suitability maps** for all bat and target-group-background grid cells, not just training row counts or source-record AUCs. Independently measured forest/vegetation and target-group recording bias or calibrated detection proxies must be made comparable across 11 heldout countries. The existing WorldClim abiotic baseline spans 1970–2000 versus GBIF occurrences 2000–2025. Observed source-intensity (`n` other plants recorded) is **not independent botanical survey effort** and using it as biological resource abundance is unsupported.

Once the missing inputs and source/bias independence are demonstrated, exploratory pairwise bat source-rank AUC could be compared across M0/M1/M3 and literature degree-preserving N1 with per-country clustering and all failed folds reported. The original **255-plant v1 remains unestimated**; **no bat M3−M1 or M3−N1 was fitted here**. `main` unchanged.
