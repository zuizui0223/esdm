# FIELD1 Phase-A terminal result

Status: **FAIL (terminal)**  
Date: 2026-09-27  
Workflow run: `36316137677`

The replacement one-shot completed all **144/144** confirmatory replicates and all
**704** frozen model fits. There were no failed replicate jobs.

## What passed

**FIELD_PRESENT = true.**

The distance-only spatial field (M1) cleared its positive and negative controls:

- K1, M1 - M0 on H1: positive-gain rate **0.75**, mean gain **4.7197**;
- K0, M1 - M0 on H1: material-gain rate **0.0625**, mean gain **-0.0755**.

Thus FIELD1 supports the bounded statement that adding one coherent distance-structured
residual field can improve held-out mapping beyond the environment-only SDM.

## What failed

**ENV_DEPENDENCE_SUPPORTED = false.**

Although K2 M2-M1 passed its intended positive comparison, M2 false-promoted in K0 and
K1, and the K5 mean/covariance factorial did not track covariance truth cleanly.

**BARRIER_DEPENDENCE_SUPPORTED = false.**

The frozen geometry audits passed, including training-side barrier learning and transfer
to a separate held-out barrier, but predictive gains did not meet the frozen positive
frequency rules. In K3, M3-M1 on H2 had positive-gain rate **0.4375** and mean gain
**-0.0149**.

**FULL_MAP_STRUCTURE_SUPPORTED = false.**

The full distance+environment+barrier field did not clear both single-axis comparisons
in K4.

## Sampling guardrail

The run produced **360 divergences across 704 fits**, or **0.5114 per fit**, exceeding
the frozen maximum of **0.10**. This independently makes the overall Phase-A gate FAIL.

## Terminal rule

This result is not eligible for threshold retuning, geometry retuning, or a same-program
rerun. No FIELD1b/FIELD2 generation may be created solely to rescue the failed
environment/barrier claims.

The exact aggregate is preserved by:

- artifact ID: `10932280009`
- aggregate JSON SHA-256:
  `56da89919350f9e3c5d293f759654068180a648d03e553b3d08aff441f29cef2`

The first authorization attempt remains separately frozen as
`FIELD1_FIRST_AUTHORIZATION_STOP.json` with no scientific outcome opened.
