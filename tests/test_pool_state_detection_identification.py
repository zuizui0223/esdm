"""Exact math and fail-closed evidence tests; no real animal-response loading."""
import itertools
import math
import pytest

from scripts.audit_pool_state_detection_identification import (
    Gates, certificate, history_probability, history_distribution,
    two_visit_composites, recover_given_anchors, identify_ladder,
)


def test_one_visit_is_only_product():
    a = Gates(.6, .8, .5, .6)
    assert history_probability(a, [1]) == pytest.approx(.144)
    assert history_probability(a, [0]) == pytest.approx(.856)


def test_exact_equivalent_likelihoods_at_any_visits():
    a = Gates(.6, .8, .5, .6)
    b = Gates(.8, .6, .75, .4)
    assert a != b
    assert a.occupancy_composite == pytest.approx(b.occupancy_composite)
    assert a.observation_composite == pytest.approx(b.observation_composite)
    for k in (1, 2, 3, 6, 10):
        for y in itertools.product((0, 1), repeat=k):
            assert history_probability(a, y) == pytest.approx(history_probability(b, y), abs=1e-13)


def test_two_visits_joint_probabilities_and_normalization():
    a = Gates(.6, .8, .5, .6)
    result = history_distribution(a, 2)
    assert result == pytest.approx({'00': .7552, '01': .1008, '10': .1008, '11': .0432})
    assert sum(result.values()) == pytest.approx(1)


def test_two_visit_composites_recover_q_and_d_not_separate_gates():
    d = history_distribution(Gates(.6, .8, .5, .6), 2)
    q, p = two_visit_composites(p_11=d['11'], p_10=d['10'])
    assert q == pytest.approx(.48)
    assert p == pytest.approx(.30)
    assert recover_given_anchors(q=q, d=p)['site_occupancy'] is None
    assert recover_given_anchors(q=q, d=p)['camera_registration'] is None


def test_camera_anchor_alone_leaves_pool_and_site_confounded():
    q, d = .48, .3
    x = recover_given_anchors(q=q, d=d, known_registration=.6)
    assert x['per_occasion_availability'] == pytest.approx(.5)
    assert x['site_occupancy'] is None and x['regional_pool'] is None


def test_pool_anchor_alone_leaves_availability_and_registration_confounded():
    x = recover_given_anchors(q=.48, d=.3, known_pool=.6)
    assert x['site_occupancy'] == pytest.approx(.8)
    assert x['per_occasion_availability'] is None


def test_both_independent_exact_anchors_recover_all_four():
    x = recover_given_anchors(q=.48, d=.3, known_pool=.6, known_registration=.6)
    assert x['regional_pool'] == pytest.approx(.6)
    assert x['site_occupancy'] == pytest.approx(.8)
    assert x['per_occasion_availability'] == pytest.approx(.5)
    assert x['camera_registration'] == pytest.approx(.6)


@pytest.mark.parametrize('bad', [0, 1, -1, float('nan'), float('inf'), None, '0.5', True])
def test_invalid_probability_refused(bad):
    with pytest.raises(ValueError):
        Gates(bad, .8, .5, .6)


@pytest.mark.parametrize('bad_history', [[], [2], [0, 1.0], [True], [None], ['1']])
def test_ambiguous_histories_refused(bad_history):
    with pytest.raises(ValueError):
        history_probability(Gates(.6, .8, .5, .6), bad_history)


@pytest.mark.parametrize('bad_n', [0, -1, 16, 1.0, True])
def test_invalid_occasions_refused(bad_n):
    with pytest.raises(ValueError):
        history_distribution(Gates(.6, .8, .5, .6), bad_n)


@pytest.mark.parametrize('args', [dict(p_11=0, p_10=.1), dict(p_11=.1, p_10=0),
                                   dict(p_11=float('nan'), p_10=.3),
                                   dict(p_11=.99, p_10=.1),
                                   dict(p_11=.02, p_10=.6)])
def test_nonidentifiable_or_invalid_two_visit_composites_refused(args):
    with pytest.raises(ValueError):
        two_visit_composites(**args)


@pytest.mark.parametrize('args', [dict(q=.48,d=.3,known_pool=.4),
                                   dict(q=.48,d=.3,known_registration=.2),
                                   dict(q=0,d=.3),dict(q=.48,d=1)])
def test_incompatible_anchors_refused(args):
    with pytest.raises(ValueError):
        recover_given_anchors(**args)


def test_evidence_ladder_requires_independent_channel_for_each_split():
    d=identify_ladder()
    assert 'a' in d['closed_repeated_visits_no_anchors']['not_identified']
    assert 'psi' in d['closed_repeats_plus_independent_registration_reference']['not_identified']
    assert not d['closed_repeats_plus_pool_and_registration_anchors']['not_identified']


def test_certificate_passes_without_promoting_empirical_evidence():
    c=certificate()
    assert all(c['decision'][k] for k in (
        'observational_equivalence_pass','two_visit_composites_pass',
        'idealized_two_anchor_recovery_pass'
    ))
    assert c['data_boundary']['wildlife_rows_opened'] is False
    assert c['data_boundary']['new_simulated_validation_generation'] is False
    assert c['decision']['eSDM_superiority_claim_authorized'] is False
    assert c['decision']['E5_G4_qualified_by_this_proof'] is False
