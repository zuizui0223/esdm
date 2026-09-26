# R5b First Empirical Opening — Terminal Result

Status: **CONSUMED STOP — NO MODEL FIT**

The semi-synthetic programme was frozen at v0.4-R5b and the first biological-response
opening was executed once under the preregistered empirical contract.

## Source

Snapshot Japan 2023, Camtrap DP 1.0.1:

- supplement DOI: `10.3897/BDJ.13.e141168.suppl4`
- Zenodo record: `15030971`
- file: `oo_1246258.zip`
- opened bytes: **8,630,359**
- MD5: `742f186013ef3b60e9754df73e5269de`
- SHA256:
  `2e99786857764151b66bfda0caaba4f23288ed9d671bb86c9ea5605727b9c07c`

The frozen source identity therefore matched exactly.

## Frozen provenance

- empirical response run: `36272212826`
- outcome head: `d024d064c71f65c13d679a2289c040b3940e8b05`
- capture artifact ID: `10916226656`
- artifact SHA256:
  `16a658a1f1bf4512be054381a1f4bb8f71c016f81813d14c5428d6d49c002b0f`
- independent ZIP SHA256 matched the GitHub artifact digest.

## Terminal integrity result

The response archive was opened and `observations.csv` was parsed under the frozen
Camtrap DP adapter.

The run stopped on the preregistered integrity rule:

> focal event `7815128` lies outside deployment interval

Terminal status:

`CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY`

This happened **before any model fit**.

Therefore:

- model fits: **0**
- heldout scores: **0**
- activity gain: **not estimated**
- state gain: **not estimated**
- no empirical biological support/null/adverse classification was produced.

## Why this is terminal

The full empirical contract froze, before response opening:

- exact event/deployment temporal linkage;
- no timestamp repair;
- no row deletion;
- no deployment-interval widening;
- no parser retuning after response;
- no candidate switch after a consumed biological response.

Accordingly, the offending event is not repaired or excluded and the endpoint is not
rerun.

## Interpretation

This is not a negative result for the eSDM ecological decomposition.

It is a **real-data contract failure** showing that the first external dataset did not
satisfy the exact temporal linkage required by the already-frozen R5b empirical model.

The key development milestone is nevertheless complete: the project left the
semi-synthetic gate loop, froze the model, opened a real response exactly once, and
accepted the preregistered terminal outcome without redesigning the model around the data.

## Stop

No new semi-synthetic v0.x gate and no replacement empirical candidate is authorized by
this programme.

Any future attempt to study relaxed timestamp linkage, row adjudication, or a different
dataset must be a separately named exploratory/replication programme and may not be
reported as the first frozen R5b empirical endpoint.
