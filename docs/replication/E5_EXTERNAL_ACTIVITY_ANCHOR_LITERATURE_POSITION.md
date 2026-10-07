# E5 external-activity-anchor literature position

Frozen: 2026-10-08, before completion of empirical one-shot run 37643401531.

This note fixes the literature framing only. It does not change the frozen empirical
model, transfer design, threshold, metric, or claim boundary.

## What is already established

Camera traps and telemetry measure animal activity from different sampling perspectives.
Direct comparisons have asked whether camera-derived and telemetry-derived activity or
space-use patterns agree within the same system. Relevant examples include:

- Wolfson et al. 2023, Ecosphere, doi:10.1002/ecs2.4728 — seasonal wild-pig activity
  from GPS telemetry and camera traps in Florida and California.
- Bassing et al. 2023, Ecological Applications, doi:10.1002/eap.2745 — contemporaneous
  GPS-collar and camera-trap inference across seven species.
- Iannino et al. 2025, Wildlife Biology, doi:10.1002/wlb3.01263 — camera-trap diel
  activity compared with collar-mounted activity sensors for Eurasian lynx.

Camera-trap observation is also known not to be a neutral recording of latent activity.
Mechanisms include diel variation in sensor sensitivity, animal speed, microsite use,
trail placement, camera model/settings, environmental conditions and missed triggers.
Relevant examples include:

- Rowcliffe et al. 2014, Methods in Ecology and Evolution,
  doi:10.1111/2041-210X.12278.
- Hofmeester et al. 2019, Ecology and Evolution, doi:10.1002/ece3.4878.
- Kolowski & Forrester 2017, PLOS ONE, doi:10.1371/journal.pone.0186679.
- Hofmeester et al. 2021 / empirical dense-array work on camera detection process,
  doi:10.1186/s40462-021-00277-3.
- Peral et al. 2022, Ecology and Evolution, doi:10.1002/ece3.9408.

Thus neither of the following is a new claim:

1. camera and telemetry activity curves can differ; or
2. camera observation can be biased by detection and placement processes.

## Gap tested by the frozen route

The present route asks a different question:

> If telemetry independently anchors relative ecological activity A(t), is the residual
> relative diel camera observation distortion D(t) reproducible enough to transfer
> between geographic regimes?

The frozen estimand is therefore not camera detection probability. It is the normalized
shape D(t) satisfying

    C(t) proportional to A(t) * D(t)

within a geography-season, where C(t) is the camera time-density and A(t) is the
telemetry-derived activity shape.

The empirical test is deliberately out-of-geography:

- estimate D(t) in Florida, apply it to California telemetry activity, predict California
  camera time-density;
- estimate D(t) in California, apply it to Florida telemetry activity, predict Florida
  camera time-density;
- repeat symmetrically for spring, summer, fall and winter.

The primary comparison is the frozen gain in held-out camera-density overlap relative
to a GPS-only activity baseline.

## Scoped novelty claim before outcome

In a targeted search of the camera-trap / telemetry activity literature available by
2026-10-08, we found studies of within-system method agreement and studies of factors
that bias camera detection, but did not find a direct test of whether a telemetry-anchored
*diel observation-distortion shape* learned in one geography transfers to another.

Accordingly, the strongest defensible novelty statement is:

> The route tests geographic portability of the observation process itself, rather than
> merely asking whether two observation methods agree.

This is a scoped literature-search conclusion, not a proof that no prior study exists.

## Result-independent interpretation

If the frozen transfer result is SUPPORTED:
- relative camera observation distortion contains a geographically portable component;
- camera-vs-telemetry mismatch is not purely site-specific noise;
- a learned observation correction can improve out-of-geography diel prediction under
  the tested design.

If UNRESOLVED:
- the data do not establish portable distortion at the frozen precision;
- this does not imply zero camera bias.

If CONTRADICTED:
- a distortion learned in one geography actively worsens held-out prediction on average;
- this supports context dependence of the observation process rather than a portable
  correction.

None of the three outcomes permits a claim about absolute detection probability,
abundance, causal sensor mechanism, or a pass of the original E5 direct-detection G4.
