# NeoBat BIEN plot expansion — prospective source-only scope (2026-11-21)

This is **not** a new fitted SDM. The original 106-species roster and the ten *already fitted* weak-shadow countries are frozen in `NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json`:

`BR, CR, EC, GF, GT, HN, NI, PA, PE, SV`.

Do **not** add or remove a country based on the match count, and do not call these ten independent ecological replications. Original shadow: 49 fitted source folds in 10 countries, not the original ecological M3 model.

Country-specific BIEN plot access uses `BIEN_plot_country(country=..., all.metadata=TRUE, natives.only=TRUE, cultivated=FALSE)` for the primary *native, non-cultivated* scope. **CR** queried first (21,949 record rows, 17 exact taxa, 31 provisional dataset+plot label pairs, four dataset labels), then **PA** queried next before its BIEN data were seen, because PA has seven frozen shadow bat folds. All ten countries and all 106 fixed taxa remain in the denominator for any descriptive coverage table. CR and PA alone cannot establish regional transferability. Introduced/cultivated fruits are **excluded from this native-only descriptive source check**; their food-resource role requires an explicitly separate sensitivity analysis.

For each authorized source, keep a receipt of BIEN release, query flags, record count, exact taxon count, matched-taxon record counts, composite `datasource + dataset + plot_name` group counts, missing plot metadata and protocol/area/abundance support; retain failures and zero-match results. Do not publish raw coordinates or claim that a zero match establishes biological absence. Dataset names, datasource IDs and plot keys require independent provenance and overlap checks against the original GBIF plant source DOI before any cross-source model comparison.

Plot/stem counts are not ripe fruit availability, and plant-country observation coverage does not validate M3−M1 or M3−N1. Any future independently sampled plant-resource model must use a frozen climate/observation baseline and source-disjoint geographic evaluation, with all attempted folds reported, including failed or negative ones.
