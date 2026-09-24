# v0.6b Joint-Only Identification Audit Results

Status: **COMPLETE — Outcome B**

The frozen audit tested whether the v0.6a conclusion had been stated too strongly.

## Provenance

- outcome run: `36012218442`
- outcome head: `20fa4da582c1442d693b8dc0217fc5cad29f30ba`
- gate freeze commit: `a4cd5f2ac809fd4db65ce4418f0648a55978fd59`
- gate blob expected/observed:
  `31d121519fe018c4cc20d75bfbfadbecc932f7a7`
- artifact ID: `10813480338`
- artifact digest:
  `sha256:682edb0c534ae7418dc77a7d4586907cbbad511e1b210f8960533cfead04be17`

## Intercept-only control

The exact v0.6a product-confounding control remained correctly refused.

For both suitability and accessibility intercepts:

- full local rank = **1**;
- rank without target = **1**;
- structural status = **NotIdentified**.

Target-SD proxies:

- suitability intercept = **4228.41**;
- accessibility intercept = **10536.45**.

The hard control therefore passed.

## Structured joint-only audit

The exact v0.6a first 24 training contexts and ecological truth were retained, but
AccessibilityCount was removed. Only joint AccessiblePresenceOnly remained.

All four targets became **structurally Identified**:

- full rank = **4**;
- rank without each target = **3**;
- singular values =
  **5.39447, 3.67242, 1.78349, 0.20265**;
- relative minimum singular value = **0.03757**;
- condition number = **26.62**.

However, the frozen practical threshold was not met by three targets.

Target-SD proxies:

- suitability intercept = **0.49463** — weak;
- habitat slope = **0.11028** — passes;
- accessibility intercept = **1.47533** — weak;
- distance/accessibility slope = **0.91023** — weak.

Therefore the frozen interpretation is **Outcome B: structural but practically weak**.

## Corrected v0.6 interpretation

v0.6a established that direct accessibility information is sufficient for practical
identification, recovery, and held-out transfer.

v0.6b shows that it is **not universally necessary for mathematical/local structural
identification**. Distinct covariates and the declared nonlinear functional form can
separate the components from joint occurrence alone.

But that formal separation is not enough here for stable estimation of the full parameter
block. Direct accessibility calibration reduced target-SD proxies to 0.106–0.198 in
v0.6a and enabled successful replicated recovery.

The correct methodological distinction is therefore:

> Parametric separability is not the same as practical process information. Joint
> occurrence can carry enough shape to identify accessibility formally, while an
> independent accessibility endpoint can still be needed to make the decomposition
> estimable at useful precision.

## Boundary

The structured joint-only result is model-based local identification. It is not
independent ecological evidence that movement/accessibility caused the observed pattern.

No movement kernel, connectivity process, dynamic colonization/extinction process, or
causal movement claim is established by v0.6b.
