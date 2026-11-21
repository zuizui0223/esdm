# NeoBat v2 source-only 106-plant qualification result

Date: 2026-11-19. Authoritative receipt:
`docs/replication/neobat/v2_106plant_reference_input_gate.json`.

## Verified by source-only GitHub Actions

[Actions #44529547264](https://github.com/zuizui0223/esdm/actions/runs/44529547264) completed successfully. Before opening author-source reference rows in this new workflow, the alternative 106-plant input gate and 84-fold denominator were fixed in `NEOBAT_V2_106PLANT_EXPLORATORY_SOURCE_GATE_FROZEN_20261119.md`. No GBIF bat response, new GBIF occurrence row, new ZIP download, same-cell result or heldout model performance was accessed in this workflow. Original NeoBat source files were retrieved with pinned commit/blob SHA validation.

- Initial plant candidate universe 255; country-holdout intersection with >=20 known-precision training cells outside **each** of 17 countries yields the same **106** fixed plants.
- Sorted plant-universe SHA-256: `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`. This prevents source-universe drift across subsequent folds.
- Of all **84 original** bat×country source-qualified folds, **83** retain >=3 source-recorded partner plant names in this 106 universe and >=2 outcountry publication references after the **complete** original-site publication embargo.
- The single source-only failure is *Sturnira tildae* × Colombia (CO): only **2** retained partner names, albeit 2 source refs. Preserve it in the denominator and report stop rather than change the minimum.
- All **83 source-qualified** folds have at least one mathematically legal two-edge, bipartite-degree-preserving swap that changes the focal bat's partner identities. This is *structural null feasibility*, not N1 calibration, exchangeability, adequate Monte Carlo power, or effect size.
- Main conclusion remains **input-feasibility only**. The original 255-plant v1 contract is unmodified; no M0/M1/M2/M3/N1 exploratory or independent ecological heldout prediction result has been estimated.

## Next genuine ecological model stages

Freeze environmental raster source identities (WorldClim climate, defensible topography and independently sourced vegetation), spatially independent target-group sampling effort/background, and 106 plant relative-suitability models fit **without** occurrence records from each withheld country. Build the same M0/M1/M3/N1 design on paired heldout bat presence–target-group background responses. Keep per-bat×country and per-country losses, failed-fold stops and country-cluster inference rather than treating 83 pairs as 83 independent studies.

Because the same source records and 84-region preflight have already been inspected, any new test on them remains **exploratory discovery**, not unseen external replication.
