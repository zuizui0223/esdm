"""Source freeze, exact name mapping and temporal null controls for CC1 pilot."""
import math
import pytest

from scripts.neobat_cc1_seed_portfolio import (
    BATS, SEED_BLOB_SHA, LINK_BLOB_SHA, RNG_SEED, read_cc1, portfolio, xorshift32,
)


def test_author_original_candidate_scope_is_26():
    assert len(BATS) == len(set(BATS)) == 26
    assert SEED_BLOB_SHA == "dc95badb04365449e9ad5a13e8a37c5a9fc552e9"
    assert LINK_BLOB_SHA == "71f179a152a262d7a98d7bb4e633cf136bc39f98"


def test_exact_binomial_and_measured_zeros_not_missing():
    csv_bytes = (
        b'"",Group.1,ficus_insipida,ficus_sp.,piper_arboreum,Day_Length,Day_Year,Day_Year_Y\n'
        b'1,2002-01-01,0,100,3,0,1,0\n'
        b'2,2002-01-15,4,0,0,0,15,0\n'
    )
    x = read_cc1(csv_bytes, {"ficus insipida", "piper arboreum"})
    assert x["matched"] == ["ficus insipida", "piper arboreum"]
    assert x["species_columns"] == 3
    assert x["missing_matched_cells"] == 0
    assert x["zero_matched_cells"] == 2
    assert x["positive_matched_cells"] == 2


def test_duplicate_date_is_refused():
    raw = (
        b'"",Group.1,ficus_insipida,Day_Length,Day_Year,Day_Year_Y\n'
        b'1,2002-01-01,0,0,0,0\n'
        b'2,2002-01-01,1,0,0,0\n'
    )
    with pytest.raises(ValueError, match="DUPLICATE_SAMPLE_DATE"):
        read_cc1(raw, {"ficus insipida"})


def test_unknown_count_is_missing_not_zero():
    raw = (
        b'"",Group.1,ficus_insipida,Day_Length,Day_Year,Day_Year_Y\n'
        b'1,2002-01-01,NA,0,0,0\n'
        b'2,2002-01-15,0,0,0,0\n'
    )
    x = read_cc1(raw, {"ficus insipida"})
    assert x["missing_matched_cells"] == 1
    assert x["zero_matched_cells"] == 1


def _sample(n=72):
    rows = {}
    for t in range(n):
        series = {}
        for k, sp in enumerate(("a a", "b b", "c c")):
            series[sp] = float(1 + ((t + k * 7) % 11))
        rows[f"{t:03d}"] = series
    return {"rows": rows}


def test_replayable_circular_shift_portfolio_without_p_values():
    x = portfolio("Candidate", {"a a", "b b", "c c"}, _sample())
    y = portfolio("Candidate", {"a a", "b b", "c c"}, _sample())
    assert x == y
    assert x["eligible"]
    assert x["shared_dates"] == 72
    assert math.isfinite(x["CV_ratio"])
    assert x["status"].startswith("MORE_")
    assert "p_value" not in x


def test_no_bat_diet_overlap_is_ineligible():
    x = portfolio("Candidate", set(), _sample())
    assert x["shared_dates"] == 0
    assert x["eligible"] is False
    assert x["CV_ratio"] is None


def test_missing_value_reduces_shared_dates_without_zero_imputation():
    sample = _sample(60)
    sample["rows"]["000"]["a a"] = None
    x = portfolio("Candidate", {"a a", "b b", "c c"}, sample)
    assert x["shared_dates"] == 59
    assert x["eligible"] is False


def test_xorshift32_deterministic_seed():
    assert xorshift32(RNG_SEED) == xorshift32(RNG_SEED)
    assert xorshift32(RNG_SEED) != RNG_SEED
