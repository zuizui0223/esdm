# Barry B3: source-backed regional camera–dog sampling geometry

**Response-blind metadata outcome from [Actions 44476110681](https://github.com/zuizui0223/esdm/actions/runs/44476110681), [artifact 14505938405](https://github.com/zuizui0223/esdm/actions/runs/44476110681/artifacts/14505938405).** Original exact 1,788-byte [B3_BARRY_GEOMETRY_RESULT.json](B3_BARRY_GEOMETRY_RESULT.json), SHA256 `0de305d3bbe622b480c7edc1e76055b36520b08ee13a8cc48dc65234175ce00f`; artifact ZIP SHA256 `cb7d84af9156a1911ac89369572069fc434e62fd7f6eff54e09ab0ed6f46a6fd`. **Biological response fields `Fisher`, `pepe`, `caminop` and all individual or station coordinates were not accessed, interpreted, exported or used in any decision.** This is a sampling design result, not a fitted ecological distribution model.

## Exact outcome, predeclared mapping only

- **1,240** camera installation/operation metadata rows; **5,037** detector-dog segment metadata rows. None lacked the frozen province+sample-unit keys.
- The original data contain **5** distinct ecoregion/province codes; both observation methods occur in **4**, and each of those 4 has ≥10 distinct units per method.
- `CamStations.Sample Unit` and `DogTracks.SampleUnit` were matched only as exact whitespace-normalized strings **within** the same `EcoProvence_number`, as frozen *before* source opening. Result: **0 shared sample-unit keys in all 5 ecoregion codes**. Cross-region reused strings: 6 camera-side sample unit strings and 14 dog-side strings. Never join on unit name alone across geographic codes.
- No camera hardware ID was associated with multiple (region,unit) identities within the supplied camera metadata. This does not prove hardware could not be moved during other years or studies. Camera rows with named min/max dates: **1,234/1,240**; with `operating_days`: **1,240/1,240**; distinct recorded season labels: **3** (no labels or seasonal effect values exported).
- Dog segment public header has no time/date/duration column, preventing direct evaluation of dog observation exposure by month/day/night from this table. Original E5 G2/G6 conditions remain unevaluated or unsupported.

### Published ecoregion metadata counts (no fisher detections)

| Ecoregion code (only published numeric group) | Camera units | Dog units | Exact shared unit key |
|---|---:|---:|---:|
| 1 | 36 | 70 | **0** |
| 2 | 3 | 0 | **0** |
| 3 | 110 | 144 | **0** |
| 4 | 134 | 96 | **0** |
| 5 | 28 | 17 | **0** |

The zero under this strict key rule is **not evidence that no stations were visited by both methods**; the two published tables may use different identifiers, a different unit grain, or location-obscuring substitutions. Their source code or data dictionary would need to specify a physically valid join. Never infer a crosswalk from similar code values, research results, or hidden coordinates. The paper's claim of some jointly surveyed units remains an author-reported design detail, not falsified by this literal join refusal.

## Interpretation and decision

Four ecoregions with method-specific effort make geographic method-crossing **plausible at a coarse geographic level**. But direct *within-unit* comparison using the exact public ID fields is **unavailable**; no detector/passage ID pairing or independent misses are proven. This remains **unqualified under the original E5**, with **0/17** candidates qualifying. No observed fisher occurrence, true occupancy, false-negative rate, G4 identification, E5 improvement, or eSDM superiority was estimated.

Follow-on route should not keep modifying the same Barry unit join after seeing the mismatch. A distinct published **Clare et al. (2017) Dryad study** already has true paired camera-and-snow-track four-category observations at 238 numbered stations with up to nine occasions, providing a more direct (still single-geography) two-method observation question. The B1 manifest showed Dryad dataset API access and public six-file listing; any outcome analysis must have a separately frozen design, stable station rows and method-specific missingness checks before opening its original response table.
