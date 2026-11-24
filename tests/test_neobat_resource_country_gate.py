"""Synthetic-only country source-code join and link embargo tests."""
import unittest
from scripts import neobat_resource_country_gate as gate
from scripts import neobat_spatial_cell_pilot as scope

def toy_grid():
    taxa=[]
    for group,names in (("bat",scope.BATS),("plant",scope.PLANTS)):
        for name in names:
            taxa.append({
                "group":group,"name":name,
                "country_results":[{"country":"BR","status":"SAMPLED_LOWER_BOUND",
                                    "cell25_lower_bound":15}]
            })
    return {"status":"SAMPLED_CELL_LOWER_BOUND_COMPLETE",
            "target_species_count":14,"taxa":taxa}

def toy_sites():
    return [
        {"SiteCode":"SBR","Country":"Brazil","RefCode":"A"},
        {"SiteCode":"SMX","Country":"Mexico","RefCode":"A"},
        {"SiteCode":"SCR","Country":"Costa Rica","RefCode":"C"},
        {"SiteCode":"SPE","Country":"Peru","RefCode":"D"},
        {"SiteCode":"SCO","Country":"Colombia","RefCode":"E"},
    ]

def toy_records():
    def rec(site,ref,plant):
        return {"SiteCode":site,"RefCode":ref,
                "CurrentBatSpecies":"Carollia perspicillata",
                "CurrentPlantSpecies":plant,
                "Interaction":"Frugivory","TrophicGuild":"Frugivore"}
    return [
        rec("SMX","A","Ficus yoponensis"), # same reference in withheld BR; must be dropped
        rec("SCR","C","Piper aduncum"),
        rec("SPE","D","Ficus citrifolia"),
        rec("SCO","E","Cecropia obtusifolia"),
    ]

class TestCountryResourceGate(unittest.TestCase):
    def test_country_code_join_and_all_site_ref_embargo(self):
        r=gate.calculate(toy_grid(),toy_records(),toy_sites())
        x=next(z for z in r["country_result"] if z["bat"]=="Carollia perspicillata")
        self.assertTrue(x["country_had_original_neobat_sites"])
        self.assertEqual(x["country"],"BR")
        self.assertNotIn("Ficus yoponensis",x["partner_names"])
        self.assertEqual(x["positive_country_plant_sample_lower_bound"],3)
        self.assertEqual(x["training_references_for_eligible_plants"],3)
        self.assertTrue(x["eligible_resource_input"])
        self.assertIsNone(r["M3_vs_M1_prediction_difference"])

    def test_fewer_than_three_is_indeterminate_not_negative(self):
        v=toy_records()[:-1]
        r=gate.calculate(toy_grid(),v,toy_sites())
        x=next(z for z in r["country_result"] if z["bat"]=="Carollia perspicillata")
        self.assertFalse(x["eligible_resource_input"])
        self.assertEqual(x["status"],"INDETERMINATE_10_PLANT_PILOT")

    def test_missing_country_mapping_fails_closed(self):
        sites=toy_sites()+[{"SiteCode":"SXX","RefCode":"X","Country":"Atlantis"}]
        with self.assertRaisesRegex(ValueError,"UNMAPPED_NEOBAT_SITE_COUNTRY_STOP"):
            gate.calculate(toy_grid(),toy_records(),sites)

    def test_not_completed_spatial_pilot_cannot_pass(self):
        g=toy_grid()
        g["status"]="PARTIAL_SAMPLE_TRANSPORT_STOP"
        with self.assertRaisesRegex(ValueError,"MISSING_COMPLETE_BOUNDED_SAMPLE_STOP"):
            gate.calculate(g,toy_records(),toy_sites())

    def test_no_false_spatial_overlap_claim(self):
        r=gate.calculate(toy_grid(),toy_records(),toy_sites())
        self.assertTrue(r["country_link_only_not_25km_cell_cooccurrence"])
        self.assertTrue(r["sampled_source_used_for_discovery_not_sealed_prediction"])
        self.assertIsNone(r["full_GBIF_download_DOI"])

if __name__=="__main__":
    unittest.main()
