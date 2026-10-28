# E7-C empirical result — strict same-camera-year diel comparisons reveal a severe overlap limit

**Completed 2026-10-28.** A separate, explicitly **post-result exploratory** source opening of the original 11 Snapshot Serengeti COCO metadata ZIPs was performed once in [GitHub Actions run 40618416135](https://github.com/zuizui0223/esdm/actions/runs/40618416135). It is **not** a repeat of the original E7 pooled-MH endpoint, not a new biological source, and not a confirmatory ecological replication. The frozen [E7-C design](E7_DIRECT_CAMERA_YEAR_DIEL_DESIGN.md) and the original 11-file SHA256/season-specific QC checks were applied without changing thresholds.

## Why this comparison matters

The earlier pooled E7 analysis produced estimates for **54/66** species pairs in discovery and **50/66** in validation, while a synthetic counterexample proved pair-specific Mantel–Haenszel aggregation can create apparent nontransitive three-species log-odds even if **no species' diel profile changes at any individual camera**.

E7-C instead uses the same camera location and hydrological year, with **all four wet-night, wet-midday, dry-night and dry-midday sequence counts positive for each species**. It first calculates each species' *local* dry/wet change in its observed night/midday ratio, then subtracts those local changes for a species pair, before any camera-year aggregation. This removes the **specific pair-dependent MH weighting problem**, not species-specific observation bias.

## Complete endpoint: stricter support makes most pairs unestimable

| Fixed species-pair universe (12 taxa; 66 unordered pairs) | Discovery S01–S05 | Validation S06–S11 |
|---|---:|---:|
| Original E7 pooled MH **estimable** | 54 | 50 |
| New E7-C strictly matched direct-cell **estimable** | **1** | **9** |
| Direct-cell pairs whose median sign withstands all site deletions | **1** | **3** |
| Camera-year cells with ≥1 species meeting its four-bin requirement | 125 | 202 |
| Complete three-species camera-year cells | 24 | 39 |
| Within-cell three-species algebraic closure tests | 85 | 137 |
| Maximum numerical closure error | 8.9×10⁻¹⁶ | 8.9×10⁻¹⁶ |

### How severe is the overlap limitation?

Among the **66** original unordered species pairs, **30** discovery pairs and **27** validation pairs had **zero** camera-year blocks where both species satisfied the four strictly positive wet/dry × night/midday record counts. The median number of matched camera-years per pair was **1** in **both** partitions.

| Count of exact shared complete camera-years per pair | Discovery S01–S05 | Validation S06–S11 |
|---|---:|---:|
| 0 | **30** | **27** |
| 1–4 | 23 | 20 |
| 5–9 | 12 | 10 |
| ≥10 | **1** | **9** |
| **Total fixed pairs** | **66** | **66** |

This stricter four-bin-positive filter especially excludes rare or strongly diel-specialized taxa; it does not mean an animal was absent from the landscape. Requiring more camera seasons or better reference detection is the next **sampling design** issue; post-hoc zero imputation or relaxing thresholds would not make the old E7-C endpoint independently valid.

**This is a support/estimand difference, not proof that the old E7 MH calculation was arithmetically wrong.** It does establish that the existing records cannot support the same community-wide comparisons under strict four-bin overlap without changing the method. There is no authorization to relax the preregistered gate or insert continuity pseudocounts after inspecting this outcome.

### The only pair directly comparable in both collection-period partitions

| Relative diel shift of **wildebeest versus zebra** | Discovery | Validation |
|---|---:|---:|
| Eligible exact camera-years | **19** | **46** |
| Distinct contributing physical cameras | **18** | **40** |
| Equal-camera-year median local dry/wet log-ratio change | **+1.39491** | **−0.07288** |
| Fraction of eligible camera-years with positive change | 13/19 (**68.4%**) | 22/46 (**47.8%**) |
| Leave-one-camera-out median range | **+1.04144 to +1.81406** | **−0.16022 to +0.00303** |
| Sign stable under all site deletions? | **Yes** | **No** |

The discovered relative recorded-diel change is positive, and survives every camera exclusion **within discovery**; that direction does **not** transport to validation, where the median is close to zero and not deletion-robust. The direct comparison used **identical taxon labels and time-bin criteria**, but *different* camera-year subsets in each original collection-period partition. This is not a longitudinal replication of one population.

The other **8** validation-only estimable pairs, with median local log-change and camera-deletion sign stability, are retained in the [result receipt](E7_DIRECT_CAMERA_YEAR_FROZEN_RESULT_RECEIPT.json), with **all 66 original pairs including unsupported cases** in the immutable [full Actions result artifact](https://github.com/zuizui0223/esdm/actions/runs/40618416135/artifacts/12785339858). Among them, three validation medians were sign-stable to single camera deletion (elephant/zebra, Thomson's gazelle/zebra, giraffe/zebra); **none** had sufficient data to compare both periods except wildebeest/zebra.

### Tautological local closure is a quality check, not an ecological result

With all species in the *same* camera/year cell, if species-specific changes are `d_i, d_j, d_k`, the pair differences must obey

`(d_i − d_j) + (d_j − d_k) − (d_i − d_k) = 0`.

The **85 + 137** computed triangle identities closed to within **8.9×10⁻¹⁶**. This confirms the arithmetic uses common within-cell support and eliminates the earlier particular MH triangle artifact. It **cannot** demonstrate no interspecific ecological interaction or the presence of one. Interactions could be present even if closure is exactly zero.

## What the observed support actually teaches us

The E7 original fixed roster includes strongly day-active and night-active mammals, many sparse across camera-year × season × time cells. The strict data eligibility gate excludes any individual taxon with even one empty recorded time bin in a camera/year. In discovery, **zebra had 62** camera-years with complete four-bin support, **wildebeest 32**, **lion 6**, **spotted hyena 4**, **warthog 1**, and **reedbuck 0**. Thus the paucity of direct matched multi-species contrasts is not an interpretation of biological absence; it is **a documented inability to measure seasonal per-species relative diel changes without zero-cell modeling and additional observation calibration**.

The newer endpoint is much stricter than E7's MH method and reports **support loss**, not a direct sensitivity estimate of the size of an E7 MH effect under exactly the same rows. Claim that the prior E7 pattern was *caused* by MH pooling is **not justified**. What is justified is that **most pooled pair estimates cannot presently be corroborated using fully observed same-camera-year four-bin contrasts**.

## Stronger ecological direction without adding model-generation loops

To test seasonal reshaping of **true** community temporal niches, the valuable next data collection should include cross-season **known-passage reference, taxon-specific effective camera detection, night/midday effort windows and near-continuous operation per camera**, alongside a measured precipitation/vegetation/resource series. The current aggregate cannot identify whether temporal record changes reflect shifts in actual animal passage, migration, vegetation-induced detection or selective zero-cell exclusion. A future count model that allows empty cells could be defensible only with an independently fixed observation model and independent outcome validation; **do not use it to rescue the already-opened E7-C endpoint**.

## Reproducibility and unchanged historical boundaries

- [Frozen separate E7-C design](E7_DIRECT_CAMERA_YEAR_DIEL_DESIGN.md) and [original-source SHA/CQ integrity receipt](E7_DIRECT_CAMERA_YEAR_FROZEN_RESULT_RECEIPT.json).
- [Single new descriptive run 40618416135](https://github.com/zuizui0223/esdm/actions/runs/40618416135): 5 synthetic tests PASS, all **11/11 source ZIP SHA256 and original E7 per-season QC matched**, no model fit; output artifact ID **12785339858**, ZIP SHA256 `65c09a20f9368f638c1d56ae8306650de3af6ebeedf2e443c728e76bf84f869f`, inner JSON SHA256 `a032635e1acfabd89c253fe52308469735c4e13776ae3f49b7294cded9e7b6cf`.
- Reproducible [direct-cell script](../../scripts/e7_direct_camera_year_diel.py) and synthetic tests.
- Original E4 fitted activity/state scores, original E5 **0/17 qualified / G4 unpassed**, E7 11-season primary results, and original graph decomposition were not revised. No new ecological p-value, credible interval, causal rainfall inference, or original-programme gate promotion.
