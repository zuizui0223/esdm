# NeoBat resource-mediated SDM — evidence, qualification gates and next experiment (2026-11-19)

**Branch:** `design/neobat-trophic-sdm-phase1-20261119`. **PR:** #244 (DRAFT); `main` untouched.

**Status: SOURCE AND SPATIAL-INPUT FEASIBILITY ESTABLISHED IN A BOUNDED PILOT; NO 2D/3D TROPHIC SDM EFFECT FITTED.**

## Confirmed source and prefit findings

| Gate | Correct result | Evidence |
|---|---|---|
| Original NeoBat provenance | 2,571 total bat–plant interactions; 1,931 Frugivory, 640 Nectarivory; 200 sites, 169 references; fruit source SiteCode–RefCode conflict 0 | `docs/replication/neobat/source_preflight.json` |
| Main frugivore candidates | 26 bats (of 31 broad frugivory-user candidates); original author source pinned to commit `d25292d19be32a85a21c60384a3f2d818e8081de` | `NEOBAT_PHASE1_SOURCE_PREFLIGHT_20261119.md` |
| GBIF public search name/count screen — bats | 26/26 bat name concepts; 1 independently evidenced *Carollia brevicauda/brevicaudum* alias | `docs/replication/neobat/gbif_search_preflight.json` |
| GBIF public search name/count screen — plants | 255/261 strict accepted species matches; 218/261 have ≥5 indexed georeferenced records in ≥2 countries | `docs/replication/neobat/plant_search_preflight.json` |
| Network data coverage | 709 distinct primary candidate bat × plant links; 691/709 to strict-match plant names, 625/709 to plants passing the two-country indexed count screen | `NEOBAT_LINK_INDEPENDENCE_AUDIT_20261119.md`; plant preflight |
| Study-country-out network input | 7/26 bats retain ≥4 source-country folds with ≥3 partner plant names and ≥2 independent literature references | `NEOBAT_COUNTRY_HELDOUT_NETWORK_INPUT_GATE_20261119.md` |
| Country-heldout **literature link recurrence**, not SDM | 6/12 countries qualified, 338 positive test edges; 46.94% observed vs 40.55% degree-preserving null, +6.39 percentage points, Monte Carlo p=0.001; a separate script matched 8/8 numerical checks | `docs/replication/neobat/crosscountry_reproduction_result.json` and `crosscountry_reproduction_verdict.json` |
| All-page GBIF occurrence SEARCH pilot | **Retired technical failure**: 29 minutes and cancelled before completing first taxon or saving a spatial record. Synthetic geometry tests 6/6 PASS | `.github/workflows/neobat-spatial-cell-pilot.yml` now guarded with `if:false` |
| **Bounded** actual GBIF spatial sample | 14 fixed taxa (4 bats and 10 source-top plants); **55/55** single country pages completed; at least 5 distinct 25-km cells in 4 sampled countries for **4/4 bats** and **7/10 plants**. This is a *first-page lower bound*, NOT full occupancy or a spatially independent test denominator | `docs/replication/neobat/spatial_country_lb.json`; `NEOBAT_SPATIAL_CELL_LOWERBOUND_DESIGN_20261119.md` |
| Known ≤12.5-km reported coordinate uncertainty | 4-country sufficient lower bound for only **1/4 bats** (*Artibeus jamaicensis*) and **2/10 plants** (*Cecropia obtusifolia*, *Piper aduncum*). Even these records' error envelopes may span cell boundaries | same bounded spatial receipt |
| **Bat country + resource-link same-country input** | Of 16 bat × sampled-country pairs, **9/16** have ≥5 sampled bat cells, ≥3 named fruit plants each with ≥5 sampled cells **in that country**, and ≥2 outcountry NeoBat references for the compatible links. All 4 bats have ≥2 potentially admissible country pairs. First source-data calculation reproduced by a separate Python/Actions run | `docs/replication/neobat/country_resource_gate.json`; `country_resource_gate_discovery.json` |
| DOI-bearing bat/plant GBIF occurrence downloads | **NOT DONE**. Request draft for 26 bat numeric taxon keys + 255 exact plant keys exists, but no authenticated dispatch or fixed full occurrence CSVs | `docs/replication/neobat/gbif_bulk_download_request_drafts.json` |
| Full plant SDMs, heldout bat SDMs, M3–M1 and rewired null | **NOT DONE**. No evidence for a trophic-model predictive gain | `NEOBAT_TROPHIC_SDM_PHASE1_DESIGN_20261119.md` |

## Interpretation ceiling

1. **Positive source-internal evidence**: documented bat–plant fruit-use links contain geographically portable partner identity information above a local degree-preserving null, conditional on source sampling biases. Reproduction of the computation is **not independent ecological replication**.
2. **Positive observability feasibility**: bounded indexed GBIF samples contain multiple records in distinct equal-area cells, and nine 4-bat × country combinations have multiple externally documented potential fruit partners with records in the same *country*.
3. **Not demonstrated**: true plant fruit abundance, fruiting season, shared 25-km bat–plant cells, detection-calibrated occupancy, direct feeding behavior, competition, resource causality, M3-vs-M1 heldout improvement, or transfer of 2D patterns to `batter` vertical niche strategies.
4. The 55-country-page sample used default GBIF search ordering, and thus is not random; countries were selected from *earlier count-only metadata*. Cells are minimum observed occupancy **records**, not demonstrated independent biological occupancy.
5. The sampled bat geographic summaries have already been opened for feasibility. They must be considered **discovery information** and cannot later masquerade as never-opened holdout responses.

## Next actual experiment: DOI-backed and independently evaluated M3

- **A. Independent GBIF occurrence source acquisition:** validate legacy numeric GBIF Backbone `TAXON_KEY` namespace, freeze 2000–2025, coordinate and geographic predicates, authenticate with GBIF, submit and capture **download key + DOI** and immutable archive fingerprint. Respect GBIF's active-job capacity limits. Do not use unbounded synchronous SEARCH paging again.
- **B. Input denominators:** accepted taxon crosswalk, 25-/50-km known-coordinate-accuracy cells, deduplicate survey events and dataset sources, fit plant relative suitability on only outcountry training areas, with explicit target-group sampling bias.
- **C. Freeze outer heldout study/country regions before inspecting prediction**, reserve a truly independent bat response, and compare M0 abiotic, M1 generic plant pool, M3 generic pool + documented weighted partner suitability against degree-preserving N1 and matched nonpartner N2.
- **D. Claim limit:** If and only if M3 improves heldout relative presence rank over M1 and source-matched nulls, support **predictive resource-link information**. Do not infer causal consumption, exact fruit resources or 3D niche mechanism from that improvement.

**Repository policy:** `main` must not be changed or this pilot described as a confirmed trophic SDM paper before the DOI-backed independent forecast and observation-bias checks pass.

## GBIF DOI request readiness — credential preflight (2026-11-19)

- Structural request check: **PASS** for the pinned 26 numeric bat taxon keys and 255 strict-match plant taxon keys, year 2000–2025, geospatial predicate, and 29-country list. This is static validation only, **not** GBIF API acceptance; see `docs/replication/neobat/gbif_bulk_request_static_preflight.json`.
- Isolated `esdm` Actions credential-presence check: **AUTH_CONFIG_INCOMPLETE**; all three names `GBIF_USERNAME` (or repository variable), `GBIF_PASSWORD`, and `GBIF_EMAIL` were absent in this repository's evaluated workflow environment. See `docs/replication/neobat/gbif_auth_presence.json`.
- No credential values were printed, transmitted or stored by this check, no authentication attempt was made, and no GBIF request or DOI exists for NeoBat. Other repositories' secrets are not automatically accessible in `esdm`.
- **Next user-only action:** configure the GBIF credentials as GitHub Actions secrets (or the username as a repo variable) for `zuizui0223/esdm`. Do not place credentials in this chat, source files, PR comments or public build logs.
- Resume only after the prerequisite is met; then independently verify the GBIF taxonomy namespace, API request acceptance, user download quota, archive checksum, DOI and data provenance before opening unobserved country bat responses.
