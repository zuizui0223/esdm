#!/usr/bin/env python3
"""Exact response-free multi-region occupancy moment identification certificate.

No wildlife data, models, simulations, or stochastic fitting are used here.
The regional latent gate R is shared across two sites, and each site's
occupancy Z_i is independent conditional on R. Site occasions are independent
conditional on Z_i. The camera only informs d=availability*registration.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path


def valid_probability(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('probability must be numeric')
    v = float(value)
    if not math.isfinite(v) or not 0 < v < 1:
        raise ValueError('probabilities must be finite strictly between 0 and 1')
    return v


def moments(rho:float, psi:float, availability:float, registration:float) ->dict:
    rho,psi,a,p=map(valid_probability,(rho,psi,availability,registration))
    d=a*p
    return {'one_detection':rho*psi*d,
            'same_site_two_visits':rho*psi*d*d,
            'cross_site_one_visit_each':rho*psi*psi*d*d,
            'effective_detection':d}


def invert_moments(one:float, same:float, cross:float)->dict:
    values=(one,same,cross)
    if any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or x<=0 for x in values):
        raise ValueError('strictly positive finite population moments required')
    d = same/one
    psi = cross/same
    rho = one*one/cross
    if not all(0<v<=1 for v in (d,psi,rho)):
        raise ValueError('moments outside this homogeneous shared-region model')
    return {'rho':rho,'psi':psi,'effective_detection':d,
            'availability_and_registration_separated':False}


def anchored_recovery(one:float,same:float,cross:float,reference_registration:float)->dict:
    registration=valid_probability(reference_registration)
    inferred=invert_moments(one,same,cross)
    d=inferred['effective_detection']
    a=d/registration
    if not 0<a<=1:
        raise ValueError('reference registration incompatible with effective detection')
    return inferred | {'availability':a,'registration':registration,
                       'availability_and_registration_separated':True}


def joint_two_site_two_visit_probability(rho:float,psi:float,a:float,p:float,history)->float:
    """All 16 four-bit detection histories, marginalizing a shared regional R.

    Ordering: site 1 visit 1, site 1 visit 2, site 2 visit 1, site 2 visit 2.
    """
    rho,psi,a,p=map(valid_probability,(rho,psi,a,p))
    if len(history)!=4 or any(x not in (0,1) for x in history):
        raise ValueError('history must be four binary observations')
    d=a*p
    likelihood=0.
    for region in (0,1):
        pr_region=rho if region else 1-rho
        possible_sites=(0,1) if region else (0,)
        for z1,z2 in product(possible_sites,repeat=2):
            if region:
                pr_occupancy=(psi if z1 else 1-psi)*(psi if z2 else 1-psi)
            else:
                pr_occupancy=1.
            emission=1.
            for site_z,ys in ((z1,history[:2]),(z2,history[2:])):
                if site_z:
                    emission*=math.prod(d if y else 1-d for y in ys)
                elif any(ys):
                    emission=0.;break
            likelihood+=pr_region*pr_occupancy*emission
    return likelihood


def all_joint_histories(rho:float,psi:float,a:float,p:float)->tuple[float,...]:
    return tuple(joint_two_site_two_visit_probability(rho,psi,a,p,history)
                 for history in product((0,1),repeat=4))


def exact_rational_rank(matrix)->int:
    """Exact, dependency-free rational row-reduction for small exponent matrices."""
    if not matrix:
        return 0
    array=[[Fraction(v) for v in row] for row in matrix]
    cols=len(array[0])
    if not cols or any(len(row)!=cols for row in array):
        raise ValueError('matrix must have nonempty equal-length rows')
    rank=0
    for c in range(cols):
        pivot=next((i for i in range(rank,len(array)) if array[i][c]),None)
        if pivot is None:continue
        array[rank],array[pivot]=array[pivot],array[rank]
        factor=array[rank][c]
        array[rank]=[v/factor for v in array[rank]]
        for i in range(len(array)):
            if i==rank:continue
            factor=array[i][c]
            array[i]=[v-factor*w for v,w in zip(array[i],array[rank])]
        rank+=1
        if rank==len(array):break
    return rank


# Exponents of rho, psi, a, p in each exact moment on the log scale:
# P(Y_i,t=1), P(Y_i,t=Y_i,u=1), P(Y_i,t=Y_j,t=1).
EXACT_LOG_MOMENT_JACOBIAN=((1,1,1,1),(1,1,2,2),(1,2,2,2))
REFERENCE_REGISTRATION_ANCHOR=(0,0,0,1)


def report()->dict:
    # Cases A and B differ in availability and device registration, not their
    # effective product. C has same single-site q,d as A but a different
    # shared-region probability, which changes across-site dependence.
    A=(0.60,0.80,0.50,0.60)
    B=(0.60,0.80,0.75,0.40)
    C=(0.80,0.60,0.50,0.60)
    am=moments(*A)
    bm=moments(*B)
    cm=moments(*C)
    ap=all_joint_histories(*A)
    bp=all_joint_histories(*B)
    cp=all_joint_histories(*C)
    recovered=invert_moments(am['one_detection'],am['same_site_two_visits'],am['cross_site_one_visit_each'])
    anchored=anchored_recovery(am['one_detection'],am['same_site_two_visits'],am['cross_site_one_visit_each'],A[3])
    ranks={'one_site_two_revisits':exact_rational_rank(EXACT_LOG_MOMENT_JACOBIAN[:2]),
           'two_sites_two_visits':exact_rational_rank(EXACT_LOG_MOMENT_JACOBIAN),
           'two_sites_two_visits_plus_independent_registration':exact_rational_rank(EXACT_LOG_MOMENT_JACOBIAN+(REFERENCE_REGISTRATION_ANCHOR,))}
    expected={'rho':A[0],'psi':A[1],'effective_detection':A[2]*A[3]}
    scalar_ok=all(abs(recovered[k]-v)<1e-12 for k,v in expected.items())
    anchored_ok=all(abs(anchored[k]-v)<1e-12 for k,v in {'rho':A[0], 'psi':A[1], 'availability':A[2], 'registration':A[3]}.items())
    if not (scalar_ok and anchored_ok and ranks=={'one_site_two_revisits':2,'two_sites_two_visits':3,'two_sites_two_visits_plus_independent_registration':4}):
        raise AssertionError('Exact moment recovery or structural rank check failed')
    return {
        'schema_version':1,
        'date':'2026-11-18',
        'status':'SHARED_REGION_TWO_SITE_TWO_VISIT_EXACT_MOMENT_IDENTIFICATION',
        'scope':'response_free_homogeneous_closed_hierarchical_submodel_not_an_empirical_fit',
        'equations':{
            'mean_one_visit':'m1 = rho*psi*a*p',
            'same_site_two_visits':'m_same = rho*psi*(a*p)^2',
            'cross_site_one_visit_each':'m_cross = rho*(psi^2)*(a*p)^2',
            'rho':'m1^2/m_cross',
            'psi':'m_cross/m_same',
            'effective_detection':'m_same/m1',
            'availability_given_reference_p':'(m_same/m1)/p_reference'},
        'examples':{'A':dict(zip(('rho','psi','a','p'),A)),
                    'B_same_full_camera_distribution':dict(zip(('rho','psi','a','p'),B)),
                    'C_same_one_site_composites':dict(zip(('rho','psi','a','p'),C))},
        'example_moments_A':am,
        'identification_recovered':recovered,
        'idealized_reference_anchored_recovery':anchored,
        'structural_log_jacobian_ranks':ranks,
        'two_site_four_bit_history_normalizes':abs(sum(ap)-1)<1e-12,
        'A_vs_B_all_16_histories_max_abs_diff':max(abs(a-b) for a,b in zip(ap,bp)),
        'A_vs_C_two_site_histories_max_abs_diff':max(abs(a-b) for a,b in zip(ap,cp)),
        'C_same_single_site_q_and_d_as_A':abs(A[0]*A[1]-C[0]*C[1])<1e-12 and abs(am['effective_detection']-cm['effective_detection'])<1e-12,
        'assertions':{'rho_psi_effective_d_identified_in_this_submodel':scalar_ok,
                      'availability_and_registration_remain_confounded_without_reference':True,
                      'independent_p_reference_can_identify_a_given_valid_reference':anchored_ok,
                      'no_empirical_biology_opened':True,
                      'does_not_qualify_E5_G4':True,
                      'previous_empirical_results_unchanged':True},
        'limits':{'requires_multiple_independent_replicate_regions_or_species_with_shared_parameterization':True,
                  'requires_two_or_more_sites_per_region_and_two_or_more_conditionally_independent_occasions':True,
                  'assumes_shared_region_availability_R_across_sites':True,
                  'assumes_homogeneous_psi_and_d_across_replicates':True,
                  'assumes_independent_local_occupancy_given_regional_state':True,
                  'assumes_conditional_independence_of_camera_occasion_records_and_no_false_positives':True,
                  'no_population_parameter_precision_from_only_one_empirical_region':True,
                  'autocorrelated_activity_breaks_simple_moment_formula':True,
                  'independent_reference_passage_not_measured_by_this_proof':True,
                  'not_novel_occupancy_theory_or_a_new_esdm_generation':True}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    out=report()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],
                      'rank':out['structural_log_jacobian_ranks'],
                      'exact_16_history_difference':out['A_vs_B_all_16_histories_max_abs_diff']}))

if __name__=='__main__': main()
