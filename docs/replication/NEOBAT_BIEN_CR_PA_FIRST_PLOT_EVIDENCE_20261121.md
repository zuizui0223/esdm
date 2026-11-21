# NeoBat: first two source-backed BIEN vegetation plot pilots (CR and PA)

Date: 2026-11-21. All counts below are from the **completed original BIEN R workflows**, not GBIF occurrence data or synthetic simulations. Fixed roster: 106 species, original shadow-country scope 10; these two countries were accessed in sequence, not selected by their results.

## Strict source scope

`BIEN_plot_country(country, all.metadata=TRUE, natives.only=TRUE, cultivated=FALSE)`, BIEN 4.2.8/build 19535, with exact matching to the frozen 106 plant binomials. These are **native, non-cultivated-source-query results only**; the denominator includes species outside that filter. Missing matches mean **unknown**, not absence. Individual rows are plant records, **not independent study sites** or measured ripe fruit.

| Metric | Costa Rica (CR) | Panama (PA) |
|---|---:|---:|
| BIEN plot-taxon record rows (all taxa) | 21,949 | 8,390 |
| Fixed 106 taxa with exact record match | 17 | 22 |
| Matched-taxon record rows | 557 | 974 |
| Distinct complete datasource+dataset+plot-name keys with any matched taxon | 31 | 35 |
| Complete source+dataset keys with any match | 4 | 3 |
| Source-label values with any match | 2 | 3 |
| Distinct source-ID values with any match | 4 | 3 |
| Matched rows with nonempty sampling protocol | 124 (22.3%) | 28 (2.9%) |
| Matched rows with collection date | 433 (77.7%) | 946 (97.1%) |
| Matched rows with positive plot-area field | 557 (100%) | 974 (100%) |
| Matched rows with positive individual-count field | 124 (22.3%) | 332 (34.1%) |

Across both countries, **15 of the exact-matched taxa are shared**, two are recorded only in CR, seven only in PA; union **24 / 106**, or 22.6% of the fixed roster. Matched records sum to 1,531, but composite labeled plots only to **66 country-scoped keys**. These 66 are identity keys, **not 66 geographically verified independent survey sites**. The large counts per few plots indicate that treating individual/stem records as independent sampling units would be pseudoreplication.

Among 15 shared taxa, **10** occur in at least two labeled plots in *each* country and **five** in at least five labeled plots in *each* country: `Calophyllum brasiliense`, `Cecropia insignis`, `Cecropia obtusifolia`, `Socratea exorrhiza`, `Turpinia occidentalis`. None reaches ten labeled plots in both countries. Top two matched taxa account for **61.94% of CR** and **65.30% of PA** matching record rows. These are source sampling concentrations, not biological abundance or fruit availability evidence.

## Immutable provenance

- CR workflow run [44890842765](https://github.com/zuizui0223/esdm/actions/runs/44890842765), head `02cd647eb5d68909ecf045539d309d04a0438ac1`, artifact ID `14702716371`, ZIP SHA-256 `12281ac7cbf88e8cdebdb6adf01f8fff29c267da7b457c9a0d9c66bec046c5b4`.
- PA workflow run [44891025645](https://github.com/zuizui0223/esdm/actions/runs/44891025645), head `7d081e43148223ccee4dc3759e5b7a0fbb94e15c`, artifact ID `14701624924`, ZIP SHA-256 `4e2bc126ec10575763345ce1761089dd0e5b89971a85f6c4f29734a8a9dacdf7`.
- Per-species positive record, source, dataset and labeled-plot counts: `docs/replication/neobat/bien_cr_hierarchical_plot_result_20261121.json` and `docs/replication/neobat/bien_pa_hierarchical_plot_result_20261121.json` (the first is on the CR pilot branch until PR #274 is merged). The original zipped receipts include all returned metadata **column names but no raw coordinates**.

## Evidence boundaries and next discriminating test

**The existing 'independent vegetation' label is a candidate, not a validated fact.** BIEN includes source-aggregated plot surveys: original `datasource` and `dataset` may overlap the GBIF archive used in the bat model. *Source disjointness and spatial independence have not been established*. The different availability of survey protocol, dates, stem count and plot area in CR and PA prevents a defensible pooled biomass model yet. A positive `individual_count` is not edible fruit production, even when area is present.

Next high-value work is identifying primary dataset creators/DOIs, checking overlap with the frozen plant GBIF datasetKey list and verifying comparable area/protocol before expanding models. Do not fit M3 or claim improved bat prediction based on the 24 taxa. No bat holdout outcomes were inspected.
