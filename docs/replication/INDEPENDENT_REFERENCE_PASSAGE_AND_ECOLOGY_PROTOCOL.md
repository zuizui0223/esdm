# From E7-C observation support to independently identified diel passage and detection

**2026-10-29 — operational evidence protocol, not a new E7 result, synthetic generation, or E5 qualification.** Use the terminal E7-C read-only support result as the reason to collect a *different class of evidence*, not to revise its failed 1/66 vs 9/66 original strict support outcome.

## Falsifiable ecological question

**Do the species-relative rates of independently observed animal passage (night versus midday) change with measured precipitation/vegetation/human-disturbance context after accounting for taxon-specific camera capture?**

The prior 11-season Snapshot Serengeti analyses show that *observed camera sequences* can have nonportable species-relative diel contrasts, while strict same-camera/year comparisons lack complete support. Neither stage tells us whether actual passage changes or sensor yield changes. The new test is to observe *independent passages* with a reference system while recording exact camera operation and environmental exposure. Only then can a daylight/season contrast be split into ecological passage versus detection stages without treating an image as a true passage.

Do **not** assume a new ecological response, positive effect, or transfer success. Site-specific vegetation, rainfall, resource phenology and human/dog use must be measured objectively and **prospectively selected**, not inferred from animal sequence counts or calendar month alone.

## Required sampling arrangement

At each matched site and period:

- An **independent continuous or pre-randomized-time reference video/thermal sensor**, time-synchronized to the focal motion camera, covers a **pre-defined focal camera reference zone**. Reference observation times must **not be chosen because the focal camera triggered**. Every passage gets an independent persistent ID *before* matching camera events.
- Preserve independent reference identity (`independent_passage_id`) and trigger-event identity (`camera_event_id`), including **reference-known passes not triggering any image**. Use one-to-one audit of crosswalk; ambiguous, duplicated or uncertain matches are rejected rather than guessed by similar species/time.
- Log the exact overlap of operating focal-camera minutes and reference-observation minutes for each **physical site × ecological phase × clock window**; record all camera downtime and non-reference intervals. A zero event count with verified reference operation differs from a camera that was turned off.
- Record independent species identity and actual timestamp with timezone, then objectively prespecify ecological phase (e.g. measured wet/dry conditions, not merely a seasonal label). Use source-observed clock bins **night 21:00–03:59** and **midday 10:00–15:59** as fixed here; this is **not astronomical solar-time correction**.
- Log **two observation stages** for every independently observed pass: (1) did focal camera trigger? (2) did that trigger register the correct species? A registered pass requires a matched camera trigger. Multiple simultaneous animals in one trigger, duplicate triggers, missing identities or observer failures need separately predeclared adjudication; **do not silently count them as zero**.
- If the reference camera itself misses passages, that **unknown reference detection** still prevents unconditional identification of true activity. Check reference completeness with a second independent view or other validated coverage procedure, and preserve the declared observable zone and field-of-view boundaries.

### Machine-readable source contract (implemented)

`scripts/independent_reference_passage_audit.py` consumes exactly two UTF-8 CSVs:

**`reference_effort.csv`**: `site_id, phase, clock_bin, camera_operational_minutes, independent_reference_minutes, reference_sampling_scheme`. Every exposure must be strictly positive. Reference time is the overlap with focal camera operation. Valid sampling schemes: `continuous_reference` and `randomized_time_blocks`. A camera-trigger-selected reference is **rejected**. If randomized, its fixed probability/inclusion design must separately be recorded for valid landscape extrapolation.

**`reference_passages.csv`**: `independent_passage_id, site_id, phase, clock_bin, species, reference_source_id, reference_timestamp, camera_triggered, species_registered, camera_event_id`. Passage ID must be unique, timestamps have an explicit UTC offset and agree with the declared clock bin, camera stage flags must be 0/1, no camera event may match two passages, and registered species must never exceed triggered passes. A pass known to the independent video but **missed by the motion camera** has `camera_triggered=0, species_registered=0, camera_event_id=""`.

For observed reference passages in a cell, the code reports:

`P(trigger | independent reference passage) = triggered / N_known`

`P(register species | trigger, independently known passage) = registered / triggered` (undefined if triggered=0)

`P(effective register | independent reference passage) = registered / N_known`

`Independent reference-passage rate = N_known / reference-observed hours`.

These are **within-zone, within-sampled-time conditional descriptors**. They are not estimates of landscape abundance, a camera manufacturer's generic detection constant, or an E5 G4 pass. An observational cross-region comparison still requires crossed camera/protocol geography, known reference integrity, site-level clustered uncertainty and the previously frozen E5 physical/temporal standards.

**Important**: the program does **not** infer a missing reference-source sensitivity or correct original E7 for detection. It validates that the *new* future data could separately measure ecological reference-pass rates and focal-camera yield before a defensible ecological effect model is used.

## Synthetic, falsifiable demonstration: a false nocturnality shift

In the new tests, the true **independent reference passage counts are 10 night and 10 midday in each of two phases** (both 10 hours of verified reference exposure). In phase A, the camera correctly registers **5/10** night and **5/10** midday; in phase B, **2/10** night but **8/10** midday.

- Independent reference night/midday rate ratio stays **1.0 → 1.0**: zero observed ecological passage-ratio shift in this controlled, synthetic setting.
- Camera registered night/midday ratio shifts **1.0 → 0.25**, a four-fold *apparent* decline in nocturnal activity.
- Known-passage effective camera yield shifts from **50% / 50%** (night/midday) to **20% / 80%** in B: exactly the source of the false shift.
- The validator rejects duplicate independent IDs, missing trigger fields, registration without a trigger, one camera event matched to multiple reference passes, wrong timestamp bin, no reference exposure, and camera-trigger-selected reference observations.

This is a **constructed proof-of-identifiability illustration, not an observed animal result**. It concretely shows why E7-C's complete camera count cells, even when present, cannot by themselves distinguish animal activity from observation process.

## Separate new public-data paths — what each actually measures

| Independent published material | Useful ecological information | Missing for a *known passage* calibration |
|---|---|---|
| [Glasgow urban camera traps 2024](https://doi.org/10.5285/e41601be-1fc7-47ed-85c4-ec00be0c3f93), McGhee et al. (2025) | 24 green spaces; Apr–Sep 2024 fox, roe deer and grey squirrel image observations; site setup/takedown times; camera detection-zone descriptions; monthly mean domestic-dog observations; movement-speed video subset Jun–Dec | Detection-zone geometry and speed are **not independent records of every undetected passage**; no documented synchronized continuous reference-passage denominator in the published metadata. Suitable for a **separate observational urban-ecology analysis** after source and schema audit, **not** automatic E5 G4 |
| [MammAlps 2025](https://doi.org/10.5281/zenodo.15040901) | 9 cameras, 3 Swiss Alpine sites; ~14 hours curated multi-view videos, labelled behavior and weather, 397 long events including false triggers; published camera/time/event IDs | Triggered/curated multi-view video and reidentification are **not a complete independent denominator of animals that never triggered**. Also only 3 sites and Aug–Oct; no cross-regional six-month transfer replication |
| [Findlay CCTV calibration (2020)](https://doi.org/10.1007/s13364-020-00478-y) | CCTV known passage reference, separable camera trigger and registration, useful direct stage definitions | Original exposed files lack **independently verified stable passage ID crosswalk** (#214); no matched different-geography long-duration transfer |
| E7/C Snapshot Serengeti already frozen | 2.66 million sequence metadata, 11 collection seasons; rich species and time patterns | No independent known-passage or focal trigger/registration calibration; strict four-positive-cell support only 1/66 vs 9/66 in E7-C |

These are **not interchangeable ecological responses**. Do not merge them into a pooled effect or treat Glasgow's detection zone / MammAlps multi-camera events as independent reference denominators just to pass E5. Published facts above describe scope only; no Glasgow or MammAlps biological row has been opened in this task.

## Practical independent ecological validation design

A future study can separately test: **(H1)** a species × measured-environment difference in independently referenced night/midday passage ratios; **(H2)** a species × environment × clock change in trigger or registration yield; and **(H3)** whether a passage-based estimate learned at one set of physical sites predicts **unopened** sites, with explicit effort, sensor and reference protocol crossing.

The ecological estimand is not the number of positive camera images, but the difference of **reference-observed passage-rate log night/midday contrasts** for two prespecified species and two prespecified environments, with independently estimated detection yield used to explain camera-only discrepancies. Formally, for species `i`, environmental phase `e` and clock `t`: `lambda_ref(i,e,t)=N_known(i,e,t)/E_ref(e,t)`; compute species-relative `[log(lambda_ref(i,e,N)/lambda_ref(i,e,D)) - log(lambda_ref(j,e,N)/lambda_ref(j,e,D))]` only where both reference rates are defined. Count zeros remain explicit; do not impute or invent the numerator. Reference temporal strata, not image timestamps alone, define the denominator. Population-level inference must respect physical-camera clustering and independently verify reference sensitivity.

**No claim now** that Glasgow, MammAlps or this new code provides those passage-based estimates. The existing E4, E5 (0/17, G4 unpassed), E7 and E7-C endpoints are unchanged. Avoid more synthetic model generations; the actual missing scientific input is **independently recorded passage × operational reference effort × taxon-specific camera yield**, not another model variant.
