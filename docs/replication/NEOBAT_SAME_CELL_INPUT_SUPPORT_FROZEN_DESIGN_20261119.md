# NeoBat prospective same-cell input-support audit (v1, response still unopened)

Date: 2026-11-19. Research child branch only; main and the frozen M0/M1/M3/N1 ecological contract are not modified.

## Purpose and stopping boundary

The 84/754 source-qualified bat×country folds were based on counts of **separately observed** bats and potentially linked fruit plants within *countries*. They do not establish that bat and plant records occur within the same 25-km cell. Before any plant crossfit or bat predictive comparison, measure **geographic support for the proposed predictor** with the two already-minted DOI archives, without treating non-observation as absence.

This is an explicitly **exploratory, response-opened discovery source audit**. It cannot preserve an independent heldout bat response, demonstrate feeding, estimate fruit abundance, support a causal mechanism, or establish M3 superiority. Do not change fold eligibility or report any M3–M1 effect from this output.

## Source and data freeze

1. Fixed 84 bat×country pairs from `docs/replication/neobat/NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json`, 19 species and 17 countries. No data-dependent additions or exclusions.
2. Original DOI bat `10.15468/dl.nxu727` 85,912 rows; original ZIP SHA-256 `fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0`.
3. Original DOI plant `10.15468/dl.xwc5zf` 367,988 rows; original ZIP SHA-256 `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`.
4. Species-name source table and pinned original NeoBat citations from `scripts/neobat_gbif_metadata_preflight.py` at author commit `d25292d19be32a85a21c60384a3f2d818e8081de`.
5. Source embargo across ALL original NeoBat sites: `docs/replication/neobat/NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json`.
6. Must exactly match existing full-DOI QC per-species×country known-precision cell counts; archive/metadata/source discrepancies STOP. Do **not** submit a new GBIF download request.

## Frozen data-handling rules

- Only GBIF matching accepted species keys, query years 2000–2025, country in the fixed 29-country universe, valid geographic coordinates and known coordinateUncertaintyInMeters <= 12,500 m enter cell supports.
- EPSG:4326 -> equal-area EPSG:6933; 25,000 m grid with index `(floor(x/25000),floor(y/25000))`. Same country and exact same cell index required. This 25km aggregation does NOT establish interacting individuals, feeding or a 25-km detection radius.
- Cells with multiple observations collapse to a **set**, not pseudo-replication. Also retain `datasetKey` sets in process memory so a more conservative overlap requires at least one distinct source dataset across bat and plant at that cell. Distinct dataset IDs do not establish independent effort.
- For each fold, source-linked partners come from *frugivory, frugivore guild* author rows, with heldout-country original-site reference embargo. Partner species and generic plant pool both must have >=5 known-precision cells in the heldout country and >=20 known-precision cells **outside** it.
- For every one of the **exact 84** frozen folds, report denominator `N` of known-precision bat cells within the country and aggregate counts of bat cells containing >=1 or >=3 eligible linked partner plant species, >=1 eligible generic plant species, >=1 eligible nonpartner plant species, and >=1 partner with different plant/bat `datasetKey`. Also report eligible partner-pool, generic-pool and literature-reference counts. **Do not** export coordinates/cell IDs, source dataset IDs, event IDs, plant co-observation matrices, or record rows.
- Runtime source counts and derived eligible pair roster must exactly agree with pre-open frozen roster and source QC; any discrepancy fails closed, without changing thresholds or swapping data.
- The output includes all 84 folds (including zero overlaps). Every cell is an observed *presence-record cell*, and a cell without other taxa is a **missing record** not a verified absence.
- No 3D, social information, fruiting-time, plant-relative-suitability SDM, M0/M1/M2/M3/N1 heldout AUC, or independent replication may be inferred from these aggregate support counts.

## After this audit (irrespective of sign)

If the fixed source passes, retain the result as a **discovery feasibility** receipt, then independently prepare plant outcountry cross-fitted continuous suitability surfaces for all 255 plants, a comparable abiotic/forest/terrain/effort grid, and source-audited target-group background. Fit only on identical holdouts and compare the prospectively primary M3–M1 and M3–N1 contrasts. The original source has already been opened for quality and this new colocation audit; external independent confirmation still needs a genuinely distinct data period or source.
