# NeoBat cross-country link-transfer secondary robustness (2026-11-19)

Source: already reproduced exploratory result at
`docs/replication/neobat/crosscountry_reproduction_result.json`;
verdict `docs/replication/neobat/crosscountry_reproduction_verdict.json`
reports eight exact source-only comparisons PASS.

This summary is **descriptive reweighting**, not new independently
confirmed effects. Six of twelve source countries qualified before the
comparison (338 heldout positive edges). Null uses 999 within-country
degree-preserving graph rewires and reference-exclusion cross-country
training only.

| Heldout country | Eligible reported edges | Observed recurrence | Degree null mean | Difference (pp) |
|---|---:|---:|---:|---:|
| Brazil | 65 | 0.5385 | 0.4310 | +10.75 |
| Costa Rica | 86 | 0.4651 | 0.3798 | +8.53 |
| French Guiana | 18 | 0.5000 | 0.4660 | +3.40 |
| Mexico | 31 | 0.7097 | 0.6411 | +6.86 |
| Panama | 113 | 0.2832 | 0.2016 | +8.16 |
| Peru | 25 | 0.3200 | 0.3138 | +0.62 |

- Country-equal mean difference: **+6.386 percentage points**;
  Monte Carlo upper-tail p=0.001 (approximate MCMC null).
- Link-count-weighted descriptive mean difference: **+7.822 pp**.
- All 6 eligible countries have positive descriptive contrasts;
  a positive direction alone is not a country-specific significance test.
- Leave-one-country-out COUNTRY-EQUAL mean contrasts range **+5.513
  to +7.540 pp**. No one qualifying country accounts for the sign.
- Only **6/12 source countries qualified**. The result does NOT imply
  global or all-Neotropical universality, and links missing from
  reference literature are not verified absent.
- Sensitivity requiring >=2 independent *training* references per link:
  +5.662 pp above degree-null; this does not certify independent raw
  field survey sources.

**Maximum permitted interpretation:** NeoBat published fruit-consumption
partner identities show above-degree recurrence across source-country
subsets, supporting use as a prior for future *predictive resource-link*
tests. This neither verifies plant abundance nor demonstrates that
Neotropical bat ranges are driven by plant partners. The SDM out-of-region
performance contrast M3 vs M1 still has not been fitted.
