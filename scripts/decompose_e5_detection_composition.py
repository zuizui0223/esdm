"""A descriptive, exact observation-process decomposition; no data access or fit.

For two regimes of independently passage-referenced animal encounters,
D_r = sum_z f_r(z) * p_r(z), where f_r is a normalized passage-covariate
distribution and p_r is calibrated P(recorded|pass,z).
"""
from __future__ import annotations

from math import isfinite
from typing import Sequence


def decompose_effective_detection(
    f1: Sequence[float],
    f2: Sequence[float],
    trigger1: Sequence[float],
    trigger2: Sequence[float],
    register1: Sequence[float],
    register2: Sequence[float],
) -> dict[str, float]:
    vectors = [list(map(float, v)) for v in
               (f1, f2, trigger1, trigger2, register1, register2)]
    n = len(vectors[0])
    if n == 0 or any(len(v) != n for v in vectors):
        raise ValueError("nonempty aligned covariate cells required")
    if any(not isfinite(x) for v in vectors for x in v):
        raise ValueError("all covariate cells must be finite")
    a, b, t1, t2, q1, q2 = vectors
    if any(x < 0 for x in a + b):
        raise ValueError("passage frequencies must be nonnegative")
    if abs(sum(a) - 1.0) > 1e-10 or abs(sum(b) - 1.0) > 1e-10:
        raise ValueError("passage distributions must each sum to 1")
    if any(x < 0 or x > 1 for x in t1+t2+q1+q2):
        raise ValueError("stage probabilities must be within [0,1]")
    p1 = [x*y for x,y in zip(t1,q1)]
    p2 = [x*y for x,y in zip(t2,q2)]
    d1 = sum(x*y for x,y in zip(a,p1))
    d2 = sum(x*y for x,y in zip(b,p2))
    mechanism = .5*sum((y-x)*(u+v) for x,y,u,v in zip(p1,p2,a,b))
    composition = .5*sum((v-u)*(x+y) for u,v,x,y in zip(a,b,p1,p2))
    return {
        "effective_detection_1": d1,
        "effective_detection_2": d2,
        "difference": d2-d1,
        "conditional_process_component": mechanism,
        "passage_composition_component": composition,
    }
