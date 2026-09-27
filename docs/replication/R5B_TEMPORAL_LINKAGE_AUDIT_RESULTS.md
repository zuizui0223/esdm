# R5b Temporal-Linkage Replication Audit

Status: **AUDIT COMPLETE — FIRST EMPIRICAL ENDPOINT UNCHANGED**

This is a separately named descriptive replication/audit of the data-integrity failure
that terminated the first frozen R5b empirical endpoint. It is not a rescue analysis and
does not reopen the empirical model fit.

## Provenance

- first empirical terminal result:
  `docs/empirical/SNAPSHOT_JAPAN_CAMTRAPDP_TERMINAL_RESULT.json`
- audit run: `36298031647`
- audit head: `40705dcecce0ddc1bf757f7865739a472275db48`
- artifact ID: `10924373256`
- artifact SHA256:
  `8a6438cbd03a53c6722cbccd8d2d04076c3c16887782af6b04e7af8e023b81d3`
- source MD5:
  `742f186013ef3b60e9754df73e5269de`
- source SHA256:
  `2e99786857764151b66bfda0caaba4f23288ed9d671bb86c9ea5605727b9c07c`

The independent ZIP SHA256 matched the GitHub artifact digest.

## Main finding

The event that triggered the frozen empirical STOP, `7815128`, was **not an isolated
record**.

Across all unique event-level animal observations:

- events: **7,620**
- outside-deployment events: **13**
- violation rate: **0.1706%**
- before deployment start: **0**
- after deployment end: **13**
- all 13 were within **24 hours** after deployment end
- 4 were within **1 hour**
- median excess beyond deployment end: **22,007 s = 6.11 h**
- maximum excess: **74,666 s = 20.74 h**

The 13 violations occurred across 10 deployments.

## Sika deer subset

For `Cervus nippon`:

- unique events: **1,430**
- outside-deployment events: **4**
- violation rate: **0.2797%**
- before start: **0**
- after end: **4**
- all 4 were within **24 hours**
- 2 were within **1 hour**
- median excess beyond deployment end: **7,686 s = 2.14 h**
- mean excess: **9,625 s = 2.67 h**
- maximum excess: **22,007 s = 6.11 h**

The four focal violations were:

- `7815128`: +1,121 s (+18 min 41 s)
- `7815129`: +12,367 s (+3 h 26 min 7 s)
- `7811733`: +3,005 s (+50 min 5 s)
- `7811315`: +22,007 s (+6 h 6 min 47 s)

They occurred at three Gunma deployments; two violations were at
`...kusaki5`.

## What this rules in and out

Every violating event timestamp and deployment start/end used the same `+00:00` offset.
The audit therefore found **no simple timezone-offset mismatch**.

The pattern is also inconsistent with a broad timestamp-system collapse: more than
99.8% of all animal events satisfied the exact frozen interval rule.

Descriptively, the failure is instead concentrated at the **deployment-end boundary**:
all detected violations are after the recorded end, all within one day, and the focal
failure belongs to a small repeated set rather than being unique.

That observation does **not** authorize a one-day grace period, row deletion, interval
extension, or any other correction. Those would be new scientific/data-processing rules
chosen after response opening.

## First empirical endpoint remains unchanged

The first frozen R5b empirical endpoint remains:

`CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY`

with:

- model fits: **0**
- heldout scores: **0**
- activity gain: **not estimated**
- state gain: **not estimated**

No row was excluded, no timestamp was repaired, no deployment interval was widened, and
no model was fit in this audit.

## Proper next use

If the project later studies whether camera-trap deployment endpoints should permit a
documented tolerance or independent adjudication rule, that must be a **new replication
protocol frozen before its own outcome**, and it cannot be reported as the first R5b
empirical endpoint.
