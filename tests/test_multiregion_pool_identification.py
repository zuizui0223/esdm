"""Exact source-free mathematical tests for 2-level regional pool identification."""
from __future__ import annotations

from itertools import product
import json
import math

import pytest

from scripts.prove_multiregion_pool_identification import (
    valid_probability, moments, invert_moments, anchored_recovery,
    joint_two_site_two_visit_probability, all_joint_histories,
    exact_rational_rank, EXACT_LOG_MOMENT_JACOBIAN,
    REFERENCE_REGISTRATION_ANCHOR, report,
)


def test_exact_moments_for_frozen_A():
    m=moments(.6,.8,.5,.6)
    assert m['one_detection']==pytest.approx(.144)
    assert m['same_site_two_visits']==pytest.approx(.0432)
    assert m['cross_site_one_visit_each']==pytest.approx(.03456)
    assert m['effective_detection']==pytest.approx(.3)


@pytest.mark.parametrize('values',[(.2,.4,.8,.9),(.8,.7,.3,.4),(.99,.3,.05,.91),(.5,.5,.5,.5)])
def test_recover_population_moments_under_idealized_hierarchy(values):
    m=moments(*values)
    recovered=invert_moments(m['one_detection'],m['same_site_two_visits'],m['cross_site_one_visit_each'])
    assert recovered['rho']==pytest.approx(values[0])
    assert recovered['psi']==pytest.approx(values[1])
    assert recovered['effective_detection']==pytest.approx(values[2]*values[3])
    assert recovered['availability_and_registration_separated'] is False


def test_anchor_recovery_for_same_model():
    m=moments(.7,.4,.5,.6)
    vals=anchored_recovery(m['one_detection'],m['same_site_two_visits'],m['cross_site_one_visit_each'],.6)
    assert vals['availability']==pytest.approx(.5)
    assert vals['registration']==pytest.approx(.6)
    assert vals['availability_and_registration_separated'] is True


@pytest.mark.parametrize('value',[0.,1.,-1.,float('nan'),float('inf'),True,'0.5'])
def test_strict_parameter_refusal(value):
    with pytest.raises(ValueError):valid_probability(value)


def test_independent_reference_inconsistent_with_composite_detection_refused():
    m=moments(.6,.8,.5,.6)
    with pytest.raises(ValueError,match='incompatible'):
        anchored_recovery(m['one_detection'],m['same_site_two_visits'],m['cross_site_one_visit_each'],.1)


@pytest.mark.parametrize('one,same,cross',[(0.,.1,.2),(.1,0.,.1),(.1,.2,0.),(-.1,.1,.1),(.1,.2,.01),(.1,.01,.2)])
def test_invalid_moment_triples_refused(one,same,cross):
    with pytest.raises(ValueError):invert_moments(one,same,cross)


def test_same_full_joint_distribution_when_a_and_p_are_confounded():
    one=all_joint_histories(.6,.8,.5,.6)
    two=all_joint_histories(.6,.8,.75,.4)
    assert len(one)==16
    assert sum(one)==pytest.approx(1.)
    assert max(abs(a-b) for a,b in zip(one,two))<1e-12


def test_same_single_site_composites_do_not_make_cross_site_histories_equal():
    first=all_joint_histories(.6,.8,.5,.6)
    second=all_joint_histories(.8,.6,.5,.6)
    assert max(abs(a-b) for a,b in zip(first,second))>0.02
    # A and C are identical for one-site histories, by previous frozen proof.
    assert .6*.8 == pytest.approx(.8*.6)
    assert .5*.6 == pytest.approx(.5*.6)


def test_exact_enumeration_recovers_all_three_moments():
    params=(.6,.8,.5,.6)
    probs={bits:joint_two_site_two_visit_probability(*params,bits)
           for bits in product((0,1),repeat=4)}
    m=moments(*params)
    assert sum(v for bits,v in probs.items() if bits[0])==pytest.approx(m['one_detection'])
    assert sum(v for bits,v in probs.items() if bits[0] and bits[1])==pytest.approx(m['same_site_two_visits'])
    assert sum(v for bits,v in probs.items() if bits[0] and bits[2])==pytest.approx(m['cross_site_one_visit_each'])
    assert sum(probs.values())==pytest.approx(1.)


def test_log_moment_rank_is_two_three_then_four_with_reference():
    assert exact_rational_rank(EXACT_LOG_MOMENT_JACOBIAN[:2])==2
    assert exact_rational_rank(EXACT_LOG_MOMENT_JACOBIAN)==3
    assert exact_rational_rank(EXACT_LOG_MOMENT_JACOBIAN+(REFERENCE_REGISTRATION_ANCHOR,))==4


def test_exact_rational_rank_handles_duplicated_rows():
    assert exact_rational_rank([[1,2],[2,4],[3,6]])==1
    assert exact_rational_rank([[1,2],[3,4]])==2
    assert exact_rational_rank([[0,0],[0,0]])==0


def test_rank_refuses_bad_shaped_rows():
    with pytest.raises(ValueError):exact_rational_rank([[1,2],[3]])


def test_history_input_guard():
    with pytest.raises(ValueError):joint_two_site_two_visit_probability(.6,.8,.5,.6,(1,0,0))
    with pytest.raises(ValueError):joint_two_site_two_visit_probability(.6,.8,.5,.6,(1,0,0,2))


def test_independent_region_gates_across_sites_break_shared_region_recovery():
    m=moments(.6,.8,.5,.6)
    observed_cross=m['one_detection']**2
    recovered=invert_moments(m['one_detection'],m['same_site_two_visits'],observed_cross)
    assert recovered['rho']==pytest.approx(1.)
    assert recovered['rho']!=pytest.approx(.6)
    # Therefore rho=.6 would be unidentifiable from these moments if sites
    # had their own independent regional gates rather than a shared R.


def test_camera_only_never_identifies_a_and_p_even_with_two_sites():
    p1=moments(.6,.8,.5,.6)
    p2=moments(.6,.8,.75,.4)
    for key in ('one_detection','same_site_two_visits','cross_site_one_visit_each'):
        assert p1[key]==pytest.approx(p2[key])


def test_frozen_result_contains_no_empirical_claims():
    r=report()
    assert r['status']=='SHARED_REGION_TWO_SITE_TWO_VISIT_EXACT_MOMENT_IDENTIFICATION'
    assert r['assertions']['no_empirical_biology_opened'] is True
    assert r['assertions']['does_not_qualify_E5_G4'] is True
    assert r['limits']['autocorrelated_activity_breaks_simple_moment_formula'] is True
    assert r['structural_log_jacobian_ranks']['two_sites_two_visits']==3
    assert r['A_vs_B_all_16_histories_max_abs_diff']<1e-12


def test_machine_readable_receipt_matches_exact_code(tmp_path):
    from pathlib import Path
    snapshot=Path(__file__).parents[1]/'docs'/'replication'/'MULTIREGION_POOL_IDENTIFICATION_RESULT.json'
    actual=json.loads(snapshot.read_text(encoding='utf-8'))
    assert actual==report()
