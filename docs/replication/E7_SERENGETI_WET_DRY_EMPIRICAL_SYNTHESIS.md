# E7 empirical outcome: wet–dry recorded community reordering is detectable but does not transport as a fixed species-pair rule

**Empirical source opened:** 2026-10-19, technical compatibility restart [GitHub Actions run 39222089646](https://github.com/zuizui0223/esdm/actions/runs/39222089646). **Audit/synthesis:** 2026-10-28. This is an independent biological dataset relative to MICA E4, but **not a pristine one-shot computational execution**: an initial attempt failed on published bare `NaN` tokens, before any biological contrast was produced, and was transparently restarted without changing the frozen biological definitions. Its source hashes, success artifact, and endpoint are pinned in [the terminal receipt](E7_SERENGETI_WET_DRY_FROZEN_RESULT_RECEIPT.json).

## General ecological question

Do the same mammalian species pairs consistently swap their *relative recorded night-versus-midday timing* between a climatological wet and dry period in different collection seasons? The underlying scientific concept is *community-relative daily organization*, not solely single-species camera activity or a change in the number of images.

The **frozen** E7 design selected a discovery panel from Snapshot Serengeti S01–S05 camera-hydrological-year presence, without consulting S06–S11 annotation outcomes. Exactly 12 taxon labels were retained (zebra, wildebeest, spotted hyena, Thomson's gazelle, warthog, Grant's gazelle, giraffe, elephant, hartebeest, buffalo, lion, reedbuck); all **66** unordered pairs were evaluated against fixed same-camera/hydrological-year, wet (Nov–Apr) versus dry (Jun–Sep), deep night (21–03:59) versus midday (10–15:59) conditions. Each pair needed at least 5 independently named physical sites, 10 eligible site-years, 3 distinct original collection-season folders and positive MH cross-products. Other months and hours were excluded; no zero imputation was performed. This covers the named recognized categories, **not** all mammals or all continuous solar time.

### Fully documented original field-record coverage

Across the original 11 ZIPs, **7,178,440 image records**, **7,261,545 annotation records**, and **2,659,222 sequence IDs with camera metadata** were processed. The fixed mammal-label whitelist, core wet/dry calendar and sequence deduplication retained **494,385 eligible mammalian category-sequence records over all hours**, and **309,945 records** in the preregistered deep-night/midday windows. These counts are species×sequence endpoints, not unique animal individuals, true passages, total regional population estimates or independent sampling units. No image files were downloaded, and no individual locations or sequence keys were uploaded.

## Actual fixed endpoint — both halves, including failures

| Fixed community comparison | Discovery S01–S05 | Validation S06–S11 |
|---|---:|---:|
| Total predeclared species pairs | 66 | 66 |
| Comparable wet/dry site-year odds contrasts | **54** | **50** |
| Descriptive species-relative diel rank reversals | **14** | **3** |
| Reversals remaining on opposite sides of one after *every calculable* single-physical-camera deletion | **2** | **0** |

**Direction transfer:** 46 pairs were estimable in **both** halves; **23/46 = 50%** had the same sign of their dry/wet log species-relative odds change. There were **zero** stable rank inversions repeated in both halves. These are descriptive fractions across **strongly dependent** taxon-pair comparisons, not binomial-trial significance tests or calibrated predictive scores. They do not justify a claim that 50% is the true ecological reproducibility rate in a superpopulation.

Two informative discovery-only examples show why the original data split matters:

| Named taxon pair; odds for first taxon relative to second | Discovery wet | Discovery dry | Validation wet | Validation dry |
|---|---:|---:|---:|---:|
| Buffalo / wildebeest | 2.841 | 0.354 | 1.291 | 2.605 |
| Giraffe / hartebeest | 0.293 | 3.351 | 0.317 | 0.446 |

Both pairs reversed their relative *recorded* day/night ranking in discovery and the reversals survived removing any single qualifying camera site. Neither remained an inversion in validation. Buffalo/wildebeest even changed the **sign** of the dry/wet relative effect, whereas giraffe/hartebeest retained a positive dry/wet effect direction but without a rank inversion. The original conditions for sample eligibility were not relaxed to retain either one.

Two pairs exhibited unqualified (non-robust) rank reversals in both periods; only **lion/wildebeest** had a repeat in the *same dry/wet direction*, and it **failed the leave-one-camera-site robustness criterion** in both splits. This is not firm species-pair temporal niche transport.

## Positive ecological information and negative evidence

**Positive observational finding:** Site/hydrological-year-matched, season-associated changes in relative *camera-record timing* are present in this distinct African-savanna mammal assemblage. Thus the research question is meaningful outside MICA: camera-recorded daily-community relationships can shift along calendar-season context and can be compared at the species-pair level, rather than only by a whole-community night/day ratio.

**Not supported by the independent holdout:** a **stable species-pair direction** of seasonal reordering, or a robust inverted rank that persists from S01–S05 to S06–S11. The numerical results 23/46 and 0 robust transfer are specifically evidence **against promoting the initially strong discovery inversions to a universal portable rule**.

However, the lack of transport does **not** identify the ecological mechanism. Even at the same physical site and hydrological year, vegetation visibility, camera effort and configuration, taxon-specific detectability, animal migration, local community composition and weather can change with season. Matched site-period counts were not independently calibrated against missed animals. The heldout seasons can reuse physical camera locations, so their records are temporally distinct but not spatially independent.

Therefore do **not** claim that true temporal niches invert, interspecific competition changes, rainfall causes activity displacement, or that the weak direction transport necessarily reflects ecological stochasticity. The simpler explanation is that **a pair-specific universal effect is not supported under the current observation and transfer design**.

## Consequence for esdm

The model-level MICA E4 failure, the observed MICA rat/muskrat species-relative rank change, and this truly separate Serengeti dataset now illustrate two distinct layers:

1. **Observation layer:** community-relative diel patterns can differ across space, source and calendar-season context; apparently large discovery effects can be nontransportable across time.
2. **Process layer still unresolved:** whether such recorded changes reflect changes in true animal passage, species-specific detection, shifting activity budgets or cross-species interactions.

For a publishable **general ecological** claim, the next decisive study would test an **a priori environmental modifier** (site-specific precipitation, vegetation cover, resource phenology or camera conditions) with crossed site/time observations and taxon-specific observation calibration. A new classification or E8 gate is **not** a substitute for that independent identification. Any new environmental-response model after seeing these outcomes must be explicitly labelled **post-result exploratory**, with a fresh heldout ecological validation.

## Frozen evidence and no reclassification

- Exact source ZIPs: all 11 SHA256 hashes pinned in [source-format-stop receipt](E7_SERENGETI_SOURCE_FORMAT_STOP.json) and successfully verified in the technical restart.
- Independent-run [artifact 12173010259](https://github.com/zuizui0223/esdm/actions/runs/39222089646/artifacts/12173010259): full 126,404-byte JSON; artifact ZIP SHA256 `e210adc894a94827a295afba87ad72fa485e8721a65ca7db11c5931655e4edfe`, inner JSON SHA256 `21a0b03d8c17442ddeeed79023ec28d23525c2815ca7a0bbaf54faec12e65f2a`.
- [Machine-checkable summary and claim firewall](E7_SERENGETI_WET_DRY_FROZEN_RESULT_RECEIPT.json).
- Original E4 scores, one-shot posterior and support decisions are unchanged. Original E5 detection identifiability gate G4 remains **unpassed**, with **0/17** qualified candidates. **Neither** E7 nor the format-compatible retry qualifies E5.
