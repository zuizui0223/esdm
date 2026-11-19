"""Synthetic-only compact source-QC audit. No GBIF API/network requests."""
from __future__ import annotations
import copy
import unittest
from unittest.mock import patch

from scripts import neobat_summarize_full_source_qc as qc

def group(name,doi,archive,n):
    s={
        "taxon":name,"indexed_records_matching_species":n,
        "countries_with_records":2,
        "country_cells":11,
        "known_precision_country_cells":9,
        "countries_with_ge5_recorded_cells":2,
        "countries_with_ge5_known_precision_cells":1
    }
    c1={"taxon":name,"country":"BR","recorded_25km_cells":6,
        "precision_le12500m_25km_cells":5}
    c2={"taxon":name,"country":"MX","recorded_25km_cells":5,
        "precision_le12500m_25km_cells":4}
    return {"status":"FULL_GBIF_RECORD_SOURCE_QC_ONLY",
            "DOI":doi,"source_archive_sha256":archive,
            "full_archive_rows_checked":n,"valid_source_rows":n,
            "quality_breakdown":{"rows":n,"valid_source_rows":n},
            "distinct_species_with_valid_cells":1,
            "species_summary":[s],
            "species_country_summary":[c1,c2]}

class TestCompactQCSummary(unittest.TestCase):
    def setUp(self):
        self.test_expected={
            "bat":{"doi":"10.15468/dl.bat1","archive_sha":"batsha","n_records":4,"n_species":1},
            "plant":{"doi":"10.15468/dl.plant1","archive_sha":"plantsha","n_records":6,"n_species":1}
        }
        self.data={
            "status":"BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED",
            "groups":{
                "bat":group("Bat spec","10.15468/dl.bat1","batsha",4),
                "plant":group("Plant spec","10.15468/dl.plant1","plantsha",6)
            }
        }

    def test_fixed_cohort_and_candidate_are_source_only(self):
        with patch.dict(qc.EXPECTED,self.test_expected,clear=True):
            result=qc.summarise(self.data)
        self.assertEqual(result["status"],"COMPLETE_SOURCE_QC_SUMMARY_NOT_MODEL")
        self.assertEqual(result["groups"]["bat"]["valid_country_year_coordinate_rows"],4)
        self.assertEqual(result["groups"]["plant"]["species_in_complete_name_cohort"],1)
        self.assertIsNone(result["ecological_M3_minus_M1"])
        self.assertFalse(result["independent_holdout_unopened"])

    def test_hash_and_doi_mismatch_are_stops(self):
        changed=copy.deepcopy(self.data)
        changed["groups"]["bat"]["source_archive_sha256"]="CHANGED"
        with patch.dict(qc.EXPECTED,self.test_expected,clear=True):
            with self.assertRaisesRegex(ValueError,"SOURCE_IDENTITY_MISMATCH_bat"):
                qc.summarise(changed)

    def test_country_cell_sums_cannot_be_inconsistent(self):
        changed=copy.deepcopy(self.data)
        changed["groups"]["plant"]["species_summary"][0]["country_cells"]=90
        with patch.dict(qc.EXPECTED,self.test_expected,clear=True):
            with self.assertRaisesRegex(ValueError,"SPECIES_CELL_SUM_INCONSISTENCY_plant"):
                qc.summarise(changed)

    def test_incomplete_full_source_does_not_promote(self):
        changed=copy.deepcopy(self.data)
        changed["status"]="PARTIAL_FULL_SOURCE_QC"
        with self.assertRaisesRegex(ValueError,"FULL_QC_NOT_COMPLETE"):
            qc.summarise(changed)

if __name__=="__main__":
    unittest.main()
