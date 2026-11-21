# NeoBat independent vegetation-plot crosswalk: executable input boundary

Date: 2026-11-21. **No BIEN/sPlot original plot rows have been downloaded or scored in this branch.**

This advances the source-independent vegetation path by pinning the actual 106 species from the existing source-derived v2 reference receipt, with original Git blob SHA and roster SHA256, and creating a deterministic, source-provenance-aware input auditor.

**Correction to earlier informal planning:** the completed shadow has **10 countries with fitted bat source folds** (BR, CR, EC, GF, GT, HN, NI, PA, PE, SV), not 11. All 106 fixed plant names and these 10 actual fitted countries are pinned in `NEOBAT_INDEPENDENT_PLOT_CROSSWALK_INPUT_20261121.json`. The original 84 source bat folds, 51 prequalified, 49 fitted, 2 shadow stops are unchanged. The 10-country scope does not convert a 10-country GBIF shadow into an independent plot replication.

## How to use

First obtain an authorized **independently collected** vegetation-plot table with documented plot source IDs and original primary-dataset IDs. Do not treat BIEN's occurrence aggregation as plot-origin data or assume its records are independent of GBIF. Normalize only source-authenticated plot records to these required CSV columns:

`source_id,source_kind,country,plot_id,taxon,origin_dataset_id`

`source_kind` must equal `independent_vegetation_plot` only after upstream human/source verification; this script cannot verify the claim from a text label. Plot identity is `(origin_dataset_id,plot_id)`, so repeated IDs in distinct source datasets are not falsely joined. The script counts distinct positive plot records and independently named origins by fixed taxon and country. It rejects duplicate plot-taxon records, and explicitly retains missing species as **unobserved/unknown**, never absent. No habitat, fruit, abundance or bat response is modeled.

```bash
python -m scripts.neobat_independent_plot_crosswalk \
  --curated-plot-csv /path/to/authorized_plot_records.csv \
  --out build/neobat/independent_plot_crosswalk_audit.json
python -m pytest -q tests/test_neobat_independent_plot_crosswalk.py
```

Output contains all 10 countries and 106 fixed taxon denominators, explicit missing matches, and countries with >=2 distinct reported source IDs. It deliberately marks `independent_field_source_qualification_verified_by_script=false`. A nonempty audit is **not** evidence of field-source independence, and an empty audit is **not** an ecological absence result. Plot-positive occurrence cannot establish surveyed absence without full species-list completeness and detectability rules.

## Biological test still outstanding

Obtain actual authorized BIEN 4.2 plot-origin records or sPlotOpen with original dataset identifiers, geographic resolution, survey years, taxon concept crosswalk and survey effort; audit all 106×10 candidate cells, including zero recorded matches as unknown. If there are multiple independent survey sources and enough spatial support, preregister plot-level heldout tests comparing climate-only versus externally measured vegetation resource covariates. Plot tree abundance remains a weak proxy for ripe fruit availability, so independent fruiting/seed-rain observations are required for the stronger trophic mechanism claim. No retuning of the completed 49-fold shadow is allowed.

Original 255-plant M3-M1/N1 ecological contrasts remain **unestimated**. No eSDM superiority claim is made.
