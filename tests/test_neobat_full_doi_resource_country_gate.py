"""Synthetic full-source resource input gate: no downloaded GBIF biological records."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from scripts import neobat_full_doi_resource_country_gate as g

BATS=[f"Bat{i} species" for i in range(26)]
PLANTS=[f"Plant{i} species" for i in range(255)]

def full_source():
    bat={
      "DOI":g.EXPECTED["bat"]["doi"],
      "source_archive_sha256":g.EXPECTED["bat"]["archive_sha"],
      "full_archive_rows_checked":g.EXPECTED["bat"]["n_records"],
      "species_summary":[{"taxon":s} for s in BATS],
      "species_country_summary":[
        {"taxon":BATS[0],"country":"BR",
         "recorded_25km_cells":10,"precision_le12500m_25km_cells":8},
        {"taxon":BATS[0],"country":"CR",
         "recorded_25km_cells":32,"precision_le12500m_25km_cells":25}
      ]
    }
    plant={
      "DOI":g.EXPECTED["plant"]["doi"],
      "source_archive_sha256":g.EXPECTED["plant"]["archive_sha"],
      "full_archive_rows_checked":g.EXPECTED["plant"]["n_records"],
      "species_summary":[{"taxon":s,"country_cells":5 if i<3 else 0}
                         for i,s in enumerate(PLANTS)],
      "species_country_summary":[
        {"taxon":p,"country":"BR",
         "recorded_25km_cells":5,"precision_le12500m_25km_cells":5}
        for p in PLANTS[:3]]
    }
    return {"status":"BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED",
            "groups":{"bat":bat,"plant":plant}}

def sites():
    return [
        {"Country":"BR","SiteCode":"A","RefCode":"H"},
        {"Country":"CR","SiteCode":"B","RefCode":"R1"},
        {"Country":"MX","SiteCode":"C","RefCode":"R2"},
        {"Country":"CO","SiteCode":"D","RefCode":"R3"}
    ]

def records():
    return [{
        "SiteCode":site,"RefCode":ref,
        "CurrentBatSpecies":BATS[0],"CurrentPlantSpecies":plant,
        "Interaction":"Frugivory","TrophicGuild":"Frugivore"
    } for site,ref,plant in zip(["B","C","D"],["R1","R2","R3"],PLANTS[:3])]

def mocked_audit(*a,**k):
    return {"species":[{"bat":b,"primary_candidate":True} for b in BATS]}

class TestFullDOIResourceGate(unittest.TestCase):
    def test_full_original_input_availability_not_effect(self):
        with patch.object(g.neobat,"audit",side_effect=mocked_audit):
            result=g.build(full_source(),records(),sites(),[{"RefCode":"R1"}])
        self.assertEqual(result["status"],"FULL_DOI_PRECISION_CONDITIONED_INPUT_FEASIBILITY_ONLY")
        self.assertEqual(result["modes"]["strict"]["bat_country_pairs_with_source_partner_input"],1)
        self.assertEqual(result["modes"]["strict"]["bats_with_2plus_countries_input_possible"],0)
        br=result["modes"]["strict"]["all_26_bats"][0]["country_records"]
        self.assertEqual(len(br),1)
        self.assertEqual(br[0]["country"],"BR")
        self.assertEqual(br[0]["plants_with_5plus_local_recorded_cells"],3)
        self.assertTrue(br[0]["input_possible"])
        self.assertIsNone(result["M3_minus_M1"])
        self.assertFalse(result["species_country_cell_cooccurrence_tested"])

    def test_ref_with_heldout_country_site_excluded_even_if_link_is_elsewhere(self):
        s=sites()+[{"Country":"BR","SiteCode":"E","RefCode":"R1"}]
        with patch.object(g.neobat,"audit",side_effect=mocked_audit):
            result=g.build(full_source(),records(),s,[{"RefCode":"R1"}])
        br=result["modes"]["strict"]["all_26_bats"][0]["country_records"][0]
        self.assertFalse(br["input_possible"])
        self.assertEqual(br["plants_with_5plus_local_recorded_cells"],2)

    def test_wrong_source_identity_stops(self):
        q=full_source()
        q["groups"]["plant"]["source_archive_sha256"]="wrong"
        with self.assertRaisesRegex(ValueError,"SOURCE_QC_DOI_SHA_ROW_MISMATCH_plant"):
            g.source_validate(q)

    def test_recorded_species_universe_never_pruned_by_outcome(self):
        with patch.object(g.neobat,"audit",side_effect=mocked_audit):
            result=g.build(full_source(),records(),sites(),[{"RefCode":"R1"}])
        self.assertEqual(result["initial_bats"],26)
        self.assertEqual(result["initial_plants"],255)
        self.assertEqual(len(result["modes"]["strict"]["all_26_bats"]),26)
        self.assertEqual(len(result["plant_species_with_no_indexed_cells"]),252)

if __name__=="__main__":
    unittest.main()
