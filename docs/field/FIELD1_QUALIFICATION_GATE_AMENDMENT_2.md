# FIELD1 Phase-A qualification gate — Amendment 2

Status: **INFRASTRUCTURE REPLACEMENT FROZEN BEFORE ANY FIELD1 CONFIRMATORY OUTCOME**

Date frozen: 2026-09-27

## Trigger

The first authorization attempt was:

- qualification branch: `field1/qualification-v1`
- authorization commit: `a495f42f09ba6a553c76a2a787476e1620848ae9`
- workflow run: `36315550882`

The authorization-purity check passed. The precheck then failed because
`tests/test_field1_workflow.py` asserted that
`docs/field/FIELD1_RUN_AUTHORIZED` must not exist. That assertion is valid on the
implementation branch before authorization, but is mechanically incompatible with the
authorized qualification branch where the marker is intentionally present.

No FIELD1 confirmatory outcome was opened:

- replicate jobs started: **0**
- replicate jobs completed: **0**
- scientific shards produced: **0**
- scientific PASS/FAIL decision: **none**

The replicate matrix was skipped because the failure occurred in precheck.

## Frozen infrastructure repair

A replacement run is allowed with every scientific element unchanged.

The only implementation changes authorized by this amendment are:

1. the static workflow test no longer requires the authorization marker to be absent;
   marker purity remains enforced by the workflow's git-diff precheck;
2. the one-shot workflow listens to a fresh replacement branch:
   `field1/qualification-v1-r2`;
3. the replacement authorization marker must additionally declare
   `replacement_amendment: docs/field/FIELD1_QUALIFICATION_GATE_AMENDMENT_2.md`.

The replacement branch must be created from the merged repair commit on `main`.
Its authorization commit must again add exactly one file:
`docs/field/FIELD1_RUN_AUTHORIZED`.

## Scientific invariants

This replacement changes none of the following:

- M0-M4 model definitions;
- K0-K5 truth worlds or truth hyperparameters;
- fresh latent-field realization per replicate;
- K6 deterministic geometry audit;
- H1/H2 holdouts;
- edge-distance/environment/barrier covariates;
- 16 replicates per world;
- 144 expected shards;
- 704 expected fits;
- positive/null gain thresholds;
- divergence threshold;
- 300 warmup / 350 retained draws / 2 chains / target accept 0.90;
- claim-promotion rules;
- interpretation boundaries.

No post-outcome retuning is involved because no confirmatory replicate was launched.
