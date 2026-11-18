"""Guard public-metadata-only nonqualification: no fake independent passages."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'docs/replication/E5_G3_G4_NEW_SOURCE_DECISION_20261118.json'


def load():
    return json.loads(SOURCE.read_text(encoding='utf-8'))


def test_decision_is_not_empirical_or_new_e5_qualification():
    doc = load()
    assert doc['schema_version'] == 1
    assert doc['programme'] == 'E5_INDEPENDENT_ACTIVITY_DETECTION'
    assert doc['review_type'] == 'PUBLIC_SOURCE_DOCUMENTATION_ONLY'
    assert doc['decision'] == 'NO_NEW_QUALIFIED_INDEPENDENT_E5_SOURCE'
    assert (doc['prior_standard_e5_registry_count'], doc['prior_standard_e5_qualified_count']) == (17, 0)
    assert doc['new_e5_qualified_count'] == 0
    assert doc['registry_mutated'] is False
    assert doc['new_candidate_added_to_original_registry'] is False
    assert doc['wildlife_response_values_opened'] is False
    assert doc['reference_passage_values_opened'] is False
    assert doc['model_fit_performed'] is False


def test_external_sources_have_evidence_and_bounded_statuses():
    doc = load()
    assert {x['id'] for x in doc['resources']} == {
        'eow_zenodo_2026_june_v13',
        'smartwilds_camera_acoustic_drones_2026nov08',
        'qilian_mountains_zenodo_2025_events',
    }
    for item in doc['resources']:
        assert item['url'].startswith('https://')
        assert item['prequalification'] == 'NOT_QUALIFIED'
        assert item['independent_known_missed_passages'] is False
        assert item['G4_independent_detection_identification'] != 'PASS'
        assert item['G3_crossed_geography_protocol'] != 'PASS'
        assert item['G2_deployment_event_effort'] != 'PASS'
        assert item['critical_reason']
        assert item['next_input_if_offered']
        assert len(item['released_contents']) >= 2


def test_no_false_absence_or_causal_claims():
    fire = load()['inference_firewall']
    assert fire['additional_e5_candidate_qualifications_claimed'] is False
    assert fire['observation_modalities_equated_to_known_passages'] is False
    assert fire['counts_are_dataset_inventory_not_independent_ecological_replicates'] is True
    assert fire['no_eSDM_superiority_claim'] is True
    assert fire['no_reanalysis_of_consumed_safari14_c1_c2_c3_e4_e5_e7'] is True
    assert fire['public_documentation_not_exhaustive_proof_of_no_private_data'] is True


def test_exact_observational_requirements():
    req = load()['field_evidence_required_for_reconsideration']
    assert len(req) == 6
    assert any('station' in x and 'device' in x for x in req)
    assert any('reference' in x and 'overlap' in x for x in req)
    assert any('misses' in x for x in req)
    assert any('six' in x for x in req)
    assert any('geography' in x for x in req)


def test_documented_source_inventory_counts_not_promoted():
    rs={x['id']:x for x in load()['resources']}
    s=rs['smartwilds_camera_acoustic_drones_2026nov08']
    assert s['published_camera_events'] == 19785
    assert s['published_camera_inventory_images'] == 235778
    assert s['G3_crossed_geography_protocol'].startswith('FAIL')
    assert s['G4_independent_detection_identification'].startswith('FAIL')
    q=rs['qilian_mountains_zenodo_2025_events']
    assert q['G4_independent_detection_identification'].startswith('FAIL')
    e=rs['eow_zenodo_2026_june_v13']
    assert e['G2_deployment_event_effort'].startswith('NOT_DEMONSTRATED')


@pytest.mark.parametrize('field', ['prior_standard_e5_registry_count','prior_standard_e5_qualified_count','new_e5_qualified_count'])
def test_all_count_fields_are_nonnegative_ints(field):
    v=load()[field]
    assert type(v) is int and v >= 0
