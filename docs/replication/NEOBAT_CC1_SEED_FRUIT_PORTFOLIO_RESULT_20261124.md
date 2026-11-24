# NeoBat–Cocha Cashu: first original field-observed seed-rain partner portfolio diagnostic

**Source-backed result, 2026-11-24; exploratory pilot only.** This does not estimate a bat distribution model, a field-verified bat diet or available ripe fruit.

## What actually opened

The independent original-author field file `CC1_ALL_FINAL.csv` from `pakdamie/TreePhenEcology`, frozen commit `521b118b75af4d1bb2b7feadb28b077a09301eab`, Git blob SHA `dc95badb04365449e9ad5a13e8a37c5a9fc552e9`, contains a Cocha Cashu, Peru, seed-rain time series used by Pak et al. 2023 (*Ecology*, DOI [10.1002/ecy.4022](https://doi.org/10.1002/ecy.4022)). Original NeoBat interactions from `gflorezm/NeoBat_Interactions` are SHA256 verified against the pre-frozen original `723198f850aa4ee7346122e71a3dd3eadaca176a65bfb87dc2a90f55f2acf10b`. This is a separately collected **botanical** field dataset; the NeoBat source diet links were documented in other localities, not confirmed in the Cocha Cashu community.

The one-site field series has **196 sampling events (2002-09-09 to 2011-01-21)** and **654 plant species columns**. Exactly **11 of the frozen original 106 plant names** match column binomials without fuzzy synonyms. Their 11×196 = **2,156 numeric cells** contain 1,832 **observed zeros** (84.97%), 324 positive counts, and no missing cells. The other 95 original plants are **not represented in the exact-name match**, not declared biologically absent. Reported seeds/trap counts are not comparable biomass of ripe fruits or proof of bats' feeding opportunities.

Original source-derived 26 candidate frugivorous bat names remain in the complete denominator. **11 labels** have at least 3 exactly matched source-linked plants and 60 jointly observed sampling events, all with 196 dates; **15 labels remain ineligible**. These 11 labels correspond to only **eight distinct plant sets**: three labels `Artibeus phaeotis`, `Chiroderma villosum`, `Platyrrhinus helleri` have the same three plants (`Ficus citrifolia`, `F. insipida`, `F. pertusa`); `Uroderma convexum` and `Vampyriscus nymphaea` have an identical four-plant set. The 11 labels therefore do *not* provide 11 independent biological repetitions.

## Primary fixed calculation: temporal alignment

The [original freeze](NEOBAT_CC1_SEED_PORTFOLIO_FROZEN_20261124.md) preceded opening numeric values. For each source-linked candidate plant set, per-species `log1p(seed_count)` time series were scaled by their means over all jointly observed sample dates, then averaged equally by date. Temporal CV was compared with the median CV from 499 fixed-seed independent circular shifts of the species series. This measures relative synchrony of the *candidate annual/fortnightly seed-fall curves*, not a likelihood or inference about a bat population.

**10 of 11 candidate labels have observed-CV / shift-null-median-CV > 1**, from 1.0173 to 1.1450. **One** (`Carollia castanea`) is slightly below 1, ratio **0.9889**. On the **eight distinct plant sets**, seven exceed 1 and one is below. The shifts break shared timing of seasonal environmental conditions; *more synchrony than a freely shifted median does not identify a special bat-specific synchrony mechanism*. A ratio near 1 is not strong compensation.

## Secondary explicitly post-hoc exhaustive same-size plant-set counterfactual

This comparison was documented **after the original portfolio outcomes were observed**, at [the post-hoc control scope](NEOBAT_CC1_SIZE_MATCHED_CONTROL_POSTHOC_20261124.md), and does **not** create a new confirmatory test. The complete eleven-plant CC1 matched source pool yields `C(11,k)` possible k-plant sets, all enumerated exactly (no Monte Carlo subsampling): k=3: 165; k=4: 330; k=5: 462; k=6: 462; k=9: 55.

The same original *observed* CV is compared against the CV distribution of all source-matched sets with the identical number k of species. A smaller percentile means a relatively more stable seed-fall portfolio; this is an inclusive descriptive rank, **not a statistical p-value**.

| Candidate label (source-linked plant count) | CV / equal-size median | Inclusive lower-CV rank fraction | Descriptive direction |
|---|---:|---:|---|
| `Carollia perspicillata` (5) | 0.925 | 0.381 | Relatively stable |
| `Artibeus lituratus` (6) | 0.871 | 0.275 | Relatively stable |
| `Artibeus jamaicensis` (9) | 1.000 | 0.509 | Median |
| `Artibeus planirostris` (4) | 0.793 | 0.203 | Relatively stable |
| `Artibeus phaeotis` (3) | 1.212 | 0.655 | Relatively variable; shares identical plant set with two other candidate labels |
| `Carollia castanea` (3) | 0.864 | 0.242 | Relatively stable |
| `Chiroderma villosum` (3) | 1.212 | 0.655 | Same 3 plants as `A. phaeotis` |
| `Platyrrhinus helleri` (3) | 1.212 | 0.655 | Same 3 plants as `A. phaeotis` |
| `Uroderma convexum` (4) | 1.027 | 0.524 | Relatively variable; shares identical set with `V. nymphaea` |
| `Vampyriscus nymphaea` (4) | 1.027 | 0.524 | Same 4 plants as `U. convexum` |
| `Artibeus watsoni` (4) | 0.968 | 0.455 | Relatively stable |

By **labels**, 5 are below, 5 above, and 1 equal to their size-matched median. Counting **eight unique plant sets**, 5 below, 2 above and 1 equal. The most relatively stable linked set still ranks at fraction **0.203**, not an unusually extreme tail within the limited eleven-plant observed pool. No source-specific **fruit-portfolio buffering advantage** is established.

## What is new, and the inferential boundary

This is the first executed original, independently collected *seed-fall* temporal series linked to the unchanged NeoBat bat–plant source catalog in this branch. It shows **real temporal source-data variation, abundant observed zeros, limited exact taxon overlap, and shared plant sets across putative bat portfolios**. The corresponding field-data negative control does not show a consistent source-link-specific buffering advantage. This is an **exploratory single-site descriptive result, not a negative proof of dietary compensation**. Source diets come from multiple places and are *not confirmed actual diets at Cocha Cashu*; 26 candidate bat labels are *not sampled bat populations*. Annual/discrete seed-trap entries are not direct bat food biomass or ripe fruit crop. The shift null does not control shared seasonality; neither the original CV ratio nor the exact same-size rank is a confirmatory p-value. Original ecological M3−M1/N1, bat predictor accuracy and eSDM superiority all remain unestimated.

**Separate BCI attempt:** the 201-species published Dryad seed output file `10.5061/dryad.4mw6m909j` could not be opened (HTTP **401** in original retrieval [Actions run 45380660654](https://github.com/zuizui0223/esdm/actions/runs/45380660654)); **no BCI measurements were inferred or substituted**. The CC1 result uses a different genuine author-hosted data source.

## Verifiability

Source-first one-shot GitHub Actions and the original Python implementation reproduce the original seed-trap time series and 26 candidate statuses, then the independent same-size post-hoc control. Only public aggregate receipts are committed:
- [Original CC1 seed portfolio result](neobat/cc1_original_seed_portfolio_result_20261124.json)
- [Exact same-size counterfactual result](neobat/cc1_size_matched_control_result_20261124.json)
- [Original computation](../../scripts/neobat_cc1_seed_portfolio.py)
- [Exhaustive size-matched analysis](../../scripts/neobat_cc1_size_matched_control.py)

The code verifies immutable original source Git blob IDs and the original NeoBat source SHA256 before opening outcomes. Raw trap rows, fine-scale locations or individual animal observations are not archived. The original first study is explicitly kept distinct from the **post-hoc** size-matched control.
