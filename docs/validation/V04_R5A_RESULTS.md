# v0.4-R5a Direct State-Composition Qualification Results

Status: **PASS**

R5a tested whether a prospectively fixed direct state-composition calibration stream
can repair the hard state-information failure that persisted through R2, R3a, and R4a.

The R4a observation geometry and all frozen R2 identification thresholds were retained.
R5a added one state-only calibration stream at the same 36 × 12 training contexts, with
one expected direct state label per exposed context and no held-out calibration exposure.

This was identification-only. No MCMC recovery or held-out transfer was run.

## Frozen provenance

- qualification run: `35841753079`
- qualification head: `f98586a61a9a3be5c7573e9e271744bd501cf11b`
- gate freeze commit: `d013b5168d7d10848d1d366669d45f83f873692a`
- gate blob expected/observed:
  `e5cef8c3ce8e1dd096ef45cc436a93ba6740bafb`
- artifact ID: `10741962664`
- artifact name: `v04-r5a-qualification-35841753079`
- GitHub digest:
  `sha256:937ac6311cadf09e759ad27c47ef2ca72d53204934b3fd768757f68495805fe2`
- independently downloaded ZIP SHA256:
  `937ac6311cadf09e759ad27c47ef2ca72d53204934b3fd768757f68495805fe2`
- source Git blob expected/observed:
  `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`

The audit artifact reports `infrastructure_block = null`.

## Mechanical result

**All 12 frozen R5a terms passed.**

This includes:

- all 13 positive targets structurally identified at Anchors A/B/C;
- all 13 positive targets practically non-weak at Anchors A/B/C;
- sparse structural identification retained;
- sparse practical refusal retained;
- unknown annotated-detection refusal retained;
- existing annotated contexts = 432;
- calibrated PresenceOnly contexts = 432;
- direct state-calibration contexts = 432;
- expected direct state labels = 432.0;
- direct state-calibration held-out contexts = 0;
- exact R4 annotated geometry preserved;
- state-only observation contract preserved.

## Hard Anchor-C state result

The unchanged practical threshold was `target_sd_proxy <= 0.25`.

R4a had failed Anchor C for all four state slopes:

| state target | R4a | R5a |
|---|---:|---:|
| precipitation | 0.27618 | **0.11499** |
| eastness | 0.32580 | **0.10497** |
| season | 0.29677 | **0.14155** |
| hour | 0.27386 | **0.13406** |

All four now pass with substantial margin.

The R5a Anchor-C global diagnostic also remains well-conditioned:

- relative minimum singular value = **0.0601038921**
- condition number = **16.6378576**

So the improvement is not a rank artifact.

## Interpretation

Across the frozen programme:

- R2 changed neither the information contract nor budget allocation and failed hard-state
  practical precision;
- R3a redistributed the same 432 annotated contexts toward more spatial replication and
  still failed;
- R4a balanced temporal contrasts and repaired Anchor A/B, but the hard Anchor-C state
  slopes still failed;
- R5a kept the R4 geometry and instead added direct conditional state-composition
  information, after which every frozen target passed the pre-MCMC gate.

Within this semi-synthetic design, the limiting issue was therefore not merely where
state-labelled observations were placed. State information was attenuated when it was
available only through counts proportional to ecological intensity × activity × state
probability.

A direct conditional state-composition calibration channel removes that attenuation and
makes the hard state slopes practically estimable.

This is a stronger methodological conclusion than “more data help”: **what is measured
can matter more than rearranging the same abundance-weighted observation cells.**

## Claim boundary

R5a does not establish posterior recovery, held-out transfer, empirical feasibility,
causality, or v0.4 promotion.

R5a **does qualify the exact R5a design for a separately frozen R5b recovery and
held-out-transfer gate**.
