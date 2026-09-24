# v0.5b Hidden Common Driver Results

Status: **FAIL**

v0.5b deliberately tested the v0.5a partner-latent model under omitted common-cause
misspecification.

The true directed partner coefficient was exactly zero. Source and focal instead shared
an unmeasured environmental driver that was partially correlated with the measured
source-specific driver.

## Frozen provenance

- outcome run: `35971827831`
- outcome head: `e9d25912b7662d397c15b10f1851e1cc0108d8ea`
- gate freeze commit: `06c6943de8cfa5a2edb8b9ecd7bde05ebb661fa5`
- gate blob expected/observed:
  `ba1ff83cabf402b98ea4fd7a3e097adcb06b5fd6`
- final artifact ID: `10796695978`
- artifact name: `v05b-result-35971827831`
- artifact digest / independently verified ZIP SHA256:
  `b49571aa68d83d964428c2cdd6e415d2ddd9a46a7b53de296604614655dc3788`

All 16 replicate jobs completed successfully. The aggregate failure is scientific:
`infrastructure_block = null`.

## False directed coefficient

Truth:

- `beta_partner = 0`.

Observed across 16 fresh replicates:

- mean fitted beta = **+0.62677**
- zero coverage = **0/16 = 0.00**
- nonzero 90% interval rate = **16/16 = 1.00**
- every interval was entirely **positive**

The frozen robustness thresholds were:

- |mean beta| <= 0.10
- zero coverage >= 0.75
- nonzero interval rate <= 0.25

All three failed decisively.

The omitted shared cause was therefore absorbed by the directed partner coefficient.

## Predictive warning signal

The false-positive coefficient did **not** translate into consistent held-out improvement.

Observed:

- Full > partner knockout in **6/16 = 0.375**
- material gain (>0.005) in **6/16 = 0.375**
- mean Full-minus-knockout held-out gain = **−0.26237**

The frozen mean-gain refusal criterion passed because the Full model was worse on average.

This produces an important failure signature:

> the posterior coefficient can be confidently nonzero while held-out predictive evidence
> does not support the same process.

## Sampling

- replicates: 16
- fits: 32
- total divergences: **0**

The failure is not a sampler pathology.

## Interpretation across v0.5a and v0.5b

v0.5a showed that a measured shared environmental response can be modeled without
automatically creating a false partner effect.

v0.5b shows the boundary:

- measured shared cause: guarded successfully;
- omitted shared cause: catastrophic parameter false positive.

Therefore the partner-latent distribution coefficient must **not** by itself be promoted
to a realized or causal interaction claim.

The fact that held-out prediction is worse on average is useful but insufficient as the
sole safeguard: 6/16 hidden-driver replicates still produced material positive predictive
gain.

## Consequence for v0.5c

The next layer should not retune the partner coefficient.

It should add an **independent interaction-event endpoint** and make claim promotion
depend on evidence from that endpoint.

The intended semantics are:

- distributional partner effect -> at most predictive dependence;
- directly observed interaction event -> realized-interaction evidence;
- causal tier remains unavailable without intervention or stronger causal design.

This preserves the negative result instead of hiding it.
