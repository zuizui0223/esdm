# NeoBat source-matched original Colombia three plant transfer: ecological input identifiability test

Date: 2026-11-19. Fixed protocol `NEOBAT_SOURCE_DATASET_MATCHED_3PLANT_CO_PILOT_FROZEN_20261119.md`. Synthetic tests [Actions #44537146799](https://github.com/zuizui0223/esdm/actions/runs/44537146799) PASS. Original full GBIF DOI + WorldClim climate/elevation source SHA checks, original plant country×species cell count replay, and all three source-matched models [Actions #44537284683](https://github.com/zuizui0223/esdm/actions/runs/44537284683) PASS.

## Fixed Colombia holdout results

| Plant | Train source-matched focal cells | CO heldout focal/source-bg cells | Abiotic only AUC | Other-plant recorded-intensity only AUC | Abiotic + intensity AUC | Added environment AUC | Exact-intensity conditional AUC; comparable pair fraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| *Cecropia obtusifolia* | 249 | 21 / 525 | 0.530 | 0.710 | 0.732 | +0.022 | 0.583; 5.49% |
| *Ficus insipida* | 232 | 78 / 504 | 0.476 | 0.795 | 0.767 | −0.028 | 0.493; 4.31% |
| *Piper aduncum* | 302 | 61 / 521 | 0.512 | 0.844 | 0.839 | −0.004 | 0.606; 2.95% |

The AUCs use newly source-`datasetKey`-restricted pseudo-backgrounds, so they are **not paired score improvements over the earlier 3-plant evaluation**, whose background population differed. All three pre-fixed sentinel plants qualified; no source failures, model options or heldout country altered. All records are derived from the already-opened GBIF discovery universe and are post-hoc to the first pilot, not independent validation. Dataset identifiers were required only in RAM and are not saved in results.

## Main scientific conclusion

Under a stricter GBIF original source collection match, the plant record-density proxy **still largely determines heldout prediction** (AUC ~0.71–0.84), while temperature, precipitation and coarse elevation add only −0.028 to +0.022 to that proxy. Conditioning on **exactly the same observed other-plant species count** yields equivocal AUC ~0.49–0.61 over only 3–5.5% of all test positive×pseudo-background pairs. This is evidence of an **observation/source-identifiability failure mode for this data + model**, not proof that real plant ecological niches are unconstrained by climate or that food plants do not determine bat occurrence.

The all-106-plant × all-17-country original source **quantity gate** (1,802/1,802 trainable, 677 test-scorable) still holds. However **trainable quantity is not validated ecological plant suitability**. Do not treat future source-effort-driven high AUC as resource abundance or automatically use it in M3. Original 255-plant v1 M0/M1/M3/N1 contract and main remain unchanged, with ecological bat M3−M1 and M3−N1 **unestimated**.

## Next non-outcome-selected test

Assess whether this observation-intensity dominance extends beyond the original fixed Colombia sentinels by applying the same now-frozen source-matched conditional contrast to the entire **106×17 original cohort**, retaining non-scorable countries and equal country/species summary weights. It must be a plainly labeled **exploratory multi-country source transfer diagnostic**, with no claim of independent data or universal ecological effect. Independently measured botanical abundance, fruit phenology, or another survey design would still be needed for a causal feeding/resource SDM.
