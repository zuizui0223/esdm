# ODSP transfer evidence portfolio v1

The source registry answers one question:

> May this frozen eSDM result be exported as an ODSP information-transfer contrast?

The evidence portfolio answers a different question:

> For sources that already passed that eligibility test, what population-level
> transfer evidence exists, and which comparisons are **not** scientifically
> authorized?

The portfolio is deliberately non-ranking.

## Current validated items

The portfolio contains exactly the sources marked `validated_exportable` in
`ODSP_TRANSFER_SOURCE_REGISTRY_V1.json`.

Current items:

- v0.4-R5b activity;
- v0.4-R5b latent state;
- v0.6a static accessibility;
- v0.7b marginal dynamic occupancy.

For every item the portfolio normalizes:

- lower and upper information levels;
- newly added information labels;
- ODSP population mean gain;
- population mean interval and status;
- observed positive-group fraction when available;
- new-group prediction interval when available;
- conservative mean value = max(0, lower population bound);
- score kind, score name and score unit;
- frozen integration receipt and its SHA-256.

## No global ranking

The portfolio does **not** sort information sources by effect size.

Two sources can share the same numerical unit and still be scientifically
incomparable because they arise from different generators, targets, conditioning
sets, held-out observations or experimental programmes.

In particular:

```text
v0.6a accessibility      +0.362 nats/context
v0.7b dynamic occupancy  +7.091 nats/context
```

does not mean dynamic occupancy is approximately twenty times more important.
The values live in different frozen experimental worlds.

The portfolio therefore sets:

```text
cross_programme_numeric_ranking_authorized = false
same_score_unit_implies_comparability = false
```

## Parallel R5b family

Activity and latent state come from the same R5b world and share the same score
currency, but their contrasts condition on one another:

```text
suitability + state
    -> + activity

suitability + activity
    -> + state
```

Neither was prospectively frozen as preceding the other.

The portfolio records them as a parallel family with:

```text
natural_order_authorized = false
combined_chain_authorized = false
additive_total_authorized = false
magnitude_ranking_authorized = false
```

This prevents the portfolio from silently manufacturing a three-level filtration.

## Downstream boundary

This artifact is a normalized evidence catalogue.

It cannot:

- promote an N2 state artifact;
- reopen the current frozen EOG mainline;
- rank spatial patches;
- select survey sites;
- authorize N4 action.

Survey-action ownership remains with ACSP.

## Build

```bash
python scripts/build_odsp_transfer_evidence_portfolio.py \
  --registry ODSP_TRANSFER_SOURCE_REGISTRY_V1.json \
  --out build/ODSP_TRANSFER_EVIDENCE_PORTFOLIO_V1.json
```

The output is deterministic and carries a canonical fingerprint.
