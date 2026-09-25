# v0.7d Equal-Dimension Static-versus-Dynamic Results

Status: **PASS**

v0.7d asked whether the v0.7 recursive colonization/extinction model still improves
late-time prediction when the memoryless occupancy comparator has exactly the same number
of free ecological parameters.

## Frozen provenance

- gate freeze commit:
  `c50e05f049da05c5b5063d5034cacfae9e8ecd98`
- gate blob:
  `131f0376a5097aa97358ff2511a63c68f2922a53`
- authorized outcome run: `36081729221`
- outcome head:
  `3a525662bdb1de68c0b3727d540f5410a46bfe64`
- qualification artifact ID: `10842770224`
- qualification artifact SHA256:
  `af3111005042859b2f08a32e09eff3355cceda6d219e176de304639222c8a74a`
- final result artifact ID: `10842252655`
- final artifact SHA256:
  `44bb5ef0214fbbdc6519a2f70d705476b3698db94994959ae59925cd530d1dd4`

Independent ZIP hashes matched the GitHub artifact digests.

## Frozen information split

Both models used the same generated realization and observation programme:

- joint occurrence generated at contexts **1-12**;
- joint occurrence fit at contexts **1-8**;
- direct OccupancyCount fit at contexts **1-4** only;
- held-out joint scoring at contexts **9-12**;
- direct occupancy exposure in held-out contexts = **zero**.

## Equal-dimension models

Dynamic:

- suitability intercept;
- initial occupancy;
- colonization;
- extinction;
- **4 ecological parameters**.

Static quadratic:

- suitability intercept;
- occupancy intercept;
- linear time slope;
- quadratic time slope;
- **4 ecological parameters**.

The static comparator is memoryless and never consumes previous occupancy.

## Qualification

Both models passed the frozen exact-JAX structural and practical gates.

For the equal-dimension static comparator:

- exact-JAX rank = **4/4**;
- rank without each target = **3**;
- condition number = **16.799**;
- relative minimum singular value = **0.05953**.

Target-SD proxies:

- alpha = **0.06485**;
- occupancy intercept = **0.11060**;
- linear time slope = **0.21229**;
- quadratic time slope = **0.22263**.

All were below the frozen practical threshold of 0.25.

## Replicated late-time comparison

Across **16 fresh paired replicates / 32 fits**:

- Dynamic > equal-dimension Static: **16/16 = 1.00**;
- frozen requirement: **>= 14/16 = 0.875**;
- mean Dynamic-minus-Static held-out gain:
  **+14.1443 nats/context**;
- frozen requirement: **>= +0.50 nats/context**;
- minimum replicate gain:
  **+3.1250 nats/context**;
- total divergences: **0**.

All **9/9 frozen checks passed**.

## Interpretation

v0.7d removes the remaining simple complexity explanation for v0.7c:

> Under the frozen marginal dynamic world and the same observation programme, recursive
> occupancy dynamics predict later occurrence better than a memoryless quadratic occupancy
> trend even when both models have exactly the same number of free ecological parameters.

The advantage therefore cannot be explained simply by the dynamic model having one extra
parameter, nor by the static comparator being structurally or practically unidentified.

Together, v0.7a-v0.7d now support a sharper sequence:

1. repeated occurrence can leave occupancy dynamics underidentified;
2. limited process-specific occupancy calibration anchors the missing scale;
3. the dynamic parameters then recover and transfer beyond the calibration window;
4. recursive dynamics outperform both a lower-dimensional linear static occupancy model
   and an equal-dimensional quadratic static occupancy model.

## Boundary

This is a semi-synthetic **dynamic-resolution value** result.

It does not establish:

- universal superiority of dynamic occupancy models;
- realized binary occupancy histories;
- directly observed colonization/extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.
