# NeoBat global botanical source-disjoint plant universe and frugivory-link feasibility (new exploratory branch)

Date: 2026-11-19. **This is source-only, not ecological prediction.** The original 255-plant v1 model and 106-plant exploratory v2 were already source-audited; M1/M3/N1 bat relative-rank performance remains unestimated.

## Fixed inputs and one deterministic selection

- Original GBIF botanical dataset `10.15468/dl.xwc5zf` **without downloading occurrences again**. Read only the previously verified 1,802 aggregate source gate `plant_106x17_global_source_embargo.json` whose source provenance includes original full DOI ZIP SHA-256 `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`; exact all-1,802 original dataset-matched source-input replay status must PASS.
- Fixed 106 original plant names with SHA `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`, all original **17 country holdouts**.
- Deterministically select plants for which the *source-disjoint* existing input gate recorded **>=20 training focal and other-plant target background cells for each of the 17 countries after holding out all datasetKey sources observed in that country**. **Expected count 35** from the previous aggregate; require exactly 35, and SHA the exact alphabetically sorted names before opening any author frugivory-link outcomes. No selection based on previously computed AUC, same-cell source overlap, source degree or bat species.
- Read author-published `gflorezm/NeoBat_Interactions` original RECORDS/SITES source at pinned original commit `d25292d19be32a85a21c60384a3f2d818e8081de` with original source blob SHA validation; no new GBIF download or bat observed occurrence ranking.

## Frozen partner and null input gate

- Keep all original **84 bat×country folds** from `NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json`. The original main bat target-group background source gate and source-only v2 106-partner eligibility remain independent prerequisite controls.
- For each heldout country, exclude **all original NeoBat publication references from the complete author site table that have a site in the heldout country**, not just refs found in a frugivory subset. Use only actual author-source `Frugivory` / `Frugivore` records for accepted 26 bats.
- Source-linked training plants must be in the single frozen 35-plant set and be independently represented by **>=5 known-precision 25km GBIF recorded cells in the heldout country** (and >=20 source-disjoint outcountry training *source cells* by selection). Source-eligible focal bat if >=3 distinct partner plant names from >=2 original outcountry source references, exactly the same literature minimum as previous v1/v2.
- Structural N1 feasibility if the source-derived 35-plant bipartite network after original publication embargo admits a valid focal-specific two-edge swap preserving both bat and plant degrees. This is *not* statistical N1 exchangeability, effective rewires or model performance.
- Preserve all 84 folds even when stopped for 35-plant partner count, source-reference, N1 or prior bat target-group background restrictions. Summarize the joint source-only eligible bat×country count and per-country concentration. No replacement species/country or threshold relaxation.
- Separately cross-tabulate the **original pre-computed** full-106 country raster-nodata training gate (`full106_raster_trainability_gate.json`) against the 35 plant names. This indicates species whose original unembargoed raster training count was inadequate. **Do not** claim a new full 35-plant source-and-raster eligibility from taking the intersection: joint source exclusion + raster nodata has not been recomputed and can only reduce usable sources. Clearly label any such count as an *upper bound*.
- Never export original coordinates, exact source site locations, source dataset IDs, per-cell species matrices, raw GBIF data or bat response records; only fixed 35 names/digest, species×country input source counts and aggregate null feasibility.

## Interpretation ceiling

35 plants is **not** a confirmed plant ecological distribution model, vegetation density, fruiting abundance, true survey-independent observations or actual food use. The criterion is source-data feasibility after strict dataset-key disjointness. Even a positive source-link gate for bats cannot be promoted to empirical M1/M3 superiority. The 255-plant v1 contract is unmodified, and the 106-plant v2 source-rank test is already explicitly exploratory. Full ecological comparison requires *jointly* raster-valid, independently characterized vegetation/sampling effort and cross-fitted plant model predictors over identical bat target-background cells.
