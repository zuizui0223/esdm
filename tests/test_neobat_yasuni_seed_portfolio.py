"""Yasuní long-format source, author binomial bridge and same-size controls."""
import csv
import hashlib
import io
import math

import pytest

import scripts.neobat_yasuni_seed_portfolio as y


def mock_source(monkeypatch, content):
    monkeypatch.setattr(y, "YAS_BLOB", y.git_blob_sha(content))
    monkeypatch.setattr(y, "YAS_BYTES", len(content))


def test_author_code_to_name_exact_match_and_no_fuzzy_synonym(monkeypatch):
    src = (
        b'"","CODIGO","Taxon.NombreActual"\n'
        b'"1","CECRFI","Cecropia ficifolia"\n'
        b'"2","VISCMA","Vismia cf. macrophylla"\n'
        b'"3","TURPOC","Turpinia occidentalis"\n')
    monkeypatch.setattr(y, "TAXON_BLOB", y.git_blob_sha(src))
    obs = y.link_names_to_author_codes(src, {
        "cecropia ficifolia", "vismia macrophylla", "turpinia occidentalis"})
    assert obs == {"CECRFI": "cecropia ficifolia",
                   "TURPOC": "turpinia occidentalis"}


def test_different_names_for_same_source_code_are_rejected(monkeypatch):
    s = ('CODIGO,Taxon.NombreActual\n'
         'X,Cecropia ficifolia\n'
         'X,Turpinia occidentalis\n').encode()
    monkeypatch.setattr(y, "TAXON_BLOB", y.git_blob_sha(s))
    with pytest.raises(ValueError, match="CONFLICTING_NAMES_FOR_ONE_CODE"):
        y.link_names_to_author_codes(s, {"cecropia ficifolia", "turpinia occidentalis"})


def test_numeric_time_order_zero_and_missing_remain_distinct(monkeypatch):
    src = (
        b'"",Day_Year_Y,variable,value\n'
        b'1,1.5,AAA,0\n'
        b'2,1.5,BBB,4\n'
        b'3,10.0,AAA,3\n'
        b'4,10.0,BBB,NA\n'
        b'5,2.5,AAA,1\n'
    )
    mock_source(monkeypatch, src)
    result = y.parse_yasuni(src, {"AAA": "cecropia ficifolia",
                                 "BBB": "spondias mombin"})
    assert list(result["rows"]) == [1.5, 2.5, 10.0]
    assert result["rows"][1.5] == {
        "cecropia ficifolia": 0, "spondias mombin": 4}
    assert result["rows"][2.5]["spondias mombin"] is None
    assert result["rows"][10.0]["spondias mombin"] is None
    assert result["matched_zero_values"] == 1
    assert result["matched_explicit_missing_values"] == 1
    assert result["matched_omitted_code_timepoints"] == 1
    assert result["matched_positive_values"] == 3


def test_duplicate_code_time_fails(monkeypatch):
    raw = (b'Day_Year_Y,variable,value\n'
           b'1.0,AAA,0\n'
           b'1.0,AAA,3\n')
    mock_source(monkeypatch, raw)
    with pytest.raises(ValueError, match="YASUNI_DUPLICATE_MATCHED_CODE_TIMEPOINT"):
        y.parse_yasuni(raw, {"AAA": "a a"})


def test_negative_counts_fail(monkeypatch):
    raw = b'Day_Year_Y,variable,value\n1.0,AAA,-1\n'
    mock_source(monkeypatch, raw)
    with pytest.raises(ValueError, match="YASUNI_INVALID_SEED_COUNT"):
        y.parse_yasuni(raw, {"AAA": "a a"})


def sample(n=75):
    values = {}
    for i in range(n):
        values[float(i + 1)] = {
            "a a": float(1 + i % 6),
            "b b": float(1 + (i + 2) % 6),
            "c c": float(1 + (i + 4) % 6),
            "d d": float(1 + (i * 3) % 7)}
    return {"rows": values}


def test_full_size_matched_enumeration_and_duplicate_sets():
    data = sample()
    p = y.portfolio("Bat", {"a a", "b b", "c c"}, data, n_perm=10)
    q = y.portfolio("Bat2", {"c c", "b b", "a a"}, data, n_perm=10)
    baseline = y.control_for_candidate_sets(
        ["a a", "b b", "c c", "d d"], [p, q], data)
    assert baseline["baseline_by_size"][0]["all_combinations"] == 4
    assert baseline["baseline_by_size"][0]["evaluable_combinations"] == 4
    assert baseline["distinct_evaluable_source_plant_sets"] == 1
    assert len(baseline["identical_source_plant_set_groups"]) == 1
    assert baseline["all_candidate_bats"][0]["same_size_CV_ratio"] > 0


def test_incomplete_baseline_does_not_promote_rank():
    src = sample()
    # Candidate set has positive signal; one 4th taxon has all zeros.
    for t in src["rows"]:
        src["rows"][t]["d d"] = 0
    p = y.portfolio("Bat", {"a a", "b b", "c c"}, src, n_perm=10)
    out = y.control_for_candidate_sets(
        ["a a", "b b", "c c", "d d"], [p], src)
    assert out["baseline_by_size"][0]["complete_baseline"] is False
    assert out["all_candidate_bats"][0]["same_size_CV_ratio"] is None
    assert out["all_candidate_bats"][0]["status"] == "INCOMPLETE_BASELINE_DO_NOT_INFER"


def test_original_latin1_author_annotations_not_replace_bytes(monkeypatch):
    # 0xA1 is a valid original Latin-1 byte but not UTF-8; preserve the blob.
    raw = (b'CODIGO,Taxon.NombreActual,Notes\n'
           b'CECRFI,Cecropia ficifolia,\xa1\n')
    monkeypatch.setattr(y, "TAXON_BLOB", y.git_blob_sha(raw))
    out = y.link_names_to_author_codes(raw, {"cecropia ficifolia"})
    assert out == {"CECRFI": "cecropia ficifolia"}
    assert y.decode_author_csv(raw).endswith("\xa1\n")
