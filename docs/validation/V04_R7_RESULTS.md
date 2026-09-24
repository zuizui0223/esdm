# v0.4-R7 Budget-Matched Calibration Results

Status: **FAIL**

R7 prospectively compared the promoted direct conditional state-composition calibration
against an equal-expected-label additional StateAnnotatedCount calibration.

The two arms used identical base observations in every replicate and each added exactly
432 expected state labels under the frozen generating truth.

## Frozen provenance

- outcome run: `35948454316`
- outcome head: `cf07394195ab8055b3ced0c231b8aee68eaa7810`
- gate freeze commit: `2c6c1473cbe7a571ee8972476225574a7906a1cb`
- gate blob expected/observed:
  `7c3261211cc8b1eb51e50f912457dd54dd8fdb33`
- final artifact ID: `10788960354`
- artifact name: `v04-r7-budget-matched-35948454316`
- artifact digest / independently verified ZIP SHA256:
  `0f822e766962226738ac962b22ad1fc86a893bafbfc8834ab6fe7ada15c91e33`

All 16 replicate shards completed successfully. The aggregate job returned failure
because the frozen scientific gate failed, not because of infrastructure:
`infrastructure_block = null`.

## Budget and pairing checks

All budget/pairing requirements passed:

- paired base observations identical in **16/16** replicates;
- Direct expected labels = **432.0**;
- Passive expected labels = **432.0**;
- mean realized Direct labels = **433.5**;
- mean realized Passive labels = **425.875**;
- 32 total fits;
- 0 divergences.

Thus the comparison is not explained by unequal expected label count or different base
training/held-out realizations.

## Held-out prediction

Frozen requirement:

- Direct > Passive in >= 75% of replicates;
- mean Direct-minus-Passive held-out gain >= 0.005.

Observed:

- Direct > Passive in **3/16 = 0.1875**;
- mean held-out gain = **−0.003016**.

So the Passive arm was better on average in east-heldout StateAnnotatedCount prediction.

The largest conceptual takeaway is that the direct calibration channel is **not**
predictively superior to an equal expected number of extra passive state annotations
under this structured world.

## State-slope recovery

Frozen requirement:

- Direct state-slope MAE better in >= 75% of replicates;
- mean state-error gain > 0.

Observed:

- Direct had lower four-slope MAE in **9/16 = 0.5625**;
- mean state-error gain = **+0.03734**.

The average direction favored Direct for state-parameter recovery, but the replicate-level
advantage was too inconsistent to pass the frozen gate.

This split is informative:

- Direct calibration can sharpen state-slope estimation on average;
- Passive annotation can still produce equal or better held-out prediction because it
  carries information through the joint intensity × activity × state observation channel.

## Interpretation

R7 rejects the strongest form of the information-type hypothesis.

The R5/R6 positive results should **not** be summarized as:

> Direct conditional state calibration is intrinsically more informative than the same
> number of passive state annotations.

Instead, the supported sequence is narrower:

1. without enough state-resolving information, hard state slopes remain practically weak;
2. adding direct state-composition calibration is one successful way to cross that
   information threshold;
3. however, when an equal expected number of additional passive state annotations is
   supplied, Direct does not dominate held-out prediction and does not robustly dominate
   state-slope recovery.

Therefore the decisive distinction is not simply **direct vs passive**. The next useful
question is which **mixture of observation channels** is most efficient for a declared
scientific target.

## Claim boundary

R7 does not invalidate the R5/R6 promotion result.

R5/R6 established that the promoted observation contract is identifiable, recoverable,
and conditionally predictively useful. R7 only narrows the interpretation of why the
direct calibration channel worked.

R7 supports no universal ranking of calibration types and provides no field-cost
comparison.
