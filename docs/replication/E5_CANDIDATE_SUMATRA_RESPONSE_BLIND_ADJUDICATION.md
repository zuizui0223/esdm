# E5 candidate screen: Sumatra paired-camera mesopredator study

Status: **E5_CANDIDATE_NOT_QUALIFIED**

This candidate was screened without opening any biological data row.

The field design is genuinely attractive for detection work: the published study used
292 paired camera stations across four Sumatran study areas, with two cameras of the
same brand at each station. The public workbook also preserves a station identifier,
event time and species code at schema level.

The decisive limitation is the released response schema itself. The five response
columns are:

`No`, `Station_ID`, `time`, `spc`, `sa`.

There is **no individual camera identifier, camera side, paired-sensor identifier or
camera brand field** in the public response schema. Therefore the two physical cameras
cannot be reconstructed as separately observed detection channels from the released
data. A paired-camera field design does not by itself satisfy E5 G4 once the public
response has collapsed the pair to station-level records.

Accordingly:

- G1 independent source: PASS
- G2 schema/effort/time: PARTIAL
- G3 geography × source crossing: NOT ESTABLISHED
- **G4 detection identifiability: FAIL**
- G5 physical replication: capacity PASS, split not frozen
- G6 temporal support: potentially adequate only after a frozen multi-area split
- G7 model freeze: NOT REACHED

No row 2+ value, species detection row, focal outcome, predictive score or model fit was
opened. No rescue by opening response values is authorized.
