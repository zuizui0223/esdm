# E7: Snapshot Serengeti — seasonal reordering of a recorded mammal community

**Frozen protocol: 2026-10-19. Predeclared before the first independent Serengeti biological annotation is opened by ESDM.**

## General ecological question

**Does the *relative diel organization* of a co-recorded mammal community change between the Serengeti's characteristic wet and dry seasons, after conditioning on the same physical camera location and hydrological year?**

E4 MICA discovered species-differential temporal changes within one camera network. E7 is intended to test the *generality of species-relative changes* in a **new protected African-savanna assemblage**, with season as the independently grounded gradient. The same species and direction are NOT assumed; Serengeti labels differ. This is a temporal/seasonal independent biological response, **not** a replication of MICA geography/source or a substitute for E5 detection calibration.

Rainfall context: Serengeti's annual wet period is broadly **November–May**, dry period **June–October**, with two wet-season rainfall peaks. We **predeclare the core-period contrast** wet **November–April** versus dry **June–September**, excluding **May and October** as transitional months. This is a climatological proxy, not individually measured rainfall, and must not be retrospectively changed after the result. Sources: Mahony et al. (2021), doi:10.1002/joc.6831; LILA Snapshot Serengeti data description.

## Independent public records and separate validation

- Official source: [LILA BC Snapshot Serengeti](https://lila.science/datasets/snapshot-serengeti), 11 seasons, COCO Camera Traps JSON and original animal classifications, not images.
- Per-season original metadata ZIPs under `https://lilawildlife.blob.core.windows.net/lila-wildlife/snapshotserengeti-v-2-0/SnapshotSerengetiSNN.json.zip`, where NN is **01…11**. Source-format headers/manifest and checksum are inspected before full biological processing; any unavailable season is explicitly logged as a **transport stop** instead of silently substituted.
- Discovery seasons **S01–S05**, validation seasons **S06–S11**, fixed by original collection-season index, not calendar-year re-ranking or outcome fit.
- **No wildlife images** are downloaded or retained. The labels are attached to images but may be trusted only at *sequence level* per LILA documentation.
- Human labels remain in the original metadata despite image removal. **Exclude the human class and all clearly non-animal/empty/noisy classes.** No human frames, coordinates or individual camera IDs exported.
- Each annotation is reduced to at most one (`seq_id`, normalized species category) event. Detectable categories that label different sexes/ages of the **same** animal (e.g. `lionfemale`/`lionmale`/`lioncub`) are collapsed to `lion` before roster selection; other category mappings are fixed by an explicit look-up table before outcome inspection. Unrecognized ambiguous categories are excluded and counted.
- Sequence location, timestamp, camera season and image identifier are read from `images` records, joined to `annotations` via exact image ID; a sequence's image records should have one consistent location/timestamp. Contradictory sequence metadata are quarantined. We do not infer additional animal passes beyond sequences.
- No calendar-time timezone conversion is applied to the documented local Serengeti timestamp (UTC+3, no daylight saving). Deep night = **21:00–03:59**, midday = **10:00–15:59**, omit other periods to reduce uncertain twilight conditions. This is recorded clock-based diel composition, not true continuous activity intensity.

## Frozen biological roster and 66 comparisons

From **S01–S05 only**, choose the **12 most broadly sampled eligible nonhuman animal categories**, ranked by the number of (`camera location`, hydrological year) combinations with at least one species-positive sequence (ties: number of distinct eligible sequences, then normalized label lexicographically). Category selection does **not** inspect night/midday ratios or wet/dry effect signs; **S06–S11 is not consulted before the list is fixed**. If fewer than two taxa qualify, end with `INSUFFICIENT_ROSTER`.

Use all unordered combinations of the fixed 12 panel taxa (**66 pairs**) and retain nonestimable pairs. The primary contrast is within each camera location×hydrological-year block, year running **November 1–October 31**. A camera-year enters a pair's wet/dry comparison only when the *same named camera site* has events for **both species in both core periods** and each period has both night and midday represented across the pair. Counts should be sequence-unit, not image count. Site-year pairs with only one period are excluded with a separate insufficient-support count.

For each `site×hydrological-year×season-phase` build species1/species2×night/midday table, compute descriptive Mantel–Haenszel pooled species-relative night/day odds across matched site-year blocks **separately within wet and dry**, then `delta_ij=log(OR_dry/OR_wet)`. No 0.5 additions or imputed daytime events. A pair's result is estimable only if **at least 5 distinct physical camera sites, 10 matched hydrological site-years and 3 distinct season-index collection folders** contribute, and both pooled stage crossproducts are positive. No threshold tuning by the answer.

- Primary ecological descriptive output: all 66 fixed pairs, share estimable, share with rank reversal (wet/dry relative odds cross one), and each pair's camera-site-level leave-one-out range where still supported.
- Validation: do this separately for **S06–S11**, *using exactly the discovery taxa* and equal matching rules; count sign-concordant pairs among those estimable in both periods and robust to single-camera exclusion.
- Negative control: do **not** claim numerical independence from repeated sampling of the same cameras across seasons; the holdout is independent **in collection-season index and source responses**, not independent in camera hardware or organism population.
- A universal wet/dry detector multiplier shared by species, time, and site would cancel from a within-camera 2×2 ratio. **Species-specific detectability, vegetation obstruction, solar-hour mismatch, seasonal abundance/migration and camera effort remain alternative mechanisms**; these are separate empirical hypotheses.

## Transport and analytic firewalls

1. First run checks only anonymous HTTP HEAD for S01/S06/S11 JSON metadata ZIPs. Do not read species annotations in the source availability check.
2. Only after successful anonymous storage access, run a **new separately designated empirical workflow** that checks real per-season JSON structures and **hashes all downloaded metadata archives** before opening biological labels. If site-time fields or category relations are absent, stop rather than manufacture them. No image download.
3. Each stage uploads a machine-readable receipt and terminal status. No outcome-adaptive species selection, threshold relaxation, biological rerun, or endpoint switch. A transport failure is not a biological negative result.
4. Source archive digests are recorded from verified downloads so later runs can pin those bytes; no fabricated hashes. Biological results are explicitly exploratory until reproduced independently.
5. No event-level p values or confidence intervals from pseudoreplication. Physical cameras are the independent clustering unit but remain potentially correlated spatially; first-stage outputs are descriptive.

**Original E4 and E5 results remain frozen. E5 = 0/17 original qualified datasets and G4 remains unpassed.**
