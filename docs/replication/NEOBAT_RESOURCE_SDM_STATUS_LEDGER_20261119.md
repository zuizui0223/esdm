# NeoBat resource-mediated 2D SDM — current evidence & gate ledger (2026-11-19)

Branch: `design/neobat-trophic-sdm-phase1-20261119` (isolated from main).
This is a **prefit study**. No comparison of resource-dependent vs.
non-resource bat distribution has been completed.

| Gate | Result | Evidence |
|---|---|---|
| Author original NeoBat CSV and key integrity | PASS: 2571 total interactions, 1931 fruit-use, zero fruit SiteCode/RefCode mismatches | `docs/replication/NEOBAT_PHASE1_SOURCE_PREFLIGHT_20261119.md` |
| Primary guild and source-network cohort | PASS: 26 Frugivore candidate bats of 31 broadly fruit-consuming bat taxa | `docs/replication/neobat/source_preflight.json` |
| Bat GBIF name and country-count metadata | PASS: 26/26 after 1 independently documented Carollia name alias; **not a DOI download** | `docs/replication/neobat/gbif_search_preflight.json`; `docs/replication/NEOBAT_CAROLLIA_NAME_CROSSWALK_20261119.md` |
| Plant GBIF public search count metadata | PASS: 255/261 exact species-name matches; 218 have >=5 georeferenced indexed records in each of 2+ countries | `docs/replication/neobat/plant_search_preflight.json` |
| Source fruit links after plant metadata gate | 691/709 linked to exactly matched plant names; 625/709 (88.2%) linked to plant with >=5 coordinate records in 2+ countries | same plant receipt |
| Source network link geography diagnostic | Exploratory six qualifying countries, 338 observed positive link edges; country-equal recurrence 46.94% vs degree-preserving null 40.55%, excess +6.39 pp, Monte Carlo p=0.001 | `docs/replication/neobat/crosscountry_reproduction_result.json`, verdict PASS 8/8 |
| Source-country-withheld network-input gate | 7/26 have >=4 source-country folds with >=3 screened partners / >=2 independent refs left | `docs/replication/NEOBAT_COUNTRY_HELDOUT_NETWORK_INPUT_GATE_20261119.md` |
| Actual 25/50-km GBIF grid cells, 4 bats + 10 source-top plants | RUN REQUESTED via `.github/workflows/neobat-spatial-cell-pilot.yml`; **not yet certified** in this ledger | `docs/replication/NEOBAT_SPATIAL_CELL_PILOT_DESIGN_20261119.md` |
| Authenticated full GBIF DOI-bearing bat/plant downloads | **NOT DONE**; request templates built but taxonomy checklist namespace and authentication must be validated | `docs/replication/neobat/gbif_bulk_download_request_drafts.json` |
| Spatial buffer and independent test folds | NOT DONE | phase1 design |
| Plant cross-fitted relative suitability, GBIF taxon/effort source bias | NOT DONE | phase1 design |
| M0-M3/N1-N2 region-heldout bat prediction | NOT DONE | phase1 design |
| 3D resource×individual movement or foraging mechanism | NOT DONE; nonmatching telemetry taxa excluded from direct fit | `docs/replication/NEOBAT_BATTER_3D_BRIDGE_SCOPE_20261119.md` |

## Scientific claim boundary

The original NeoBat literature preserves some bat-plant *link identity*
across country subsets beyond the local network-degree null. The published
fruit-link data are unevenly sampled, source-internal, and partly based
on old observations. The link diagnostic cannot establish current
consumption or causal effects on bats. GBIF source counts are **not**
independent 25-km occupied cells, and cannot be turned into calibrated
occurrence probabilities or environmental effect coefficients.

Proposed eventual test: M3 observed-link resource-alignment + generic
plant pool vs M1 generic plant pool only, evaluated on **unopened
country/region buffered bat occurrences** with plants cross-fitted on
the same outer folds and matched source-independent null rewires.

## Next action without outcome-dependent threshold changes

1. Read the exact authored `docs/replication/neobat/spatial_cell_pilot.json`
   when/if produced and inspect status before claiming spatial feasibility.
2. If 14-taxon pilot meets predeclared source and known-accuracy gates,
   expand to all eligible 26 bats / 255 exact-match plants by authenticated
   DOI-bearing download; do **not** equate current public search with a DOI.
3. Keep 6 ambiguous plant names out of main analysis until separately
   evidenced accepted-name crosswalks; report the lost-link denominator.
4. Freeze source/effort/spatial folds and model selection on discovery
   only, then conduct M3-vs-M1 and degree-rewire challenge in independent
   heldout geography. Valid final outcome may be null or inconclusive.

Do not merge to main as a positive trophic SDM paper result.
