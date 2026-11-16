"""Receipt-only C2 guard: no original sequence or network access."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
RESULT=HERE/'docs'/'replication'/'NEON_C2_FROZEN_RESULT.json'
FROZEN_SHA256='364c5eef71a5db979502d5de8a5d6ad6aebad066cbb5ccffa8433bc950b436fb'


def test_exact_one_shot_frozen_stop_bytes():
    raw=RESULT.read_bytes()
    assert len(raw)==305
    assert hashlib.sha256(raw).hexdigest()==FROZEN_SHA256


def test_no_ecological_result_extracted_from_taxonomy_stop():
    r=json.loads(RESULT.read_text())
    assert r['schema_version']==1
    assert r['status']=='RESPONSE_SCHEMA_STOP'
    assert r['reason']=='RESPONSE_SCHEMA_STOP: taxonomic class conflicts for a binomial'
    assert r['inference_limits']['no_positive_result_claimed'] is True
    assert r['inference_limits']['model_fit_performed'] is False
    assert 'regional_results' not in r
    assert 'pair_summaries' not in r
    assert 'source_species' not in r
