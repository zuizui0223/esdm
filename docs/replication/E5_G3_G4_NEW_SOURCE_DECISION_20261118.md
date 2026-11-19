# E5 G3/G4-first reassessment: do not confuse multimodality with detection identification

**2026-11-18 | Response-blind public-documentation decision | Not an empirical ecology result**

## Why this assessment is necessary

The frozen E5 gate has **0 of 17 standard-qualified datasets**. The limiting conjunction is **G3** (source/protocol not confounded with geography) **and G4** (an independently identifiable observation/detection channel). A paper reporting multiple camera models, paired cameras at nonoverlapping viewpoints, event-declustered records, or co-located microphones does not in itself provide a known denominator for animals the focal camera missed. The elementary esdm M2 proof further requires many independent regions with repeated sites and occasions to separately recover a shared regional pool probability, conditional site occupancy and composite effective recording; even this does not split availability from registration without independent reference.

This is a targeted assessment of *three external resource families*, **not an expansion from 17 to 20 formal E5 candidates**, a new version of the E5 gate, or a field-data reanalysis. Only public release documentation was read. EOW's existing open PR #190 already describes a G4-first protocol concept; it does not establish released event-level calibration. The older Kays41 raw-header PR #191 is separate and remains unqualified; this assessment neither merges those PRs nor reopens their source.

## Source 1: European Observatory of Wildlife

The examined public [EOW Results Database v13 (30 June 2026)](https://zenodo.org/records/21060656) advertises an XLSX with policy, site metadata, **site-year summary metrics** and legend, plus the REM photogrammetry protocol PDF. Its density workflow can use calibration poles and distance estimation, but **these are not evidence that independent passage/miss reference rows and matched deployment records were released**. `G2=NOT_DEMONSTRATED`, `G4=NOT_DEMONSTRATED`, `G3=PROMISING/UNVERIFIED`; **do not promote**. Zenodo marks the version as having a newer version; the statement is restricted to the examined release and does not claim to have exhaustively audited every later version or privately accessible material.

## Source 2: SmartWilds cross-modal dataset (2026-11-08 camera update)

The [SmartWilds public repository](https://github.com/Imageomics/smartwilds) and [dataset card](https://github.com/Imageomics/smartwilds/blob/main/metadata/smartwilds_metadata.md) expose **19,785 camera Events**, **235,778-image inventory**, acoustic, drone and visitor observations in a common Darwin Core event hierarchy, with site/campaign alignment. The same Ohio conservation facility was sampled in 2025; there is **no independent geography × protocol crossing**. Importantly:

- [Joining guide](https://imageomics.github.io/smartwilds/datasets/joining/) documents shared site codes (TW02, TW06, TW09) and corrected clocks; these allow *cross-modal observational corroboration*, not a complete passage denominator.
- [Defect inventory](https://github.com/Imageomics/smartwilds/blob/main/metadata/DEFECT_INVENTORY.md) explicitly flags wrong/unset clock on **93.9% of images**, camera relocation and battery gaps, and **true deployment/retrieval times that cannot be reliably reconstructed in some cases**. Correcting observation timestamps does not prove camera active minutes.
- Most occurrences are machine labels and bursts/frames duplicate animals; a zero occurrence is not known absence. Acoustic detections are vocalizations, drone sorties cover selected flight windows and locations; neither systematically enumerates all silent/undetected animal passages through the focal camera's physical zone.

Therefore `G3=FAIL (one geographic site network)`, `G4=NOT DEMONSTRATED (no separately identified detection channel)`, `G2=PARTIAL` and `G6=FAIL` for the frozen ≥6 calendar months on *both* sides. The original frozen G4 additionally allows a rigorously identified replicated-sensor or repeated-visit observation model, or independent deployment-linked ranging calibration. This assessment does not prohibit those alternatives; none is established by the released source documentation examined here. Do not count camera events or images as independent biological replicates. **The public release is valuable for a separate methodological question—cross-modal clock/label/effort reconciliation—not the standard E5 identifiable detector fit.** No SmartWilds event/occurrence rows were opened here.

## Source 3: Qilian Mountains desert steppe

The [published data descriptor (2025)](https://www.nature.com/articles/s41597-025-06105-2) reports 22 cameras deployed in the Qilian Mountains from December 2020 to January 2022, with effort documentation and [3,828 time-declustered camera detection events](https://doi.org/10.5281/zenodo.15733158). These are **not** observations of passages missed by all cameras; they are independent *camera-triggered* detection events defined by a time threshold. Thus no independent G4 identification is demonstrated by this event table. The study is one regional network, so `G3=FAIL` for the frozen crossed geography/source test. No source event values were read.

## Biological conclusion and next action

**No new standard E5 dataset was qualified; the 17-source registry and 0/17 outcome remain unchanged.** There is no ecological positive or negative result to add to esdm, no valid correction to E4's activity transfer, and no evidence of esdm beating an SDM.

The next meaningful step is not to add an 18th semisynthetic gate or retrofit older responses. Request from data holders an **independent paired passage-reference package** using the already-implemented [three-table protocol](INDEPENDENT_REFERENCE_PASSAGE_AND_ECOLOGY_PROTOCOL.md): (1) camera/reference minutes and sampling scheme, (2) timestamped operating-interval overlaps with stable station-to-device crosswalks, (3) independently identified passages including camera nontriggers, followed by a genuinely crossed geography/protocol and a frozen geographic holdout. An eligible **alternative G4 route** remains permissible under the original frozen contract if paired sensor, repeated-visit or calibration data separately identify effective detection with a documented model; simply having extra sensors or repeated events is not that proof. The existing `scripts/independent_reference_passage_audit.py` must validate supplied data *before any focal outcome or model fit*.

This record **does not infer that no private calibration data exist**, claim that other cross-modal studies are scientifically weak, or substitute restricted calibration photos for known animal passages. It documents precisely the currently demonstrated E5 limitation so future work can go directly to a different evidence class.

Machine-readable summary: [`E5_G3_G4_NEW_SOURCE_DECISION_20261118.json`](E5_G3_G4_NEW_SOURCE_DECISION_20261118.json).
