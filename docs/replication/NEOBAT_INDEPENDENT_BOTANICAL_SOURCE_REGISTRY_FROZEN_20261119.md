# NeoBat next source frontier: independent plot abundance and seed/fruit proxies (response-blind)

Frozen date: 2026-11-19. Scope: **external-source metadata and access feasibility only**, after completed *weak shadow* source-geography non-support (49/51 fitted; signed source AUC S3−S1 −0.00569; S3−SN1 −0.00800). This document registers *potential sources* before reading their biological species records. It does not revise the previous 84- or 51-fold source response or create new M1/M3 effect claims.

## Why the original source is exhausted

Our plant predictors in the completed shadow program were WorldClim-only logistic models of GBIF source-recorded plant cells, not measured fruit density; bat target-group pseudo-background was also GBIF-sourced and not true absence. There is no independent vegetation biomass, fruiting/flowering, survey effort or direct bat diet response in the original 49 fits. The single nominal bat×country SN1 p=0.04 among 49 is not independently replicated. Further retrospective tuning on those same results cannot produce a valid confirmatory ecological claim.

## Source registry, from publisher/curator descriptions

| Candidate | Public identifier / URL | Independent information | Immediate access and spatial ceiling |
|---|---|---|---|
| **sPlotOpen**, Sabatini et al. 2021 | `https://doi.org/10.25829/idiv.3474-40-3292`; curator `https://www.idiv.de/research/projects/splot/splotopen-splot/` | Open global vegetation plot metadata and abundance/cover: 95,104 plots from 105 sources, 114 countries, plot size/date, species composition | **Top regional validation candidate.** Original ZIP download via `https://idata.idiv.de/ddm/Data/DownloadZip/3474?version=5047` is *not yet byte validated*; no 106-partner overlap, 11-country counts, coordinate uncertainty, origin/GBIF independence verified. Sampling spatial bias and uncertain local representative coverage must be audited. |
| **BIEN 4.2 vegetation-plots component**, Enquist et al. 2026 | `https://bien.nceas.ucsb.edu/bien/biendata/`; `BIEN_plot_list_datasource()`, `BIEN_plot_metadata()` via BIEN R package | Curator counts 363,258 surveyed plots, 17,247,823 plot-origin records, including structured abundance/within-plot nondetection | **Top regional candidate, access/API/source firewall pending.** BIEN also aggregates GBIF records; only true plot-origin primary datasets excluding duplicates of the two frozen GBIF DOIs can be used as external evidence. Do **not** treat all BIEN occurrence data as independent. |
| **BCI 58ha canopy tree survey**, Wright 2026 updated Aug 31 | `https://doi.org/10.5061/dryad.1g1jwsvc3` | Six plots, three large canopy-tree censuses (2004/05, 2014, 2025), 15,562 trees, 222 species, species-key file and plot coordinates | Dryad page publicly lists downloadable files; bytes/taxon overlap not yet inspected. **One Panama locality only**; canopy density is not weekly fruit supply; cannot validate across 11 countries. |
| **BCI seed rain traps**, Wright & Calderón 2016 | `https://repository.si.edu/items/a4d5a31a-193a-482e-8b1a-9e2b0d71108a` | 18 tree species, 2008–2012 repeated seed-trap counts at ~250 traps with weekly censuses | Closest independent local **resource seasonality** indicator, but seed rain is not available ripe fruit or bat consumption. File `seedataSave.csv` listed publicly, exact source access/taxon match not verified. Only one locality. |
| BCI 50ha multi-census stand abundance, Condit et al. 2019 | `https://doi.org/10.15146/5xcp-0d46` | Eight censuses of mapped trees over 1982–2015, independent plot abundance | Large 286MB archive; BCI one locality only; respect terms and redistribution restrictions. |
| ForestGEO other sites | `https://forestgeo.si.edu/explore-data` | Additional structured permanent tree plots | 30 of 78 site datasets in portal, many require application; cross-country/taxon/time coverage not yet qualified. |
| 2026 Zenodo BCI 84-species seed-trap series | `https://doi.org/10.5281/zenodo.20814484` | Weekly BCI seed counts for 84 species, metadata publicly visible | **Files restricted** at time checked. Do not attempt unauthorized retrieval or infer taxon overlap. |

## Hard separation of research outputs

### Stage A — country and species metadata-only feasibility (next executable)

1. Use source publisher metadata and HTTP HEAD (no biological records) to check authorized access and archive schemas. Preserve `HTTP_403`, `HEAD_405`, inaccessible portal, or authentication needed as distinct *source gates*, not ecology negatives.
2. For a future cross-country independent test, use only identifiable *source-level independent* vegetation survey datasets with coordinate/plot area quality, dates and mutually independent field collection protocols, not GBIF copies. A plant×country/25km prediction cell cannot be labeled surveyed absent unless the original plot actually supports detecting that plant.
3. Predefine taxonomic crosswalk to **all fixed 106 species**, source investigation denominators for **all 11 shadow-eligible countries**; do not select on the observed S3 effect. Explicitly report how many 106 species and 11 countries lack even one independent quantitative plot. Require at least two independent primary vegetation sources across two countries before trying a geographic generalization claim; **one BCI forest is only a local validation opportunity**.
4. Forest-tree counts are potential abundance **proxies**, but a frugivore's food varies with plant growth form, ripeness, season and diet; never equate tree abundance, tree cover, or seed rain directly to fruit available for bat feeding. Only source-designated fruiting / seed-rain repeated observations can support phenology, and even then with conversion assumptions.

### Stage B — future independent external test (NOT authorized to infer today)

A truly source-independent validation would compare heldout, calibrated plant-resource predictions to **plot survey presence/abundance** at *unopened* plot sites, then explicitly test bat source geography with independent observed bat effort or behavior. Avoid evaluating the same GBIF bat observations again as a fresh source-independent confirmation; existing 255-plant ecological M3−M1/N1 remain null/unestimated.

No initial original row data, plot coordinates or downloadable archives were read at source-registry creation. This is a source qualification/provenance ledger, not a reported discovery. Do not merge to `main` as a biological finding.
