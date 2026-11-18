#!/usr/bin/env python3
"""Exact observational-equivalence audit for a minimal four-gate camera model.

No camera/wildlife observations, random simulation, optimisation, or empirical fit.
This exact one-unit submodel is NOT a general theorem about all multi-scale
occupancy designs: independent spatial replication, validated source pools,
multiple devices and auxiliary signals can change structural identification.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import itertools
import json
import math
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Gates:
    regional_pool: float
    site_occupancy: float
    per_occasion_availability: float
    camera_registration: float

    def __post_init__(self) -> None:
        for name, value in vars_as_dict(self).items():
            if type(value) not in (float, int) or not math.isfinite(value) or not 0 < value < 1:
                raise ValueError(f'{name} must be a finite interior probability (0,1)')

    @property
    def occupancy_composite(self) -> float:
        return self.regional_pool * self.site_occupancy

    @property
    def observation_composite(self) -> float:
        return self.per_occasion_availability * self.camera_registration


def vars_as_dict(x: Gates) -> dict[str, float]:
    return {
        'regional_pool': x.regional_pool,
        'site_occupancy': x.site_occupancy,
        'per_occasion_availability': x.per_occasion_availability,
        'camera_registration': x.camera_registration,
    }


def history_probability(gates: Gates, binary_history: Iterable[int]) -> float:
    """Marginalise shared binary pool & occupancy; conditional occasions iid.

    R ~ Bernoulli(rho); Z | R ~ Bernoulli(R psi).
    A_t | Z ~ Bernoulli(Z a); Y_t | A_t ~ Bernoulli(A_t p).
    A_t and Y_t are conditionally independent between visits given Z.
    The observation process is closed, no false positives, no missing effort.
    """
    h = tuple(binary_history)
    if not h or any(type(y) is not int or y not in (0, 1) for y in h):
        raise ValueError('nonempty history of 0/1 integers required')
    q, d = gates.occupancy_composite, gates.observation_composite
    detected = sum(h)
    if detected == 0:
        return 1 - q + q * (1 - d) ** len(h)
    return q * (d ** detected) * ((1 - d) ** (len(h) - detected))


def history_distribution(gates: Gates, occasions: int) -> dict[str, float]:
    if type(occasions) is not int or not 1 <= occasions <= 15:
        raise ValueError('occasions must be an integer from 1 through 15')
    out = {
        ''.join(map(str, h)): history_probability(gates, h)
        for h in itertools.product((0, 1), repeat=occasions)
    }
    if not math.isclose(sum(out.values()), 1, rel_tol=0, abs_tol=1e-12):
        raise AssertionError('joint detection histories must sum to one')
    return out


def two_visit_composites(*, p_11: float, p_10: float) -> tuple[float, float]:
    """Identification of (q,d) from population probabilities, not one history.

    p11 = q*d*d; p10 = q*d*(1-d), with q in (0,1), d in (0,1).
    Thus d=p11/(p11+p10), q=(p11+p10)/d.
    """
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in (p_11, p_10)):
        raise ValueError('strictly positive, finite P(11) and P(10) required')
    if p_11 + p_10 >= 1:
        raise ValueError('P(11)+P(10) must be less than 1')
    d = p_11 / (p_11 + p_10)
    q = (p_11 + p_10) / d
    if not 0 < d < 1 or not 0 < q < 1:
        raise ValueError('inferred q or d outside (0,1)')
    return q, d


def recover_given_anchors(*, q: float, d: float,
                          known_pool: float | None = None,
                          known_registration: float | None = None) -> dict[str, float | None]:
    """Only separately measured anchors permit the corresponding split.

    These are idealized exact anchors. Real imperfect reference cameras,
    uncertain regional ranges or incompatible camera zones do not pass.
    """
    for name, v in (('q', q), ('d', d)):
        if type(v) not in (float, int) or not math.isfinite(v) or not 0 < v < 1:
            raise ValueError(f'{name} must be a finite interior probability')
    psi, avail = None, None
    if known_pool is not None:
        if type(known_pool) not in (int, float) or not math.isfinite(known_pool) or not q <= known_pool <= 1:
            raise ValueError('known regional pool probability must be in [q,1]')
        psi = q / known_pool
    if known_registration is not None:
        if (type(known_registration) not in (int, float)
                or not math.isfinite(known_registration) or not d <= known_registration <= 1):
            raise ValueError('known registration probability must be in [d,1]')
        avail = d / known_registration
    return {
        'regional_pool': float(known_pool) if known_pool is not None else None,
        'site_occupancy': psi,
        'per_occasion_availability': avail,
        'camera_registration': float(known_registration) if known_registration is not None else None,
        'identified_occupancy_product_q': q,
        'identified_availability_registration_product_d': d,
    }


def identify_ladder() -> dict[str, dict]:
    return {
        'one_visit_no_anchors': {
            'identified': ['q*d = rho*psi*a*p'],
            'not_identified': ['rho', 'psi', 'a', 'p', 'q', 'd'],
            'requirements': ['no false positives', 'known exposure'],
        },
        'closed_repeated_visits_no_anchors': {
            'identified': ['q = rho*psi', 'd = a*p'],
            'not_identified': ['rho', 'psi', 'a', 'p'],
            'requirements': ['at least two visits with population replication',
                             'closure and conditional occasion independence',
                             'non-degenerate detection', 'known active survey effort'],
        },
        'closed_repeats_plus_independent_registration_reference': {
            'identified': ['q = rho*psi', 'a', 'p'],
            'not_identified': ['rho', 'psi'],
            'requirements': ['matched independently observed passage denominator',
                             'verified camera/reference overlapping exposure and zone',
                             'calibrated or qualified reference sensitivity'],
        },
        'closed_repeats_plus_pool_and_registration_anchors': {
            'identified': ['rho', 'psi', 'a', 'p'],
            'not_identified': [],
            'requirements': ['independent measured pool probability or fixed verified eligibility',
                             'independently calibrated camera registration',
                             'closed conditionally independent repeated visits'],
        },
    }


def certificate() -> dict:
    # Distinct biological and sensor explanations have exactly the same
    # likelihood for every possible binary encounter history at any K.
    case_a = Gates(0.60, 0.80, 0.50, 0.60)
    case_b = Gates(0.80, 0.60, 0.75, 0.40)
    max_differences = {}
    for visits in (1, 2, 3, 6, 10):
        aa = history_distribution(case_a, visits)
        bb = history_distribution(case_b, visits)
        max_differences[str(visits)] = max(abs(aa[k] - bb[k]) for k in aa)
    p2 = history_distribution(case_a, 2)
    q, d = two_visit_composites(p_11=p2['11'], p_10=p2['10'])
    anchored = recover_given_anchors(q=q, d=d,
                                    known_pool=case_a.regional_pool,
                                    known_registration=case_a.camera_registration)
    tol = 1e-12
    return {
        'schema_version': 1,
        'status': 'EXACT_OBSERVATIONAL_EQUIVALENCE_MINIMAL_SITE_MODEL',
        'scope': 'One region-species-by-site observational unit with shared pool and site states, independent occasion-level availability; no false positives',
        'not_a_universal_multiscale_occupancy_nonidentifiability_claim': True,
        'data_boundary': {
            'wildlife_rows_opened': False,
            'prior_empirical_fits_changed': False,
            'new_simulated_validation_generation': False,
            'independent_calibration_obtained': False,
        },
        'distinct_parameter_vectors': {'A': vars_as_dict(case_a), 'B': vars_as_dict(case_b)},
        'equal_composite_probabilities': {'q': q, 'd': d, 'single_visit_positive': q*d},
        'exact_two_visit_joint_probabilities_A': p2,
        'max_likelihood_probability_discrepancy_by_number_of_visits': max_differences,
        'recovered_with_both_exact_independent_anchors_A': anchored,
        'identification_ladder': identify_ladder(),
        'decision': {
            'observational_equivalence_pass': all(v < tol for v in max_differences.values()),
            'two_visit_composites_pass': abs(q-case_a.occupancy_composite) < tol and abs(d-case_a.observation_composite) < tol,
            'idealized_two_anchor_recovery_pass': all(abs(anchored[k] - v) < tol for k, v in vars_as_dict(case_a).items()),
            'eSDM_superiority_claim_authorized': False,
            'E5_G4_qualified_by_this_proof': False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = certificate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if not all(result['decision'][k] for k in (
        'observational_equivalence_pass', 'two_visit_composites_pass', 'idealized_two_anchor_recovery_pass'
    )):
        raise SystemExit(1)
    print(json.dumps({'status': result['status'], 'decision': result['decision']}, sort_keys=True))


if __name__ == '__main__':
    main()
