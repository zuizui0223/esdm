"""BCI Dryad original-seed annual portfolio calculation; no synthetic ecology claim."""
import csv
import hashlib
import io
import json
import math

import pytest

from scripts.neobat_bci_fruit_portfolio import (
    DOI, ENTRY, NEOBAT_SHA256, PRIMARY_BATS, evaluate_bat, dryad_link,
    fetch_dryad_csv, cv,
)


def test_dryad_nested_source_links_allow_string_file_identifiers():
    meta = {"_links": {"stash:download": {"href": "/api/v2/files/not-an-int/download"}}}
    assert dryad_link(meta, "stash:download") == (
        "https://datadryad.org/api/v2/files/not-an-int/download")
    with pytest.raises(ValueError, match="DRYAD_LINK_OUTSIDE_OFFICIAL_API"):
        dryad_link({"_links": {"stash:download": {"href": "https://example.org/x"}}},
                   "stash:download")


def test_dryad_source_download_follows_author_file_path_and_sha256():
    raw = b"year,sp4,genus,species,abscised_seeds,viable_seeds,total_seeds,sum_parts\n"
    sha = hashlib.sha256(raw).hexdigest()
    ds = {"identifier": DOI,
          "_links": {"stash:version": {"href": "/api/v2/versions/111"}}}
    version = {"_links": {"stash:files": {"href": "/api/v2/versions/111/files"}}}
    file = {"path": "fruit_drop.csv", "size": len(raw), "digestType": "sha-256",
            "digest": sha, "_links": {"stash:download": {"href": "/api/v2/files/str-5/download"}}}
    files = {"total": 1, "_embedded": {"stash:files": [file]}}
    data = {ENTRY: json.dumps(ds).encode(),
            "https://datadryad.org/api/v2/versions/111": json.dumps(version).encode(),
            "https://datadryad.org/api/v2/versions/111/files": json.dumps(files).encode(),
            "https://datadryad.org/api/v2/files/str-5/download": raw}
    content, prov = fetch_dryad_csv(fetch=lambda u, n: data[u])
    assert content == raw
    assert prov["file_sha256"] == sha
    assert prov["file_size_bytes"] == len(raw)


def test_dryad_bad_digest_is_refused():
    raw = b"csv"
    ds = {"identifier": DOI, "_links": {"stash:version": {"href": "/api/v2/versions/1"}}}
    version = {"_links": {"stash:files": {"href": "/api/v2/versions/1/files"}}}
    f = {"path": "fruit_drop.csv", "size": 3, "digest": "0" * 64,
         "digestType": "sha-256",
         "_links": {"stash:download": {"href": "/api/v2/files/4/download"}}}
    file_list = {"total": 1, "_embedded": {"stash:files": [f]}}
    data = {ENTRY: json.dumps(ds).encode(),
            "https://datadryad.org/api/v2/versions/1": json.dumps(version).encode(),
            "https://datadryad.org/api/v2/versions/1/files": json.dumps(file_list).encode(),
            "https://datadryad.org/api/v2/files/4/download": raw}
    with pytest.raises(ValueError, match="DRYAD_PUBLISHER_DIGEST_MISMATCH"):
        fetch_dryad_csv(fetch=lambda u, n: data[u])


def _sample_series(n=12, identical=False):
    d = {}
    for j, sp in enumerate(("A a", "B b", "C c")):
        for y in range(2000, 2000 + n):
            viable = 2 + ((y - 2000) % 4) if identical else 2 + ((y - 2000 + j * 2) % 4)
            d[(sp, y)] = (0., float(viable), float(viable))
    return d


def test_portfolio_evaluable_does_not_generate_p_value():
    result = evaluate_bat("Test bat", {"A a", "B b", "C c"}, _sample_series())
    assert result["eligible_for_portfolio"] is True
    assert result["joint_years"] == 12
    assert result["observed_portfolio_CV"] is not None
    assert result["observed_over_null_CV"] is not None
    assert "p_value" not in result


def test_missing_calendar_years_never_imputed_as_zeros():
    d = _sample_series()
    del d[("C c", 2001)]
    del d[("C c", 2002)]
    del d[("C c", 2003)]
    r = evaluate_bat("Bat", {"A a", "B b", "C c"}, d)
    assert r["joint_years"] == 9
    assert r["eligible_for_portfolio"] is False
    assert r["observed_over_null_CV"] is None


def test_no_matched_plants_is_ineligible():
    out = evaluate_bat("Bat", set(), _sample_series())
    assert out["joint_years"] == 0
    assert out["eligible_for_portfolio"] is False
    assert out["plant_names"] == []


def test_original_bat_universe_kept():
    assert len(PRIMARY_BATS) == 26
    assert len(set(PRIMARY_BATS)) == 26
    assert len(NEOBAT_SHA256) == 64


def test_constant_series_cv_zero():
    assert cv([1., 1., 1.]) == 0.
    assert cv([0., 0., 0.]) is None
