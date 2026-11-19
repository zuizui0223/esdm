"""Synthetic-only checks for prefit DOI country × resource gates; no real heldout outcomes."""
from __future__ import annotations
import unittest
from copy import deepcopy

from scripts import neobat_full_source_country_resource_gate as gate

BAT="Carollia perspicillata"
PLANTS=("Ficus insipida","Piper aduncum","Cecropia obtusifolia","Solanum rugosum")

def qc():
    def item(taxon,cc,all_n,strict_n):
        return {"taxon":taxon,"country":cc,"recorded_25km_cells":all_n,
                "precision_le12500m_25km_cells":strict_n}
    bat=[item(BAT,"BR",11,8),item(BAT,"CO",36,25)]
    plants=[]
    for p in PLANTS:
        plants.extend([item(p,"BR",12,6),item(p,"CO",32,25)])
    return {"status":"BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED","groups":{
        "bat":{"species_country_summary":bat},
        "plant":{"species_country_summary":plants}}}

def sources():
    sites=[{"SiteCode":"S1","Country":"Mexico","RefCode":"R1"},
           {"SiteCode":"S2","Country":"Costa Rica","RefCode":"R2"},
           {"SiteCode":"S3","Country":"Brazil","RefCode":"R0"},
           {"SiteCode":"S4","Country":"Colombia","RefCode":"R4"},
           {"SiteCode":"S5","Country":"Mexico","RefCode":"R0"}]
    def record(site,ref,p):
        return {"Interaction":"Frugivory","TrophicGuild":"Frugivore",
                "CurrentBatSpecies":BAT,"CurrentPlantSpecies":p,
                "SiteCode":site,"RefCode":ref}
    rec=[record("S1","R1",PLANTS[0]),
         record("S2","R2",PLANTS[1]),
         record("S2","R2",PLANTS[2]),
         record("S5","R0",PLANTS[3]), # same RefCode as BR; remove on BR holdout
         record("S4","R4",PLANTS[0])]
    return rec,sites

class TestFullCountryResource(unittest.TestCase):
    def test_broad_strict_gate_and_embargo(self):
        rec,site=sources()
        got=gate.calculate(qc(),rec,site,[BAT],list(PLANTS),enforce_roster=False)
        self.assertEqual(got["total_bat_country_pairs"],29)
        x=next(x for x in got["folds"] if x["country"]=="BR")
        self.assertTrue(x["known_precision"]["input_candidate"])
        self.assertEqual(x["known_precision"]["linked_plant_species_meeting_5_20"],3)
        # R1, R2, and R4 remain; only R0 is embargoed by the heldout BR source site.
        self.assertEqual(x["known_precision"]["independent_outcountry_NeoBat_refs"],3)
        self.assertEqual(x["known_precision"]["plant_pool_species_meeting_5_20"],4)
        self.assertEqual(x["known_precision"]["nonpartner_pool_species_meeting_5_20"],1)
        self.assertNotIn(PLANTS[3],x["known_precision"]["eligible_partner_names"])
        self.assertEqual(got["known_precision_source_candidate_pairs"],1)
        self.assertEqual(got["ecological_M3_minus_M1"],None)
        self.assertTrue(got["country_cooccurrence_not_confirmed"])

    def test_report_keeps_every_country_and_noneligible_stratum(self):
        rec,site=sources()
        got=gate.calculate(qc(),rec,site,[BAT],list(PLANTS),enforce_roster=False)
        self.assertEqual(len(got["folds"]),len(gate.COUNTRIES))
        self.assertEqual(got["bats_with_two_or_more_known_precision_candidate_countries"],0)
        x=next(x for x in got["folds"] if x["country"]=="MX")
        self.assertEqual(x["known_precision"]["status"],"BAT_CELLS_BELOW_GATE")
        s=gate.compact(got)
        self.assertEqual(s["denominators"]["bat_country"],29)
        self.assertTrue(s["cooccurrence_and_M3_effect_not_evaluated"])

    def test_missing_plant_precision_removes_strict_input_only(self):
        rec,site=sources();a=qc()
        for r in a["groups"]["plant"]["species_country_summary"]:
            if r["taxon"]==PLANTS[2]:
                r["precision_le12500m_25km_cells"]=0
        got=gate.calculate(a,rec,site,[BAT],list(PLANTS),enforce_roster=False)
        x=next(x for x in got["folds"] if x["country"]=="BR")
        self.assertFalse(x["known_precision"]["input_candidate"])
        self.assertEqual(x["known_precision"]["status"],"PARTNER_PLANT_CELLS_INSUFFICIENT")
        self.assertTrue(x["indexed"]["input_candidate"])

    def test_duplicate_species_country_and_invalid_precision_fail(self):
        group=qc()["groups"]["bat"]
        group["species_country_summary"].append(deepcopy(group["species_country_summary"][0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_TAXON_COUNTRY"):
            gate.index(group)
        a=qc()["groups"]["bat"]
        a["species_country_summary"][0]["precision_le12500m_25km_cells"]=20
        with self.assertRaisesRegex(ValueError,"INVALID_CELL_COUNTS"):
            gate.index(a)

    def test_source_ref_conflict_and_unknown_country_fail(self):
        rec,site=sources()
        rec[0]["RefCode"]="wrong"
        with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_EVENT_LINK"):
            gate.calculate(qc(),rec,site,[BAT],list(PLANTS),enforce_roster=False)
        rec,site=sources()
        site[0]["Country"]="Atlantis"
        with self.assertRaisesRegex(ValueError,"UNKNOWN_NEOBAT_SITE_COUNTRY"):
            gate.calculate(qc(),rec,site,[BAT],list(PLANTS),enforce_roster=False)

    def test_source_group_must_be_completed(self):
        rec,site=sources()
        wrong=qc();wrong["status"]="FULL_SOURCE_QC_STOP"
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_DOI_QC"):
            gate.calculate(wrong,rec,site,[BAT],list(PLANTS),enforce_roster=False)

if __name__=="__main__":
    unittest.main()
