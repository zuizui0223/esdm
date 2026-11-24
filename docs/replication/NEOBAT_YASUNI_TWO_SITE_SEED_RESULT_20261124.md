# NeoBat × Amazonian seed-fall original field series: Yasuní second-site result

Date: 2026-11-24 (Asia/Tokyo). **Original biological source opened and analysed, not a simulated or GBIF/BIEN proxy result.** Pre-outcome frozen plan: [Yasuní prospective site scope](NEOBAT_YASUNI_SEED_PORTFOLIO_FROZEN_20261124.md) at commit `a4e90d778a7ef086af8675c8a4d16bb2b7a0eb84`.

## 1. Original field data opened

The author's original Yasuní (Ecuador) processed long-format seed-fall table from **Pak et al. 2023, Ecology, DOI [10.1002/ecy.4022](https://doi.org/10.1002/ecy.4022)**, `pakdamie/TreePhenEcology` commit `521b118b75af4d1bb2b7feadb28b077a09301eab`, passed full Git blob verification (`YASUNI_ALL_FINAL.csv` `11cafba9ae138605fdd79cea7a31bc4821d869ee`, original 14,572,057 bytes). Original author code-to-current-binomial bridge `YAS_FAMILY_CODE.csv` also passed Git blob verification (`d9e017afc326059d5feb8f89e4a17bd079f52301`). No raw data are committed.

- **298,282 original rows = 1,054 taxon codes × 283 numeric fractional-year sampling points**, source coverage from `Day_Year_Y` 0.16153–17.14990 (~2000–2017, not reconstructed precise calendar dates).
- Ten exact plant names from the fixed 106 appear in the **final** time series, matching all ten pre-outcome code-bridge candidates: `Cecropia ficifolia`, `C. membranacea`, `C. sciadophylla`, `Celtis iguanaea`, `Licania arborea`, `Socratea exorrhiza`, `Spondias mombin`, `Turpinia occidentalis`, `Vismia baccifera`, `V. macrophylla`.
- Their **2,830 source plant×time values** have 1,909 recorded zeros (67.46%) and 921 positive values; no source-coded missing or omitted plant×time entries. Zeros are **trap seed-fall observations**, not negative bat diets or proof of unavailable fruit.
- The original source cleaning removed Moraceae, Solanaceae, and other selected groups before writing the public final Yasuní table. **Unavailable Ficus and Solanum source columns are not ecological absences.** The full fixed 106 remain in scope as unobserved where not present.

Original NeoBat source interaction author CSV checks pass against `723198f850aa4ee7346122e71a3dd3eadaca176a65bfb87dc2a90f55f2acf10b`; all original **26 primary frugivorous candidate bat labels** retained, of which **6 have >=3 matched original fruit-linked plants and >=60 jointly observed timepoints** (all 283). Six eligible portfolios use six different plant sets; the other **20** candidate labels remain null, not converted to zero resources.

## 2. Result from the frozen fixed comparison

For each candidate source-linked plant set, the per-plant `log1p(seed_count)` series was standardized by its mean, averaged equally per timepoint and summarized with sample CV. The frozen source-free `499` independent species circular shifts (seed 20261124) give a median null CV; reported ratio is observed CV / median shift CV. The reference destroys shared seasonal timing, so it is a **descriptive synchrony lens, not a climate-controlled causal hypothesis test**.

| Source candidate bat | Candidate plant species | Observed / shift-null CV | Descriptive direction |
|---|---:|---:|---|
| `Carollia perspicillata` | 7 | 1.0228 | More synchronous |
| `Artibeus lituratus` | 5 | 1.0478 | More synchronous |
| `Artibeus jamaicensis` | 3 | 1.1652 | More synchronous |
| `Artibeus planirostris` | 5 | 0.9858 | Marginally more compensatory |
| `Carollia brevicauda` | 4 | 0.9975 | Essentially equal, slightly below |
| `Rhinophylla pumilio` | 3 | 1.0421 | More synchronous |

**4 of 6 ratios exceed 1; 2 of 6 are below 1.** No significance threshold is applied. Original paper already reports community-level synchrony and some family-scale compensation; this observed pattern alone does not establish a new ecological mechanism.

The **exhaustive same-size comparison was frozen before seeing Yasuní values**, unlike the earlier post-hoc CC1 control. The matched ten-plant author-derived universe produces all `C(10,k)` sets at the eligible sizes: k=3:120, k=4:210, k=5:252, k=7:120. All combinations were evaluable with the original same CV formula. Here the *observed* CV of five of the six candidate partner sets is lower than the same-size median; one (C. perspicillata, ratio 1.00043) is slightly above. The inclusive fractional CV ranks range from **0.250 to 0.508**—none is an extreme low-variability set. These fractions are not p-values. The apparent directional stability does not support generalized bat-specific resource buffering, and site-specific diet links were not observed.

## 3. What the two original field sites do and do not replicate

| Observation | Cocha Cashu, Peru | Yasuní, Ecuador |
|---|---:|---:|
| Original seed-fall sampling dates/timepoints | 196 | 283 |
| Seed-fall species columns/codes | 654 | 1,054 |
| Exact frozen 106 species in observed file | 11 | 10 |
| Recorded zeros in matched plant×time values | 1,832/2,156 (84.97%) | 1,909/2,830 (67.46%) |
| Candidate source bat labels with >=3 plants | 11/26 | 6/26 |
| Distinct source-linked plant sets among those | 8 | 6 |
| Shift-null ratio >1 (by candidate labels) | 10/11 | 4/6 |
| Observed CV < same-size median (by labels) | 5/11 | 5/6 |

Exactly **three plants** are source-matched in *both* sites: `Celtis iguanaea`, `Spondias mombin`, `Turpinia occidentalis`. Four original bat candidate labels have eligible portfolios at *both* sites: `Carollia perspicillata`, `Artibeus lituratus`, `Artibeus jamaicensis`, and `Artibeus planirostris`. **None of the four has the identical plant partner set at the two sites.** Thus this cannot be presented as four replications of the same bat diet, as proof of locally realized foraging, or as a cross-site estimate of an individual bat species' food security.

Both sites derive from the **same Pak et al. publication**, processing decisions, and the same separate NeoBat interaction network. They are separate field locations but **not two independent source papers or bat sampling programmes**. Sampling periods and the original family censoring differ. If the ecological question is whether flexible diets buffer fruit-resource shortages, require locally confirmed bat–plant links, directly measured edible fruit/fruiting rates, effort-calibrated bat outcomes and source-disjoint geographic holdouts. Nothing here estimates ecological SDM M3−M1/N1 or its superiority.

### Preserved evidence and reproduction
- [Yasuní original field result](neobat/yasuni_seed_portfolio_original_result_20261124.json) from immutable author CSV, author bridge and original NeoBat source checks.
- [Post-hoc descriptive two-site reconciliation](neobat/cc1_yasuni_26bat_descriptive_crosssite_20261124.json) retains the full 26 source candidate names, all null/ineligible cases, and exact shared plant identities.
- [Original Yasuní analyzer](../../scripts/neobat_yasuni_seed_portfolio.py) and [offline tests](../../tests/test_neobat_yasuni_seed_portfolio.py).
- Initial official original run hit a Latin-1 annotation in an otherwise source-correct CSV; subsequent code adopted a lossless Latin-1 fallback *after* UTF-8, with source Git blobs still required to match. An intermediate author-data run completed biologically, but failed only to push a stale branch after a concurrent test commit. The later latest-head run successfully computed and committed the final source result.
- No raw trap records, precise coordinates or bat outcomes uploaded.
