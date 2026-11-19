# NeoBat next external tree-survey resource: BCI Dryad 2026 API file-manifest freeze

Date: 2026-11-19. Research branch only, `main` unchanged. This is a **new original-author external botanical dataset registry check**, responding to the completed weak GBIF source-geometry shadow result and not an independent bat M3 validation.

## Fixed source before any new API response

- Dataset: Wright et al. 2026 Barro Colorado Island (BCI), Panama canopy-tree survey, published DOI `10.5061/dryad.1g1jwsvc3`. Public publisher landing page `https://datadryad.org/dataset/doi:10.5061/dryad.1g1jwsvc3`. Previously confirmed page HEAD HTTP 200 in the distinct NeoBat independent-source registry, but **source biological records and file inventories were not accessed** by that registry.
- Dryad official public v2 REST metadata endpoint: `https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.1g1jwsvc3`; from its self-contained public `_links`, follow only the same-host version metadata and public file listing. No downloaded original file bodies, coordinates, tree measurements, species tables or animal data in this stage. No API authentication, no uploads/POST or source substitution.
- Source provenance is critical: record exact dataset identifier, public dataset ID, current publication status, version number/id/updated date, file-list size/count, file paths/names, original file sizes, `digestType`/`digest` if supplied, and selected public metadata links. If the API is unavailable, gated, lacks version/file links, responds inconsistently, or requires credentials, preserve explicit `SOURCE_STOP` status; no fallback to scraped or made-up records.
- Resolve Dryad hypermedia `_links` only if HTTPS host `datadryad.org` and path begins `/api/v2/`. Follow a maximum of 10 file-list pages (100 files/page) with publisher-provided next links; require list count consistency and no duplicate file IDs. Cap JSON response at 2MB and each GET to 40 seconds. Never download any `stash:download` link in this metadata stage.
- Export only DOI/metadata and public *file names*, sizes and digests. No tree plot rows, fine location, taxa, original file bytes, plant source GBIF row reuse, bat responses or per-cell predictions.
- This source is a **single Panama locality**, not one of 11 independent geographic replicates. The described canopy-tree stem counts are possible ecological abundance proxies, but not actual ripe fruit supply or bat dietary intake. It must not automatically validate original 35- or 106-plant relative suitability across 11 bat source countries. Frozen primary original v1 255-plant M3−M1/N1 remains unestimated.
- If the data files are publicly available and their size/digests/authors verified, a **separate subsequent freeze** is needed before inspecting original biological species data, independently testing the fixed original 106 plant taxon crosswalk and reporting all 106 matches/failures.

## Reproducibility/claim ceiling

This is a source-file metadata verification only. Source availability does not equal usable numerical abundance, independently sampled bat responses, geographic or mechanistic replication. Existing original GBIF source-reported S3−S1 ~−0.0057 across 49 shadow folds is a **weak-proxy exploratory null**, not a negative causal fruit-resource test.
